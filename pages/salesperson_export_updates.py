import streamlit as st

import commission
import exchange
from state import current_salesperson, ensure_state, require_salesperson

st.set_page_config(page_title="Export My Updates", layout="wide")
ensure_state()
require_salesperson()

me = current_salesperson()
st.title("Export My Updates")
st.caption("Once you're done reviewing on My Invoices, download this and send it back to Finance.")

session_key = f"my_invoices_{me}"
lines_key = f"my_line_items_{me}"

if session_key not in st.session_state:
    st.warning("Nothing imported yet - go to **My Invoices** first to import Finance's report.", icon="📥")
    st.stop()

invoices = st.session_state[session_key]
line_items = st.session_state[lines_key]

ready = int((invoices["sales_status"] == "Ready for finance").sum())
remaining = int(len(invoices) - ready - invoices["ignored"].sum())
m1, m2 = st.columns(2)
m1.metric("Ready for finance", ready)
m2.metric("Still need attention", remaining)
if remaining:
    st.warning(
        f"{remaining} invoice(s) aren't marked ready yet - you can still export now (Finance "
        "will just see them as not-yet-ready), or go back to My Invoices to finish them first.",
        icon="⚠️",
    )

out_bytes = exchange.write_workbook(invoices, line_items)
st.download_button(
    "Download my updates (.xlsx)",
    data=out_bytes,
    file_name=f"{me.replace(' ', '_')}_commission_updates.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()
if st.button("Start over (discard imported file)"):
    del st.session_state[session_key]
    del st.session_state[lines_key]
    st.rerun()
