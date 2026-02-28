"""
Streamlit UI for the Support ticket resolution system.
Chat (with streaming), Admin (upload, list, delete).
"""

import streamlit as st
from pathlib import Path

from src.config import DEPARTMENTS, REGIONS, TICKET_RESOLUTIONS_PATH
from src.rag_service import answer_stream, get_admin_service

st.set_page_config(page_title="Support Ticket Resolution System", page_icon="🎫", layout="wide")
st.title("Support Ticket Resolution System")
st.markdown("_Multi-region RAG-based documentation search_")

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
        ["Chat", "Admin"],
        label_visibility="collapsed",
        key="nav_page",
    )
    if page == "Chat":
        st.divider()
        if st.button("New Chat"):
            st.session_state.messages = []
            st.rerun()

# --- Chat Page ---
if page == "Chat":
    # Filters above chat (scoped search)
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

# --- Admin Page ---
else:
    admin = get_admin_service()

    st.subheader("Ticket Resolutions")
    st.caption("Load from `data/ticket_resolutions.json` — each ticket becomes searchable in the knowledge base.")
    if st.button("Sync Ticket Resolutions", type="secondary"):
        result = admin.sync_ticket_resolutions(TICKET_RESOLUTIONS_PATH)
        if result.success:
            st.success(f"✓ Synced **{result.chunks_created}** ticket resolution(s)")
        else:
            st.error(f"✗ Failed: {result.error}")

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
            st.success(f"✓ Indexed **{result.source}** — {result.chunks_created} chunks created")
        else:
            st.error(f"✗ Failed: {result.error or 'Ingestion failed'}")

    # Last upload status (persists until next upload)
    if st.session_state.last_ingest_result:
        r = st.session_state.last_ingest_result
        status = "🟢 Success" if r.success else "🔴 Failed"
        st.caption(f"Last upload: {status} — {r.source} ({r.region}, {r.department})")

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
