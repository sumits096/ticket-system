"""
Jira Service – creates issues via the Jira Cloud REST API v3.

Requires these env vars (set in .env):
    JIRA_URL          https://yourorg.atlassian.net
    JIRA_EMAIL        your-email@company.com
    JIRA_API_TOKEN    token from https://id.atlassian.com/manage-profile/security/api-tokens
    JIRA_PROJECT_KEY  e.g. SUP
"""

import logging
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

from src.config import ASSIGNEE_MAP, JIRA_PRIORITY_MAP, Settings
from src.models import IncomingTicket, JiraIssueResult, TicketDecision

logger = logging.getLogger(__name__)


class JiraService:
    """Creates Jira issues and posts AI resolution as a comment."""

    def __init__(self):
        self._settings = Settings()
        self._base_url = self._settings.jira_url.rstrip("/")
        self._auth = HTTPBasicAuth(
            self._settings.jira_email,
            self._settings.jira_api_token,
        )
        self._project_key = self._settings.jira_project_key
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def create_issue(
        self,
        ticket: IncomingTicket,
        decision: TicketDecision,
    ) -> JiraIssueResult:
        """
        Create a Jira issue from the incoming ticket + AI decision.
        Posts the AI resolution as a comment on the newly created issue.
        """
        if not self._settings.jira_configured:
            return JiraIssueResult(
                success=False,
                error="Jira is not configured. Set JIRA_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env",
            )

        issue_result = self._create_issue(ticket, decision)
        if not issue_result.success or not issue_result.issue_key:
            return issue_result

        # Post resolution as a work comment
        self._add_comment(issue_result.issue_key, ticket, decision)

        return issue_result

    # ── Private helpers ───────────────────────────────────────────────────────

    def _create_issue(
        self,
        ticket: IncomingTicket,
        decision: TicketDecision,
    ) -> JiraIssueResult:
        jira_priority = JIRA_PRIORITY_MAP.get(decision.priority, "Medium")

        description_adf = self._build_description_adf(ticket, decision)

        payload: dict = {
            "fields": {
                "project": {"key": self._project_key},
                "summary": f"[{ticket.source_system.upper()}] {ticket.subject}",
                "description": description_adf,
                "issuetype": {"name": "Bug"},
                "priority": {"name": jira_priority},
                "labels": [
                    "auto-assigned",
                    "ai-analysed",
                    ticket.source_system,
                ],
            }
        }

        # Attempt to set assignee by email (works when user management is not strict)
        assignee_email = ASSIGNEE_MAP.get(decision.department)
        if assignee_email:
            account_id = self._resolve_account_id(assignee_email)
            if account_id:
                payload["fields"]["assignee"] = {"accountId": account_id}

        url = f"{self._base_url}/rest/api/3/issue"
        try:
            resp = requests.post(
                url,
                json=payload,
                auth=self._auth,
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            issue_key = data.get("key", "")
            issue_url = f"{self._base_url}/browse/{issue_key}"
            logger.info("Created Jira issue %s for external ticket %s", issue_key, ticket.external_id)
            return JiraIssueResult(success=True, issue_key=issue_key, issue_url=issue_url)
        except requests.HTTPError as exc:
            body = ""
            try:
                body = exc.response.text[:500]
            except Exception:
                pass
            logger.error("Jira API error creating issue: %s — %s", exc, body)
            return JiraIssueResult(success=False, error=f"Jira API error: {exc} — {body}")
        except Exception as exc:
            logger.exception("Unexpected error creating Jira issue")
            return JiraIssueResult(success=False, error=str(exc))

    def _add_comment(
        self,
        issue_key: str,
        ticket: IncomingTicket,
        decision: TicketDecision,
    ) -> None:
        """Post the AI-generated resolution as a comment on the Jira issue."""
        comment_body = self._build_comment_adf(ticket, decision)
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}/comment"
        try:
            resp = requests.post(
                url,
                json={"body": comment_body},
                auth=self._auth,
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            logger.info("Posted AI resolution comment on %s", issue_key)
        except Exception:
            logger.warning("Could not post comment on %s", issue_key, exc_info=True)

    def _resolve_account_id(self, email: str) -> Optional[str]:
        """Look up a Jira account ID by email address."""
        url = f"{self._base_url}/rest/api/3/user/search"
        try:
            resp = requests.get(
                url,
                params={"query": email},
                auth=self._auth,
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            users = resp.json()
            if users:
                return users[0].get("accountId")
        except Exception:
            logger.debug("Could not resolve account ID for %s", email, exc_info=True)
        return None

    # ── Atlassian Document Format (ADF) builders ──────────────────────────────

    def _build_description_adf(self, ticket: IncomingTicket, decision: TicketDecision) -> dict:
        """Build an ADF document for the Jira issue description."""
        return {
            "version": 1,
            "type": "doc",
            "content": [
                self._adf_heading(f"Source: {ticket.source_system.upper()} — Ticket {ticket.external_id}", 3),
                self._adf_paragraph(f"Reporter: {ticket.reporter or 'Unknown'}"),
                self._adf_paragraph(f"Region: {ticket.region}"),
                self._adf_heading("Original Description", 4),
                self._adf_paragraph(ticket.description),
                self._adf_heading("AI Analysis", 4),
                self._adf_paragraph(
                    f"Department: {decision.department}  |  "
                    f"Priority: {decision.priority}  |  "
                    f"Confidence: {decision.confidence:.0%}"
                ),
                self._adf_paragraph(f"Priority Reason: {decision.priority_reason}"),
            ],
        }

    def _build_comment_adf(self, ticket: IncomingTicket, decision: TicketDecision) -> dict:
        """Build an ADF document for the resolution comment."""
        resolution_lines = decision.resolution.split("\n")
        content = [
            self._adf_heading("AI-Generated Resolution", 3),
            self._adf_paragraph(
                f"Assigned to: {decision.assignee_name}  |  "
                f"Priority: {decision.priority}  |  "
                f"Confidence: {decision.confidence:.0%}"
            ),
        ]
        for line in resolution_lines:
            line = line.strip()
            if line:
                content.append(self._adf_paragraph(line))

        if decision.sources:
            content.append(self._adf_heading("Knowledge Base Sources", 4))
            for s in decision.sources:
                content.append(self._adf_paragraph(f"- {s.source} ({s.region})"))

        content.append(
            self._adf_paragraph(
                f"[Auto-generated by Support Ticket Resolution System from {ticket.source_system.upper()} ticket {ticket.external_id}]"
            )
        )
        return {"version": 1, "type": "doc", "content": content}

    @staticmethod
    def _adf_paragraph(text: str) -> dict:
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": text or " "}],
        }

    @staticmethod
    def _adf_heading(text: str, level: int = 3) -> dict:
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": [{"type": "text", "text": text}],
        }
