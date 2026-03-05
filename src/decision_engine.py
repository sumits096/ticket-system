"""
Decision Engine – analyses an incoming ticket using RAG and returns
a structured decision: department, priority, assignee and resolution steps.
"""

import json
import logging
import re
from typing import Dict, List, Optional

import cohere

from src.config import ASSIGNEE_MAP, CHAT_MODEL, TOP_K_RETRIEVAL, Settings
from src.embedding_service import EmbeddingService
from src.models import IncomingTicket, SourceCitation, TicketDecision
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

# ── Keyword-based department classification ───────────────────────────────────
# Each department maps to a list of keywords found in subject/description.
# Longer / more specific phrases are matched first (order matters within each list).
DEPARTMENT_KEYWORDS: Dict[str, List[str]] = {
    "Infra": [
        "vpn", "network", "server", "database", "db ", " db", "postgres", "mysql",
        "mongodb", "redis", "kubernetes", "k8s", "docker", "cloud", "aws", "azure",
        "gcp", "s3 ", "ec2", "vm ", "virtual machine", "firewall", "ssl", "tls",
        "certificate", "dns", "ip address", "bandwidth", "latency", "downtime",
        "outage", "deployment", "devops", "ci/cd", "pipeline", "jenkins", "linux",
        "windows server", "active directory", "ldap", "storage", "disk", "cpu",
        "memory", "ram", "backup", "restore", "wifi", "internet", "switch", "router",
        "laptop", "hardware", "monitor", "hdmi", "printer", "email server", "smtp",
        "production down", "service down", "application down", "site down",
        "500 error", "503", "504", "timeout", "crash", "reboot",
    ],
    "HR": [
        "payroll portal", "payroll", "salary slip", "salary", "leave request",
        "leave balance", "leave", "attendance", "onboarding", "offboarding",
        "resignation", "termination", "appraisal", "performance review", "hr portal",
        "hr self-service", "hr self service", "employee portal", "self service",
        "benefits", "insurance", "pf ", "provident fund", "gratuity", "bonus",
        "increment", "promotion", "transfer", "joining", "offer letter",
        "appointment letter", "relieving letter", "noc", "training", "induction",
        "id card", "access card", "badge", "background check", "bgv", "employee id",
    ],
    "Finance": [
        "invoice", "payment gateway", "payment", "reimbursement", "expense claim",
        "expense", "budget", "billing", "accounts payable", "accounts receivable",
        "accounts", "accounting", "sap erp", "sap", "erp", "tally", "quickbooks",
        "tax filing", "tax", "gst filing", "gst", "tds", "vendor payment",
        "vendor", "purchase order", "po ", " po", "finance portal", "financial report",
        "financial", "ledger", "balance sheet", "p&l", "profit", "loss",
        "audit", "compliance", "receipt", "credit note", "debit note",
        "bank statement", "bank", "transaction", "month end closing", "month end",
        "quarter end", "year end", "closing entries",
    ],
}


def _keyword_department(text: str) -> Optional[str]:
    """Return the best-matching department from ticket text using keyword scoring."""
    text_lower = text.lower()
    scores: Dict[str, int] = {"Infra": 0, "HR": 0, "Finance": 0}
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                # Longer keywords score higher
                scores[dept] += len(kw.split())
    best_dept = max(scores, key=lambda d: scores[d])
    return best_dept if scores[best_dept] > 0 else None


DECISION_SYSTEM_PROMPT = """You are an expert IT/business support analyst.

Analyse the incoming support ticket and produce a JSON decision.

Department classification rules (choose ONE):
- "Infra"   : anything about servers, VPN, network, databases, cloud, DevOps, hardware,
               software installations, email servers, outages, deployments, security certs
- "HR"      : payroll portal, salary slips, leave, attendance, onboarding, employee benefits,
               HR self-service, PF, appraisals, ID cards, background verification
- "Finance" : invoices, payments, reimbursements, SAP/ERP, tax, GST, vendor management,
               purchase orders, accounting, expense claims, month-end closing
- "General" : access requests, Confluence/Jira access, general how-to, miscellaneous

Priority guidelines:
- P1 (Critical): production down, data loss, security breach, ALL users affected
- P2 (High): major feature broken, many users affected, no workaround
- P3 (Medium): partial impact, workaround available, deadline-sensitive
- P4 (Low): cosmetic, how-to question, nice-to-have

Respond with ONLY this JSON object (no markdown fences, no extra text):
{
  "department": "<Infra | HR | Finance | General>",
  "priority": "<P1 | P2 | P3 | P4>",
  "priority_reason": "<one sentence>",
  "assignee_name": "<team or role best suited>",
  "resolution": "<numbered step-by-step resolution>"
}
"""


class DecisionEngine:
    """Uses RAG retrieval + Cohere to decide assignee, priority and resolution."""

    def __init__(self):
        settings = Settings()
        self._client = cohere.ClientV2(api_key=settings.cohere_api_key)
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStore()
        self._model = CHAT_MODEL
        self._top_k = TOP_K_RETRIEVAL

    def analyse(self, ticket: IncomingTicket) -> TicketDecision:
        """Retrieve similar context then ask Cohere to decide on the ticket."""
        query_text = f"{ticket.subject}\n\n{ticket.description}"

        # Pre-classify department from keywords (used as hint + fallback)
        keyword_dept = _keyword_department(query_text)
        logger.info("Keyword-based department hint: %s", keyword_dept or "none")

        # Retrieve relevant chunks from the knowledge base
        embedding = self._embedding_service.embed_query(query_text)
        chunks = self._vector_store.search(
            query_embedding=embedding,
            region=ticket.region,
            top_k=self._top_k,
        )

        documents = [
            {
                "data": {
                    "text": c.content,
                    "title": c.source,
                    "region": c.region,
                }
            }
            for c in chunks
        ]

        # Embed the keyword hint directly in the user message so the LLM sees it
        hint_line = (
            f"Keyword analysis suggests department: {keyword_dept}. "
            f"Use this as a strong signal unless the description clearly indicates otherwise.\n\n"
            if keyword_dept else ""
        )
        user_message = (
            f"Incoming ticket from {ticket.source_system.upper()}\n"
            f"ID: {ticket.external_id}\n"
            f"Subject: {ticket.subject}\n\n"
            f"{hint_line}"
            f"Description:\n{ticket.description}"
        )

        raw_json = ""
        try:
            stream = self._client.chat_stream(
                model=self._model,
                messages=[
                    {"role": "system", "content": DECISION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                documents=documents if documents else None,
            )
            parts: List[str] = []
            for event in stream:
                if not event:
                    continue
                ev_type = getattr(event, "type", None) or getattr(event, "event_type", None)
                if ev_type == "content-delta":
                    delta = getattr(event, "delta", None)
                    if delta and hasattr(delta, "message"):
                        msg = delta.message
                        if hasattr(msg, "content") and msg.content:
                            txt = getattr(msg.content, "text", None) or (
                                msg.content.get("text") if isinstance(msg.content, dict) else None
                            )
                            if txt:
                                parts.append(txt)
            raw_json = "".join(parts).strip()
        except Exception:
            logger.exception("Cohere call failed during ticket analysis")
            return self._fallback_decision(ticket)

        decision_data = self._parse_json(raw_json)
        if not decision_data:
            logger.warning("Could not parse decision JSON, using fallback. Raw: %s", raw_json[:200])
            return self._fallback_decision(ticket)

        # Build source citations
        seen: set = set()
        citations: List[SourceCitation] = []
        for c in chunks:
            key = (c.source, c.region)
            if key not in seen:
                seen.add(key)
                citations.append(SourceCitation(source=c.source, region=c.region))

        avg_score = (sum(c.score for c in chunks) / len(chunks)) if chunks else 0.0
        confidence = round(min(0.95, 0.5 + avg_score * 0.45), 2)

        department = decision_data.get("department", "General")
        if department not in ("Infra", "HR", "Finance", "General"):
            department = "General"

        # If LLM fell back to General but keyword detection found a specific dept, trust keywords
        if department == "General" and keyword_dept and keyword_dept != "General":
            logger.info(
                "LLM returned General; overriding with keyword department: %s", keyword_dept
            )
            department = keyword_dept

        assignee = decision_data.get("assignee_name") or ASSIGNEE_MAP.get(department, "support-team@company.com")

        priority = self._sanitise_priority(decision_data.get("priority", ""))

        return TicketDecision(
            department=department,
            priority=priority,
            priority_reason=self._to_str(decision_data.get("priority_reason")) or "AI-assessed priority.",
            assignee_name=self._to_str(assignee) or "support-team@company.com",
            resolution=self._to_str(decision_data.get("resolution")) or "Please review manually.",
            confidence=confidence,
            sources=citations,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_str(value) -> str:
        """Coerce any LLM output field to a plain string."""
        if value is None:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value)

    def _sanitise_priority(self, value: str) -> str:
        """Normalise any priority string the LLM returns to a valid P1–P4 value."""
        valid = {"P1", "P2", "P3", "P4"}
        if value in valid:
            return value
        # Handle variants like "p2", "2", "High", "Medium", etc.
        mapping = {
            "1": "P1", "p1": "P1", "critical": "P1", "highest": "P1",
            "2": "P2", "p2": "P2", "high": "P2",
            "3": "P3", "p3": "P3", "medium": "P3", "normal": "P3",
            "4": "P4", "p4": "P4", "low": "P4", "lowest": "P4",
        }
        return mapping.get(str(value).strip().lower(), "P3")

    def _parse_json(self, text: str) -> dict | None:
        """Try to extract and parse a JSON object from the model output."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try to find the first {...} block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None

    def _fallback_decision(self, ticket: IncomingTicket) -> TicketDecision:
        """Return a safe default decision when AI analysis fails."""
        return TicketDecision(
            department="General",
            priority="P3",
            priority_reason="Could not analyse ticket automatically — defaulting to Medium priority.",
            assignee_name=ASSIGNEE_MAP.get("General", "support-team@company.com"),
            resolution="Please review this ticket manually. Automatic analysis was unavailable.",
            confidence=0.0,
        )
