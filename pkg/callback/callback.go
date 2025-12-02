package callback

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	log "github.com/sirupsen/logrus"
)

const (
	// Time allowed to write a message to the peer.
	writeWait = 10 * time.Second

	// Time allowed to read the next pong message from the peer.
	pongWait = 60 * time.Second

	// Send pings to peer with this period. Must be less than pongWait.
	pingPeriod = (pongWait * 9) / 10

	// Maximum message size allowed from peer.
	maxMessageSize = 512 * 1024 // 512KB

	// Default timeout for callback responses
	defaultCallbackTimeout = 30 * time.Second
)

// CallbackRequest represents a callback request from the guest VM to the client.
type CallbackRequest struct {
	ID        string          `json:"id"`
	Method    string          `json:"method"`
	Params    json.RawMessage `json:"params,omitempty"`
	Timestamp int64           `json:"timestamp"`
}

// CallbackResponse represents a response from the client to a callback request.
type CallbackResponse struct {
	ID     string          `json:"id"`
	Result json.RawMessage `json:"result,omitempty"`
	Error  *CallbackError  `json:"error,omitempty"`
}

// CallbackError represents an error in a callback response.
type CallbackError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// ClientSession represents an active WebSocket connection from a client.
type ClientSession struct {
	ID     string
	VMName string
	conn   *websocket.Conn
	send   chan []byte
	done   chan struct{}

	// pendingCallbacks tracks callbacks waiting for responses
	pendingLock      sync.RWMutex
	pendingCallbacks map[string]chan *CallbackResponse
}

// SessionManager manages all active client sessions.
type SessionManager struct {
	lock     sync.RWMutex
	sessions map[string]*ClientSession // keyed by vmName

	// OnSessionClose is called when a session closes (for VM cleanup)
	OnSessionClose func(vmName string)
}

// NewSessionManager creates a new SessionManager.
func NewSessionManager() *SessionManager {
	return &SessionManager{
		sessions: make(map[string]*ClientSession),
	}
}

// CreateSession creates a new client session for the given VM.
func (m *SessionManager) CreateSession(vmName string, conn *websocket.Conn) (*ClientSession, error) {
	m.lock.Lock()
	defer m.lock.Unlock()

	// Check if session already exists for this VM
	if existing, ok := m.sessions[vmName]; ok {
		// Close the existing session
		existing.Close()
	}

	session := &ClientSession{
		ID:               fmt.Sprintf("%s-%d", vmName, time.Now().UnixNano()),
		VMName:           vmName,
		conn:             conn,
		send:             make(chan []byte, 256),
		done:             make(chan struct{}),
		pendingCallbacks: make(map[string]chan *CallbackResponse),
	}

	m.sessions[vmName] = session

	// Start the read and write pumps
	go session.writePump()
	go session.readPump(m)

	log.WithFields(log.Fields{
		"sessionId": session.ID,
		"vmName":    vmName,
	}).Info("Client session created")

	return session, nil
}

// GetSession returns the session for the given VM name.
func (m *SessionManager) GetSession(vmName string) *ClientSession {
	m.lock.RLock()
	defer m.lock.RUnlock()
	return m.sessions[vmName]
}

// RemoveSession removes and closes the session for the given VM.
func (m *SessionManager) RemoveSession(vmName string) {
	m.lock.Lock()
	session := m.sessions[vmName]
	delete(m.sessions, vmName)
	m.lock.Unlock()

	if session != nil {
		session.Close()
	}
}

// handleSessionClose is called when a session closes.
func (m *SessionManager) handleSessionClose(vmName string) {
	m.lock.Lock()
	delete(m.sessions, vmName)
	m.lock.Unlock()

	log.WithField("vmName", vmName).Info("Client session closed")

	if m.OnSessionClose != nil {
		m.OnSessionClose(vmName)
	}
}

// Close closes the client session.
func (s *ClientSession) Close() {
	select {
	case <-s.done:
		// Already closed
		return
	default:
		close(s.done)
		s.conn.Close()
	}
}

// SendCallback sends a callback request to the client and waits for a response.
func (s *ClientSession) SendCallback(ctx context.Context, req *CallbackRequest) (*CallbackResponse, error) {
	// Create a channel to receive the response
	responseChan := make(chan *CallbackResponse, 1)

	// Register the pending callback
	s.pendingLock.Lock()
	s.pendingCallbacks[req.ID] = responseChan
	s.pendingLock.Unlock()

	// Clean up on exit
	defer func() {
		s.pendingLock.Lock()
		delete(s.pendingCallbacks, req.ID)
		s.pendingLock.Unlock()
	}()

	// Serialize the request
	data, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal callback request: %w", err)
	}

	// Send the request
	select {
	case s.send <- data:
	case <-s.done:
		return nil, fmt.Errorf("session closed")
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	// Wait for response
	select {
	case resp := <-responseChan:
		return resp, nil
	case <-s.done:
		return nil, fmt.Errorf("session closed while waiting for callback response")
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// readPump pumps messages from the WebSocket connection.
func (s *ClientSession) readPump(m *SessionManager) {
	defer func() {
		m.handleSessionClose(s.VMName)
		s.Close()
	}()

	s.conn.SetReadLimit(maxMessageSize)
	s.conn.SetReadDeadline(time.Now().Add(pongWait))
	s.conn.SetPongHandler(func(string) error {
		s.conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	for {
		_, message, err := s.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.WithFields(log.Fields{
					"sessionId": s.ID,
					"vmName":    s.VMName,
				}).WithError(err).Error("WebSocket read error")
			}
			return
		}

		// Parse the response
		var resp CallbackResponse
		if err := json.Unmarshal(message, &resp); err != nil {
			log.WithFields(log.Fields{
				"sessionId": s.ID,
				"vmName":    s.VMName,
			}).WithError(err).Error("Failed to parse callback response")
			continue
		}

		// Route to the pending callback
		s.pendingLock.RLock()
		responseChan, ok := s.pendingCallbacks[resp.ID]
		s.pendingLock.RUnlock()

		if ok {
			select {
			case responseChan <- &resp:
			default:
				// Channel full or closed, log and continue
				log.WithFields(log.Fields{
					"sessionId":  s.ID,
					"vmName":     s.VMName,
					"callbackId": resp.ID,
				}).Warn("Failed to deliver callback response")
			}
		} else {
			log.WithFields(log.Fields{
				"sessionId":  s.ID,
				"vmName":     s.VMName,
				"callbackId": resp.ID,
			}).Warn("Received response for unknown callback")
		}
	}
}

// writePump pumps messages from the send channel to the WebSocket connection.
func (s *ClientSession) writePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		s.conn.Close()
	}()

	for {
		select {
		case message, ok := <-s.send:
			s.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				// Channel closed
				s.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := s.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			s.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := s.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}

		case <-s.done:
			return
		}
	}
}

// RouteCallback routes a callback from a VM to the appropriate client session.
// This is called by the vsock server when it receives a CALLBACK command.
func (m *SessionManager) RouteCallback(ctx context.Context, vmName string, method string, params json.RawMessage) (json.RawMessage, error) {
	session := m.GetSession(vmName)
	if session == nil {
		return nil, fmt.Errorf("no active session for VM: %s", vmName)
	}

	// Create the callback request
	req := &CallbackRequest{
		ID:        fmt.Sprintf("%s-%d", vmName, time.Now().UnixNano()),
		Method:    method,
		Params:    params,
		Timestamp: time.Now().Unix(),
	}

	// Set timeout if not already set in context
	if _, ok := ctx.Deadline(); !ok {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, defaultCallbackTimeout)
		defer cancel()
	}

	// Send and wait for response
	resp, err := session.SendCallback(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("callback failed: %w", err)
	}

	if resp.Error != nil {
		return nil, fmt.Errorf("callback error [%d]: %s", resp.Error.Code, resp.Error.Message)
	}

	return resp.Result, nil
}

