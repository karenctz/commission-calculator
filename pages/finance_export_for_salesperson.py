import streamlit as st

import commission
import exchange
import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Export for Salesperson", layout="wide")
ensure_state()
require_finance()

st.title("Export for Salesperson")
st.caption(
    "Produces a file containing ONLY the picked salesperson's rows - send it to them manually "
    "(email/Teams/however). This deliberate, one-person-at-a-time export is the actual privacy "
    "boundary: nothing automatically syncs the full dataset to anyone."
)

invoices = st.session_state["invoices"]
line_items = st.session_state["line_items"]

salesperson = st.selectbox("Which salesperson?", options=mock_data.SALESPEOPLE)

their_invoices = invoices[invoices["salesperson"] == salesperson]
st.markdown(f"**Preview - what {salesperson} will receive**")
st.dataframe(
    their_invoices[["invoice_no", "customer", "invoice_date", "sales_status", "correction_note"]],
    use_container_width=True, hide_index=True,
)

not_reviewed = (their_invoices["sales_status"] == "Not yet reviewed").sum()
needs_correction = (their_invoices["sales_status"] == "Needs correction").sum()
m1, m2, m3 = st.columns(3)
m1.metric("Total invoices", len(their_invoices))
m2.metric("Not yet reviewed", int(not_reviewed))
m3.metric("Needs correction", int(needs_correction))

xlsx_bytes = exchange.build_export(invoices, line_items, salesperson)
st.download_button(
    f"Download exchange file for {salesperson}",
    data=xlsx_bytes,
    file_name=f"{salesperson.replace(' ', '_')}_commission_review.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.info(
    "Once downloaded: send this file to " + salesperson + " yourself. They'll import it on "
    "**My Invoices**, work through it, and export their own updates back to you.",
    icon="✉️",
)
