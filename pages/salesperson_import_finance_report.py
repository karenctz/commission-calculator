import streamlit as st

import exchange
from state import current_salesperson, ensure_state, require_salesperson

st.set_page_config(page_title="Import Finance Report", layout="wide")
ensure_state()
require_salesperson()

me = current_salesperson()
st.title("Import Finance Report")
st.caption(
    f"Signed in as **{me}**. Load the exchange file Finance sent you - this becomes your whole "
    "working session on My Invoices. This page never reads the master dataset, so there's "
    "nothing here to leak even by accident."
)

session_key = f"my_invoices_{me}"
lines_key = f"my_line_items_{me}"

if session_key in st.session_state:
    st.success(
        f"You already have a file loaded ({len(st.session_state[session_key])} invoices). "
        "Head to **My Invoices** to work through it, or start over below."
    )
    if st.button("Start over (discard imported file)"):
        del st.session_state[session_key]
        del st.session_state[lines_key]
        st.rerun()
    st.stop()

uploaded = st.file_uploader("Your exchange file (.xlsx)", type=["xlsx"], key="my_upload")
use_sample = st.button(
    f"Use a sample file for {me} instead",
    help="Prototype shortcut - simulates having received and opened Finance's export",
)
if uploaded:
    inv, lines = exchange.read_export(uploaded.read())
    st.session_state[session_key] = inv
    st.session_state[lines_key] = lines
    st.rerun()
elif use_sample:
    master_inv = st.session_state["invoices"]
    master_lines = st.session_state["line_items"]
    xlsx_bytes = exchange.build_export(master_inv, master_lines, me)
    inv, lines = exchange.read_export(xlsx_bytes)
    st.session_state[session_key] = inv
    st.session_state[lines_key] = lines
    st.rerun()
else:
    st.info("Upload the file (or click the sample button) to continue to My Invoices.")
