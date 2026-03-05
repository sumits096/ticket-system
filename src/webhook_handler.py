"""
Webhook Handler – normalises payloads from ServiceNow and Zendesk,
orchestrates the AI decision pipeline, creates the Jira issue,
and writes an integration audit log.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from src.config import INTEGRATION_LOG_PATH
from src.decision_engine import DecisionEngine
from src.jira_service import JiraService
from src.models import (
    IncomingTicket,
    IntegrationLog,
    JiraIssueResult,
    TicketDecision,
)

logger = logging.getLogger(__name__)

# Lazy-initialised singletons (shared across requests in the same process)
_decision_engine: DecisionEngine | None = None
_jira_service: JiraService | None = None


def _get_decision_engine() -> DecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine


def _get_jira_service() -> JiraService:
    global _jira_service
    if _jira_service is None:
        _jira_service = JiraService()
    return _jira_service


# ── Payload normalisers ───────────────────────────────────────────────────────

def normalise_servicenow(payload: Dict[str, Any]) -> IncomingTicket:
    """
    Normalise a ServiceNow incident webhook payload.

    Expected fields (Business Rule outbound REST):
        sys_id, number, short_description, description,
        category, caller_id (display value), urgency, impact
    """
    region_map = {
        "india": "India",
        "us": "US",
        "united states": "US",
    }
    raw_region = str(payload.get("region", "")).strip().lower()
    region = region_map.get(raw_region, "All")

    return IncomingTicket(
        source_system="servicenow",
        external_id=payload.get("number") or payload.get("sys_id", "UNKNOWN"),
        subject=payload.get("short_description", "(no subject)"),
        description=payload.get("description", ""),
        reporter=payload.get("caller_id", ""),
        region=region,
        raw_payload=payload,
    )


def normalise_zendesk(payload: Dict[str, Any]) -> IncomingTicket:
    """
    Normalise a Zendesk ticket webhook payload.

    Zendesk sends the ticket object inside a 'ticket' key when using
    Target / Trigger webhooks, or directly at the top level for HTTP targets.
    """
    ticket_data: Dict[str, Any] = payload.get("ticket", payload)

    region_map = {
        "india": "India",
        "us": "US",
        "united states": "US",
    }
    # Zendesk tags can carry region info e.g. ["region_india", "priority_high"]
    tags = ticket_data.get("tags", [])
    region = "All"
    for tag in tags:
        tag_lower = str(tag).lower().replace("region_", "")
        if tag_lower in region_map:
            region = region_map[tag_lower]
            break

    requester = ticket_data.get("requester", {})
    reporter = requester.get("name") or requester.get("email", "")

    return IncomingTicket(
        source_system="zendesk",
        external_id=str(ticket_data.get("id", "UNKNOWN")),
        subject=ticket_data.get("subject", "(no subject)"),
        description=ticket_data.get("description", ""),
        reporter=reporter,
        region=region,
        raw_payload=payload,
    )


# ── Main orchestration ────────────────────────────────────────────────────────

def process_ticket(
    ticket: IncomingTicket,
) -> Tuple[TicketDecision, JiraIssueResult]:
    """
    Full pipeline:
      1. Run decision engine (RAG + Cohere) → TicketDecision
      2. Create Jira issue with assignee, priority, AI resolution comment
      3. Write audit log entry
    Returns (decision, jira_result).
    """
    logger.info(
        "Processing %s ticket %s: %s",
        ticket.source_system,
        ticket.external_id,
        ticket.subject[:80],
    )

    decision = _get_decision_engine().analyse(ticket)
    logger.info(
        "Decision → dept=%s priority=%s assignee=%s confidence=%.0f%%",
        decision.department,
        decision.priority,
        decision.assignee_name,
        decision.confidence * 100,
    )

    jira_result = _get_jira_service().create_issue(ticket, decision)
    if jira_result.success:
        logger.info("Jira issue created: %s", jira_result.issue_key)
    else:
        logger.warning("Jira issue creation failed: %s", jira_result.error)

    _write_log(ticket, decision, jira_result)
    return decision, jira_result


# ── Audit log ─────────────────────────────────────────────────────────────────

def _write_log(
    ticket: IncomingTicket,
    decision: TicketDecision,
    jira_result: JiraIssueResult,
) -> None:
    log_entry = IntegrationLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_system=ticket.source_system,
        external_id=ticket.external_id,
        subject=ticket.subject,
        department=decision.department,
        priority=decision.priority,
        assignee_name=decision.assignee_name,
        jira_issue_key=jira_result.issue_key,
        jira_issue_url=jira_result.issue_url,
        success=jira_result.success,
        error=jira_result.error,
    )
    try:
        with open(INTEGRATION_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(log_entry.model_dump_json() + "\n")
    except Exception:
        logger.warning("Could not write integration log", exc_info=True)


def read_integration_logs(limit: int = 50) -> list[IntegrationLog]:
    """Return the most recent integration log entries (newest first)."""
    try:
        with open(INTEGRATION_LOG_PATH, encoding="utf-8") as fh:
            lines = [l.strip() for l in fh if l.strip()]
        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(IntegrationLog.model_validate_json(line))
            except Exception:
                continue
        return entries
    except FileNotFoundError:
        return []
