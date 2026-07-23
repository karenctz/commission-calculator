import streamlit as st

import report
from state import ensure_state, require_finance

st.set_page_config(page_title="Export", layout="wide")
ensure_state()
require_finance()

st.title("Export")
st.caption(
    "Builds the payout report .xlsx shaped like the existing commission spreadsheet, with a "
    "per-salesperson subtotal. Defaults to invoices that are BOTH approved and paid by the "
    "customer - the two independent gates - since that's what's actually payable right now. "
    "Ignored invoices are always excluded from totals but listed on a separate sheet for audit."
)

invoices = st.session_state["invoices"]
line_items = st.session_state["line_items"]

salespeople = sorted(invoices["salesperson"].unique().tolist())
salesperson = st.selectbox("Salesperson", options=["All"] + salespeople)

c1, c2 = st.columns(2)
with c1:
    require_approved = st.checkbox("Require commission approved", value=True)
with c2:
    require_paid = st.checkbox("Require paid by customer", value=True)

d1, d2 = st.columns(2)
with d1:
    date_from = st.text_input("From date (YYYY-MM-DD, optional)")
with d2:
    date_to = st.text_input("To date (YYYY-MM-DD, optional)")

if not require_approved or not require_paid:
    st.warning(
        "This will include invoices that aren't fully payable yet - use this to preview amounts, "
        "not as the actual payout run.",
        icon="⚠️",
    )

xlsx_bytes = report.build_report(
    invoices, line_items,
    require_approved=require_approved,
    require_paid=require_paid,
    salesperson=salesperson,
    date_from=date_from or None,
    date_to=date_to or None,
)

st.download_button(
    "Download commission report (.xlsx)",
    data=xlsx_bytes,
    file_name="commission_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.info(
    f"Ignored invoices excluded from this export: {int(invoices['ignored'].sum())} "
    "(see the 'Ignored (excluded)' sheet in the downloaded file for the audit list).",
    icon="ℹ️",
)
