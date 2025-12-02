package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	log "github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"

	"github.com/abshkbh/arrakis/out/gen/serverapi"
	"github.com/abshkbh/arrakis/pkg/callback"
	"github.com/abshkbh/arrakis/pkg/config"
	"github.com/abshkbh/arrakis/pkg/server"
)

const (
	API_VERSION = "v1"
)

// WebSocket upgrader with default options
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// Allow all origins for development; restrict in production
		return true
	},
}

// sendErrorResponse sends a standardized error response to the client.
func sendErrorResponse(w http.ResponseWriter, statusCode int, message string) {
	resp := serverapi.ErrorResponse{
		Error: &serverapi.ErrorResponseError{
			Message: &message,
		},
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(resp)
}

type restServer struct {
	vmServer       *server.Server
	sessionManager *callback.SessionManager
}

// Health check endpoint for load balancer monitoring
func (s *restServer) healthCheck(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleWebSocket handles WebSocket connections for RPC callbacks.
func (s *restServer) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "handleWebSocket")
	vars := mux.Vars(r)
	vmName := vars["name"]

	if vmName == "" {
		logger.Error("Empty vm name in WebSocket connection")
		sendErrorResponse(w, http.StatusBadRequest, "VM name is required")
		return
	}

	// Upgrade HTTP connection to WebSocket
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Failed to upgrade to WebSocket")
		return
	}

	// Create session for this VM
	session, err := s.sessionManager.CreateSession(vmName, conn)
	if err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Failed to create session")
		conn.Close()
		return
	}

	logger.WithFields(log.Fields{
		"vmName":    vmName,
		"sessionId": session.ID,
	}).Info("WebSocket connection established")
}

// Implement handler functions
func (s *restServer) startVM(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "startVM")
	startTime := time.Now()

	var req serverapi.StartVMRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithError(err).Error("Invalid request body")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid request format: %v", err))
		return
	}

	if req.GetVmName() == "" {
		logger.Error("Empty vm name")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			"Empty vm name")
		return
	}

	vmName := req.GetVmName()
	resp, err := s.vmServer.StartVM(r.Context(), &req)
	if err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Failed to start VM")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to start VM: %v", err))
		return
	}

	elapsedTime := time.Since(startTime)
	logger.WithFields(log.Fields{
		"vmName":      vmName,
		"startupTime": elapsedTime.String(),
	}).Info("VM started successfully")
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) destroyVM(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "destroyVM")
	vars := mux.Vars(r)
	vmName := vars["name"]

	// Create request object with the VM name
	req := serverapi.VMRequest{
		VmName: &vmName,
	}

	resp, err := s.vmServer.DestroyVM(r.Context(), &req)
	if err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Failed to destroy VM")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to destroy VM: %v", err))
		return
	}

	// Also remove any active session for this VM
	s.sessionManager.RemoveSession(vmName)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) destroyAllVMs(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "destroyAllVMs")
	resp, err := s.vmServer.DestroyAllVMs(r.Context())
	if err != nil {
		logger.WithError(err).Error("Failed to destroy all VMs")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to destroy all VMs: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) listAllVMs(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "listAllVMs")
	resp, err := s.vmServer.ListAllVMs(r.Context())
	if err != nil {
		logger.WithError(err).Error("Failed to list all VMs")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to list all VMs: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) listVM(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "listVM")
	vars := mux.Vars(r)
	vmName := vars["name"]
	resp, err := s.vmServer.ListVM(r.Context(), vmName)
	if err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Failed to list VM")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to list VM: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) snapshotVM(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "snapshotVM")
	vars := mux.Vars(r)
	vmName := vars["name"]

	var req struct {
		SnapshotId string `json:"snapshotId,omitempty"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Invalid request body")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid request format: %v", err))
		return
	}

	resp, err := s.vmServer.SnapshotVM(r.Context(), vmName, req.SnapshotId)
	if err != nil {
		logger.WithFields(log.Fields{
			"vmName":     vmName,
			"snapshotId": req.SnapshotId,
		}).WithError(err).Error("Failed to create snapshot")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to create snapshot: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) updateVMState(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "updateVMState")
	vars := mux.Vars(r)
	vmName := vars["name"]

	var req serverapi.V1VmsNamePatchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Invalid request body")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid request format: %v", err))
		return
	}

	status := req.GetStatus()
	if status != "stopped" && status != "paused" && status != "resume" {
		logger.WithFields(log.Fields{
			"vmName": vmName,
			"status": status,
		}).Error("Invalid status value")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid status value: %s", status))
		return
	}

	vmReq := serverapi.VMRequest{
		VmName: &vmName,
	}

	var resp *serverapi.VMResponse
	var err error
	if status == "stopped" {
		resp, err = s.vmServer.StopVM(r.Context(), &vmReq)
	} else if status == "paused" {
		resp, err = s.vmServer.PauseVM(r.Context(), &vmReq)
	} else { // status == "resume"
		resp, err = s.vmServer.ResumeVM(r.Context(), &vmReq)
	}

	if err != nil {
		logger.WithFields(log.Fields{
			"vmName": vmName,
			"status": status,
		}).WithError(err).Error("Failed to update VM state")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to change VM state to '%s': %v", status, err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) vmCommand(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "vmCommand")
	vars := mux.Vars(r)
	vmName := vars["name"]

	var req serverapi.VmCommandRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Invalid request body")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid request format: %v", err))
		return
	}

	if req.GetCmd() == "" {
		logger.WithField("vmName", vmName).Error("Command cannot be empty")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			"Command cannot be empty")
		return
	}

	cmd := req.GetCmd()
	// Default to blocking if not specified
	blocking := true
	if req.Blocking != nil {
		blocking = *req.Blocking
	}

	resp, err := s.vmServer.VMCommand(r.Context(), vmName, cmd, blocking)
	if err != nil {
		logger.WithFields(log.Fields{
			"vmName":   vmName,
			"cmd":      cmd,
			"blocking": blocking,
			"success":  false,
		}).Error("Failed to execute command")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to execute command: %v", err))
		return
	}

	logger.WithFields(log.Fields{
		"vmName":   vmName,
		"cmd":      cmd,
		"blocking": blocking,
		"success":  true,
	}).Info("Successfully executed command")
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) vmFileUpload(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "vmFileUpload")
	vars := mux.Vars(r)
	vmName := vars["name"]

	var req serverapi.VmFileUploadRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithField("vmName", vmName).WithError(err).Error("Invalid request body")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			fmt.Sprintf("Invalid request format: %v", err))
		return
	}

	if len(req.GetFiles()) == 0 {
		logger.WithField("vmName", vmName).Error("No files provided")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			"No files provided for upload")
		return
	}

	files := req.GetFiles()
	resp, err := s.vmServer.VMFileUpload(r.Context(), vmName, files)
	if err != nil {
		logger.WithFields(log.Fields{
			"vmName":    vmName,
			"fileCount": len(files),
		}).WithError(err).Error("Failed to upload files")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to upload files: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *restServer) vmFileDownload(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "vmFileDownload")
	vars := mux.Vars(r)
	vmName := vars["name"]

	paths := r.URL.Query().Get("paths")
	if paths == "" {
		logger.WithField("vmName", vmName).Error("Missing 'paths' query parameter")
		sendErrorResponse(
			w,
			http.StatusBadRequest,
			"Missing 'paths' query parameter")
		return
	}

	resp, err := s.vmServer.VMFileDownload(r.Context(), vmName, paths)
	if err != nil {
		logger.WithFields(log.Fields{
			"vmName": vmName,
			"paths":  paths,
		}).WithError(err).Error("Failed to download files")
		sendErrorResponse(
			w,
			http.StatusInternalServerError,
			fmt.Sprintf("Failed to download files: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// InternalCallbackRequest represents a callback request from a VM to the host.
type InternalCallbackRequest struct {
	VMName string          `json:"vmName"`
	Method string          `json:"method"`
	Params json.RawMessage `json:"params,omitempty"`
}

// InternalCallbackResponse represents the response to a callback request.
type InternalCallbackResponse struct {
	Result json.RawMessage `json:"result,omitempty"`
	Error  string          `json:"error,omitempty"`
}

// handleInternalCallback handles callback requests from VMs.
// This endpoint is called by the vsockserver running inside guest VMs.
func (s *restServer) handleInternalCallback(w http.ResponseWriter, r *http.Request) {
	logger := log.WithField("api", "handleInternalCallback")

	var req InternalCallbackRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		logger.WithError(err).Error("Invalid callback request body")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(InternalCallbackResponse{
			Error: fmt.Sprintf("Invalid request format: %v", err),
		})
		return
	}

	if req.VMName == "" || req.Method == "" {
		logger.Error("Missing vmName or method in callback request")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(InternalCallbackResponse{
			Error: "vmName and method are required",
		})
		return
	}

	logger.WithFields(log.Fields{
		"vmName": req.VMName,
		"method": req.Method,
	}).Info("Processing callback from VM")

	// Route the callback to the client via WebSocket
	result, err := s.vmServer.RouteCallback(r.Context(), req.VMName, req.Method, req.Params)
	if err != nil {
		logger.WithFields(log.Fields{
			"vmName": req.VMName,
			"method": req.Method,
		}).WithError(err).Error("Failed to route callback")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(InternalCallbackResponse{
			Error: fmt.Sprintf("Callback failed: %v", err),
		})
		return
	}

	logger.WithFields(log.Fields{
		"vmName": req.VMName,
		"method": req.Method,
	}).Info("Callback completed successfully")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(InternalCallbackResponse{
		Result: result,
	})
}

func main() {
	var serverConfig *config.ServerConfig
	var configFile string

	app := &cli.App{
		Name:  "arrakis-restserver",
		Usage: "A daemon for spawning and managing cloud-hypervisor based microVMs.",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "config",
				Aliases:     []string{"c"},
				Usage:       "Path to config file",
				Destination: &configFile,
				Value:       "./config.yaml",
			},
		},
		Action: func(ctx *cli.Context) error {
			var err error
			serverConfig, err = config.GetServerConfig(configFile)
			if err != nil {
				return fmt.Errorf("server config not found: %v", err)
			}
			log.Infof("server config: %v", serverConfig)
			return nil
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.WithError(err).Fatal("server exited with error")
	}

	// At this point `serverConfig` is populated.
	// Create the session manager for handling WebSocket connections
	sessionManager := callback.NewSessionManager()

	// Create the VM server
	vmServer, err := server.NewServer(*serverConfig, sessionManager)
	if err != nil {
		log.Fatalf("failed to create VM server: %v", err)
	}

	// Set up callback to destroy VM when client disconnects
	sessionManager.OnSessionClose = func(vmName string) {
		log.WithField("vmName", vmName).Info("Client disconnected, destroying VM")
		req := serverapi.VMRequest{
			VmName: &vmName,
		}
		if _, err := vmServer.DestroyVM(context.Background(), &req); err != nil {
			log.WithField("vmName", vmName).WithError(err).Error("Failed to destroy VM on client disconnect")
		}
	}

	// Create REST server
	s := &restServer{
		vmServer:       vmServer,
		sessionManager: sessionManager,
	}
	r := mux.NewRouter()

	// Register routes
	r.HandleFunc("/"+API_VERSION+"/vms", s.startVM).Methods("POST")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}", s.updateVMState).Methods("PATCH")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}", s.destroyVM).Methods("DELETE")
	r.HandleFunc("/"+API_VERSION+"/vms", s.destroyAllVMs).Methods("DELETE")
	r.HandleFunc("/"+API_VERSION+"/vms", s.listAllVMs).Methods("GET")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}", s.listVM).Methods("GET")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}/snapshots", s.snapshotVM).Methods("POST")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}/cmd", s.vmCommand).Methods("POST")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}/files", s.vmFileUpload).Methods("POST")
	r.HandleFunc("/"+API_VERSION+"/vms/{name}/files", s.vmFileDownload).Methods("GET")
	r.HandleFunc("/"+API_VERSION+"/health", s.healthCheck).Methods("GET")

	// WebSocket endpoint for RPC callbacks
	r.HandleFunc("/"+API_VERSION+"/vms/{name}/ws", s.handleWebSocket).Methods("GET")

	// Internal endpoint for VM callbacks (called by vsockserver in guest)
	r.HandleFunc("/"+API_VERSION+"/internal/callback", s.handleInternalCallback).Methods("POST")

	// Start HTTP server
	srv := &http.Server{
		Addr:    serverConfig.Host + ":" + serverConfig.Port,
		Handler: r,
	}

	go func() {
		log.Printf("REST server listening on: %s:%s", serverConfig.Host, serverConfig.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down server...")
	if err := srv.Shutdown(context.Background()); err != nil {
		log.Fatalf("Server shutdown failed: %v", err)
	}
	vmServer.DestroyAllVMs(context.Background())
	log.Println("Server stopped")
}
