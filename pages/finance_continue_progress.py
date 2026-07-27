import streamlit as st

import exchange
from state import ensure_state, require_finance

st.set_page_config(page_title="Continue Where You Left Off", layout="wide")
ensure_state()
require_finance()

st.title("Continue Where You Left Off")
st.caption(
    "Nothing persists automatically yet - this app doesn't have (or need) a database, but that "
    "does mean your approvals/paid flags/edits only live in this browser session. Load a "
    "progress file you saved earlier (see **Export Progress**) to pick up exactly where you "
    "left off, instead of starting over from the BC/PO/Worksheet imports with everything back "
    "to not-yet-reviewed."
)

progress_file = st.file_uploader(
    "Your saved progress file (.xlsx)", type=["xlsx"], key="progress_upload",
)
if progress_file:
    inv, lines = exchange.read_export(progress_file.read())
    st.session_state["invoices"] = inv
    st.session_state["line_items"] = lines
    st.success(f"Loaded {len(inv)} invoice(s) from your saved progress file.")
else:
    st.info(
        "Upload a file to restore it as your working session. If you don't have one yet, this "
        "session is already using the fresh sample dataset - go to **Export Progress** later to "
        "save your work before closing.",
        icon="📥",
    )
