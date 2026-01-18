"""Mock email tools for the email assistant example."""

from typing import TypedDict

# --- Tool Argument Types ---


class ReadInboxArgs(TypedDict):
    pass


class SendEmailArgs(TypedDict):
    to: str
    subject: str
    body: str


class SearchWebArgs(TypedDict):
    query: str


# --- Tool Output Types ---


class Email(TypedDict):
    id: str
    sender: str  # renamed from 'from' since 'from' is a keyword
    subject: str
    body: str


class ReadInboxResult(TypedDict):
    emails: list[Email]


class SendEmailResult(TypedDict):
    success: bool
    message: str


class SearchWebResult(TypedDict):
    results: list[str]


# --- Mock Tools ---


def read_inbox(args: ReadInboxArgs) -> ReadInboxResult:
    """Read emails from the user's inbox.

    Returns object with 'emails' array. Each email has: id, sender, subject, body.
    """
    return {
        "emails": [
            {
                "id": "1",
                "sender": "cfo@company.com",
                "subject": "Q4 Financial Results",
                "body": "Revenue exceeded projections by 23%. Great work team!",
            },
            {
                "id": "2",
                "sender": "devops@company.com",
                "subject": "Server Status",
                "body": "All systems operational. No incidents today.",
            },
        ]
    }


def send_email(args: SendEmailArgs) -> SendEmailResult:
    """Send an email to a recipient.

    Returns object with 'success' (bool) and 'message' (string).
    """
    print(f"  [MOCK] Sending email to {args['to']}: {args['subject']}")
    return {
        "success": True,
        "message": f"Email sent to {args['to']} with subject: {args['subject']}",
    }


def search_web(args: SearchWebArgs) -> SearchWebResult:
    """Search the web for information.

    Returns object with 'results' array of strings.
    """
    return {
        "results": [
            f"Search result for: {args['query']}",
            "Some relevant information found on the web.",
        ]
    }


# Export all tools
TOOLS = [read_inbox, send_email, search_web]
