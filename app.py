"""
Streamlit UI for the Support Ticket Resolution System.
Pages: Chat, Admin, Integrations.
"""

import json
from pathlib import Path

import streamlit as st

from src.config import DEPARTMENTS, REGIONS, TICKET_RESOLUTIONS_PATH
from src.rag_service import answer_stream, get_admin_service

st.set_page_config(page_title="Support Ticket Resolution System", page_icon="🎫", layout="wide")
st.title("Support Ticket Resolution System")
st.markdown("_Multi-region RAG-based documentation search & third-party integration_")

# Init session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_ingest_result" not in st.session_state:
    st.session_state.last_ingest_result = None

# Sidebar navigation
with st.sidebar:
    st.subheader("Navigation")
    page = st.radio(
        "Pages",
        ["Chat", "Admin", "Integrations"],
        label_visibility="collapsed",
        key="nav_page",
    )
    if page == "Chat":
        st.divider()
        if st.button("New Chat"):
            st.session_state.messages = []
            st.rerun()

# ── Chat Page ─────────────────────────────────────────────────────────────────
if page == "Chat":
    col_region, col_dept, _ = st.columns([1, 1, 3])
    with col_region:
        region = st.selectbox("Region", REGIONS, key="region")
    with col_dept:
        department = st.selectbox(
            "Department",
            options=DEPARTMENTS,
            format_func=lambda x: "All" if x == "" else x,
            key="department",
        )

    st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for s in msg["sources"]:
                        src = s.get("source", "") if isinstance(s, dict) else s.source
                        reg = s.get("region", "") if isinstance(s, dict) else s.region
                        st.caption(f"**{src}** ({reg})")
            if "confidence" in msg:
                st.metric("Confidence", f"{msg['confidence']:.0%}")

    question = st.chat_input("Ask a question about your documentation...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            for part in answer_stream(
                question=question,
                region=region,
                department=department if department else None,
            ):
                if part["type"] == "token":
                    full_response += part["content"]
                    message_placeholder.markdown(full_response + "▌")
                elif part["type"] == "done":
                    resp = part["response"]
                    message_placeholder.markdown(resp.answer)

                    if resp.sources:
                        with st.expander("Sources"):
                            for s in resp.sources:
                                st.caption(f"**{s.source}** ({s.region})")
                    st.metric("Confidence", f"{resp.confidence:.0%}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": resp.answer,
                        "sources": [s.model_dump() for s in resp.sources],
                        "confidence": resp.confidence,
                    })
        st.rerun()

# ── Admin Page ────────────────────────────────────────────────────────────────
elif page == "Admin":
    admin = get_admin_service()

    st.subheader("Ticket Resolutions")
    st.caption("Load from `data/ticket_resolutions.json` — each ticket becomes searchable in the knowledge base.")
    if st.button("Sync Ticket Resolutions", type="secondary"):
        result = admin.sync_ticket_resolutions(TICKET_RESOLUTIONS_PATH)
        if result.success:
            st.success(f"Synced **{result.chunks_created}** ticket resolution(s)")
        else:
            st.error(f"Failed: {result.error}")

    st.divider()
    st.subheader("Upload Documents")
    col1, col2, col3 = st.columns(3)
    with col1:
        uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])
    with col2:
        doc_region = st.selectbox("Region", REGIONS, key="admin_region")
    with col3:
        dept_options = [d for d in DEPARTMENTS if d]
        dept_default = dept_options.index("General") if "General" in dept_options else 0
        department_upload = st.selectbox(
            "Department",
            options=dept_options,
            index=dept_default,
            key="admin_department",
        )

    if st.button("Ingest", type="primary") and uploaded:
        path = Path(uploaded.name)
        path.write_bytes(uploaded.getvalue())
        result = admin.upload_document(
            path,
            region=doc_region,
            department=department_upload,
        )
        path.unlink(missing_ok=True)
        st.session_state.last_ingest_result = result
        if result.success:
            st.success(f"Indexed **{result.source}** — {result.chunks_created} chunks created")
        else:
            st.error(f"Failed: {result.error or 'Ingestion failed'}")

    if st.session_state.last_ingest_result:
        r = st.session_state.last_ingest_result
        status_label = "Success" if r.success else "Failed"
        st.caption(f"Last upload: {status_label} — {r.source} ({r.region}, {r.department})")

    st.divider()
    st.subheader("Document Library")

    docs = admin.list_documents()
    if docs:
        for d in docs:
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                ts = d.uploaded_at[:16].replace("T", " ") if d.uploaded_at else ""
                uploaded_str = f" · Last updated: {ts}" if ts else ""
                st.write(
                    f"**{d.source}** · {d.region} · {d.department} · "
                    f"{d.chunk_count} chunks{uploaded_str}"
                )
            with col3:
                if st.button("Delete", key=f"del_{d.source}_{d.region}_{d.department}"):
                    admin.delete_document(d.source, region=d.region, department=d.department)
                    r = st.session_state.last_ingest_result
                    if r and r.source == d.source and r.region == d.region and r.department == d.department:
                        st.session_state.last_ingest_result = None
                    st.rerun()
    else:
        st.info("No documents yet. Upload a PDF or DOCX above.")

# ── Integrations Page ─────────────────────────────────────────────────────────
else:
    st.subheader("Third-Party Integrations")
    st.markdown(
        "Connect ServiceNow or Zendesk via webhooks. The system analyses each incoming ticket "
        "with AI, assigns it to the right person, sets the priority, and creates a Jira issue "
        "with a resolution comment — automatically."
    )

    # ── Configuration status ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Configuration Status")

    from src.config import Settings
    settings = Settings()

    col_jira, col_cohere = st.columns(2)
    with col_jira:
        if settings.jira_configured:
            st.success(f"Jira connected — {settings.jira_url}  |  Project: {settings.jira_project_key}")
        else:
            st.warning(
                "Jira not configured. Add `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` "
                "and `JIRA_PROJECT_KEY` to your `.env` file."
            )
    with col_cohere:
        if settings.cohere_api_key:
            st.success("Cohere API key configured")
        else:
            st.error("COHERE_API_KEY missing in .env")

    # ── Webhook URLs ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Webhook Endpoints")
    st.markdown(
        "Start the webhook server alongside this UI: "
        "`python -m uvicorn webhook_server:app --host 0.0.0.0 --port 8000`"
    )

    col_sn, col_zd, col_manual = st.columns(3)
    with col_sn:
        st.markdown("**ServiceNow**")
        st.code("POST http://<your-host>:8000/webhook/servicenow", language="text")
        with st.expander("Example payload"):
            st.json({
                "number": "INC0012345",
                "short_description": "VPN not connecting",
                "description": "Users in Mumbai cannot connect to VPN since 09:00 IST.",
                "caller_id": "john.doe",
                "category": "Network",
                "region": "India",
            })
    with col_zd:
        st.markdown("**Zendesk**")
        st.code("POST http://<your-host>:8000/webhook/zendesk", language="text")
        with st.expander("Example payload"):
            st.json({
                "ticket": {
                    "id": 98765,
                    "subject": "Payroll portal access denied",
                    "description": "Getting 403 error on payroll portal since morning.",
                    "requester": {"name": "Jane Smith", "email": "jane@company.com"},
                    "tags": ["region_india", "finance"],
                },
            })
    with col_manual:
        st.markdown("**Manual / Test**")
        st.code("POST http://<your-host>:8000/webhook/manual", language="text")
        with st.expander("Example payload"):
            st.json({
                "source_system": "manual",
                "external_id": "TEST-001",
                "subject": "Cannot access HR portal",
                "description": "Employee getting login error on HR self-service portal.",
                "region": "India",
            })

    # ── Test Analyser ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Test Ticket Analyser")
    st.caption("Paste a ticket description to preview the AI decision without calling an external system or creating a Jira issue.")

    with st.form("test_analyser"):
        t_subject = st.text_input("Subject", placeholder="e.g. VPN not connecting in Mumbai office")
        t_desc = st.text_area(
            "Description",
            height=130,
            placeholder="Describe the issue in detail...",
        )
        t_region = st.selectbox("Region", REGIONS, key="int_region")
        t_source = st.selectbox("Simulated Source", ["servicenow", "zendesk", "manual"])
        submitted = st.form_submit_button("Analyse", type="primary")

    if submitted and t_subject and t_desc:
        from src.decision_engine import DecisionEngine
        from src.models import IncomingTicket

        with st.spinner("Analysing with AI..."):
            ticket = IncomingTicket(
                source_system=t_source,
                external_id="PREVIEW-001",
                subject=t_subject,
                description=t_desc,
                region=t_region,
            )
            engine = DecisionEngine()
            decision = engine.analyse(ticket)

        priority_colors = {"P1": "red", "P2": "orange", "P3": "blue", "P4": "green"}
        priority_color = priority_colors.get(decision.priority, "blue")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Department", decision.department)
        c2.metric("Priority", decision.priority)
        c3.metric("Assignee", decision.assignee_name)
        c4.metric("Confidence", f"{decision.confidence:.0%}")

        st.info(f"**Priority Reason:** {decision.priority_reason}")

        st.markdown("**AI Resolution Steps**")
        st.markdown(decision.resolution)

        if decision.sources:
            with st.expander("Knowledge Base Sources Used"):
                for s in decision.sources:
                    st.caption(f"**{s.source}** ({s.region})")

    elif submitted:
        st.warning("Please fill in both Subject and Description.")

    # ── Integration Logs ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Recent Integration Events")

    from src.webhook_handler import read_integration_logs

    col_refresh, col_limit, _ = st.columns([1, 1, 4])
    with col_limit:
        log_limit = st.selectbox("Show last", [10, 25, 50, 100], key="log_limit")
    with col_refresh:
        st.button("Refresh", key="refresh_logs")

    logs = read_integration_logs(limit=log_limit)

    if logs:
        for log in logs:
            ts = log.timestamp[:19].replace("T", " ") if log.timestamp else ""
            status_icon = "green" if log.success else "red"
            status_text = "Success" if log.success else "Failed"

            with st.expander(
                f"[{ts}]  {log.source_system.upper()}  |  {log.external_id}  |  "
                f"{log.subject[:60]}  |  {log.priority}  |  {status_text}"
            ):
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Department", log.department)
                col_b.metric("Priority", log.priority)
                col_c.metric("Assignee", log.assignee_name)
                col_d.metric("Status", status_text)

                if log.jira_issue_key:
                    jira_link = (
                        f"[{log.jira_issue_key}]({log.jira_issue_url})"
                        if log.jira_issue_url
                        else log.jira_issue_key
                    )
                    st.markdown(f"**Jira Issue:** {jira_link}")
                if log.error:
                    st.error(f"Error: {log.error}")
    else:
        st.info(
            "No integration events yet. "
            "Start the webhook server and send a test request, or use the Test Analyser above."
        )
