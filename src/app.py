import streamlit as st
from qa_engine import answer_query
from embed_store import get_model, create_session_collection, get_known_companies
from ingest import ingest_uploaded_pdf

MAX_REPORTS = 5

st.set_page_config(page_title="ESG Report Analyst", page_icon="🌱", layout="centered")

# --- Session-scoped state ---
if "collection" not in st.session_state:
    st.session_state.collection = create_session_collection()
if "embed_model" not in st.session_state:
    st.session_state.embed_model = get_model()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

collection = st.session_state.collection
embed_model = st.session_state.embed_model

# --- Sidebar ---
with st.sidebar:
    if st.button("🔄 New Chat / Clear Session", use_container_width=True):
        st.session_state.collection = create_session_collection()
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

    st.markdown("---")
    st.subheader("📄 Upload reports for this session")
    st.caption(f"Upload up to {MAX_REPORTS} ESG reports. They're indexed for this session only.")

    uploaded_files = st.file_uploader(
        "Upload ESG/sustainability reports (PDF)",
        type="pdf",
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files:
        if len(uploaded_files) > MAX_REPORTS:
            st.warning(f"Please upload at most {MAX_REPORTS} reports for this session.")
        else:
            for uploaded_file in uploaded_files:
                st.markdown(f"**{uploaded_file.name}**")
                company_input = st.text_input(
                    "Company name", key=f"company_{uploaded_file.name}", placeholder="e.g. TCS"
                )
                year_input = st.text_input(
                    "Reporting year", key=f"year_{uploaded_file.name}", placeholder="e.g. 2023-2024"
                )

                if st.button(
                    f"Process {uploaded_file.name}",
                    key=f"process_{uploaded_file.name}",
                    disabled=not (company_input and year_input),
                ):
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        result = ingest_uploaded_pdf(
                            uploaded_file.getvalue(), uploaded_file.name,
                            company_input, year_input, collection, embed_model
                        )
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

    st.markdown("---")
    st.subheader("This session's reports")
    companies = get_known_companies(collection)
    st.write(", ".join(companies) if companies else "No reports uploaded yet.")

    st.markdown("---")
    st.caption(
        "Answers are grounded only in reports uploaded this session. "
        "If data isn't disclosed or isn't directly comparable, this will say so."
    )

# --- Main chat area ---
st.title("🌱 ESG Report Analysis Assistant")
st.caption("Upload reports in the sidebar, then ask questions with page-level citations.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Ask a question about the uploaded reports...")

if query:
    if not get_known_companies(collection):
        st.warning("Please upload and process at least one report first.")
    else:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        known_companies = get_known_companies(collection)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving evidence..."):
                result = answer_query(
                    query,
                    known_companies,
                    collection,
                    embed_model,
                    recent_history=st.session_state.messages[:-1],
                )
                answer = result["answer"]

            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})