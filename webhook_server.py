"""
Webhook Server – FastAPI app that receives events from ServiceNow and Zendesk,
runs the AI decision pipeline, and creates Jira issues.

Run with:
    python -m uvicorn webhook_server:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    POST /webhook/servicenow   – receive ServiceNow incident events
    POST /webhook/zendesk      – receive Zendesk ticket events
    POST /webhook/manual       – test with a manually constructed ticket
    GET  /health               – liveness check
    GET  /logs                 – recent integration log entries
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.models import IncomingTicket
from src.webhook_handler import (
    normalise_servicenow,
    normalise_zendesk,
    process_ticket,
    read_integration_logs,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Support Ticket Resolution System – Webhook API",
    description=(
        "Receives webhook events from ServiceNow and Zendesk, "
        "analyses them with AI (RAG + Cohere), and creates enriched Jira issues "
        "with auto-assignment, priority scoring, and resolution comments."
    ),
    version="1.0.0",
)


# ── Liveness ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "Support Ticket Resolution System Webhook API"}


# ── ServiceNow ────────────────────────────────────────────────────────────────

@app.post("/webhook/servicenow", tags=["Webhooks"])
async def servicenow_webhook(request: Request):
    """
    Receive a ServiceNow incident webhook.

    Configure in ServiceNow:
      Business Rule → Outbound REST Message → POST to this URL
      Payload example:
        {
          "number": "INC0012345",
          "short_description": "VPN not connecting",
          "description": "Users in Mumbai office cannot connect to VPN since 09:00 IST.",
          "caller_id": "john.doe",
          "category": "Network",
          "region": "India"
        }
    """
    payload: Dict[str, Any] = await _parse_body(request)
    ticket = normalise_servicenow(payload)
    return await _run_pipeline(ticket)


# ── Zendesk ───────────────────────────────────────────────────────────────────

@app.post("/webhook/zendesk", tags=["Webhooks"])
async def zendesk_webhook(request: Request):
    """
    Receive a Zendesk ticket webhook.

    Configure in Zendesk:
      Admin → Objects & Rules → Webhooks → Create webhook → POST to this URL
      Trigger: Ticket Created
      Payload example:
        {
          "ticket": {
            "id": 98765,
            "subject": "Payroll system access denied",
            "description": "Cannot log in to payroll portal. Getting 403 error.",
            "requester": { "name": "Jane Smith", "email": "jane@company.com" },
            "tags": ["region_india", "finance"]
          }
        }
    """
    payload: Dict[str, Any] = await _parse_body(request)
    ticket = normalise_zendesk(payload)
    return await _run_pipeline(ticket)


# ── Manual / test ─────────────────────────────────────────────────────────────

@app.post("/webhook/manual", tags=["Webhooks"])
async def manual_webhook(ticket: IncomingTicket):
    """
    Submit a manually constructed ticket for testing without a real external system.

    Request body: IncomingTicket JSON
    """
    return await _run_pipeline(ticket)


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.get("/logs", tags=["System"])
def get_logs(limit: int = 20):
    """Return the most recent integration log entries (newest first)."""
    entries = read_integration_logs(limit=limit)
    return {"count": len(entries), "entries": [e.model_dump() for e in entries]}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _parse_body(request: Request) -> Dict[str, Any]:
    try:
        return await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON body: {exc}",
        )


async def _run_pipeline(ticket: IncomingTicket) -> JSONResponse:
    try:
        decision, jira_result = process_ticket(ticket)
    except Exception as exc:
        logger.exception("Pipeline error for ticket %s", ticket.external_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {exc}",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "ticket": {
                "source_system": ticket.source_system,
                "external_id": ticket.external_id,
                "subject": ticket.subject,
            },
            "decision": {
                "department": decision.department,
                "priority": decision.priority,
                "priority_reason": decision.priority_reason,
                "assignee_name": decision.assignee_name,
                "confidence": decision.confidence,
                "resolution": decision.resolution,
                "sources": [s.model_dump() for s in decision.sources],
            },
            "jira": {
                "success": jira_result.success,
                "issue_key": jira_result.issue_key,
                "issue_url": jira_result.issue_url,
                "error": jira_result.error,
            },
        },
    )
