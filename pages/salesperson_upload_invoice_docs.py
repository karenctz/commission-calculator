import streamlit as st

from state import current_salesperson, ensure_state, require_salesperson

st.set_page_config(page_title="Upload Invoice Documents", layout="wide")
ensure_state()
require_salesperson()

me = current_salesperson()
st.title("Upload Invoice Documents")
st.caption(
    "If Auto-Match couldn't find one of your invoice PDFs (missing from the shared SharePoint "
    "folder), upload it here - it lands in your own folder so Finance's next Auto-Match run can "
    "pick it up. Prototype: nothing is actually written to SharePoint yet, this just shows where "
    "it would land."
)

root = st.session_state.get("root_folder") or f"<your SharePoint folder>/{me}"
state_key = f"uploaded_invoice_docs_{me}"
if state_key not in st.session_state:
    st.session_state[state_key] = []

uploaded = st.file_uploader("Invoice PDF(s)", type=["pdf"], accept_multiple_files=True, key="invoice_doc_upload")
if uploaded:
    for f in uploaded:
        dest = f"{root}/Invoices/{f.name}"
        if not any(u["name"] == f.name for u in st.session_state[state_key]):
            st.session_state[state_key].append({"name": f.name, "path": dest, "size": f.size})
    st.success(f"Uploaded {len(uploaded)} file(s) - would land at the paths below.")

if st.session_state[state_key]:
    st.subheader("Uploaded this session")
    st.dataframe(
        [{"File": u["name"], "Would land at": u["path"], "Size (KB)": round(u["size"] / 1024, 1)} for u in st.session_state[state_key]],
        use_container_width=True, hide_index=True,
    )
else:
    st.info("No files uploaded yet.")
