import streamlit as st

import exchange
from state import ensure_state, require_finance

st.set_page_config(page_title="Export Progress", layout="wide")
ensure_state()
require_finance()

st.title("Export Progress")
st.caption(
    "Grab this before you close the app. It saves everything in your current session - every "
    "salesperson's invoices/line items, whatever imports/edits/approvals/paid flags you've made "
    "so far - as one file. Reload it on **Continue Where You Left Off** next time to pick up "
    "exactly where you stopped, instead of starting over."
)

invoices = st.session_state["invoices"]
st.download_button(
    "Download current progress (.xlsx)",
    data=exchange.write_workbook(invoices, st.session_state["line_items"]),
    file_name="commission_progress.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.caption(f"{len(invoices)} invoice(s) in this session right now.")
