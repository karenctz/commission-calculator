import streamlit as st

import exchange
import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import Salesperson Updates", layout="wide")
ensure_state()
require_finance()

st.title("Import Salesperson Updates")
st.caption(
    "Upload the file a salesperson sent back after reviewing their flagged items - this merges "
    "their edits into the master by invoice number. Nothing here overwrites blindly: any row "
    "that looks stale (e.g. re-processed by Auto-Match since it was exported) is flagged instead "
    "of silently replaced."
)

uploaded = st.file_uploader("Salesperson's returned exchange file (.xlsx)", type=["xlsx"], key="salesperson_update_upload")
use_sample = st.selectbox(
    "Or simulate a returned file from",
    options=["(none)"] + mock_data.SALESPEOPLE,
    help="Prototype shortcut - re-exports that salesperson's current rows unchanged, so you can see the merge flow",
)

updated_invoices = updated_line_items = None
if uploaded:
    updated_invoices, updated_line_items = exchange.read_export(uploaded.read())
elif use_sample != "(none)":
    master_inv = st.session_state["invoices"]
    master_lines = st.session_state["line_items"]
    xlsx_bytes = exchange.build_export(master_inv, master_lines, use_sample)
    updated_invoices, updated_line_items = exchange.read_export(xlsx_bytes)

if updated_invoices is not None:
    st.subheader("Preview of the returned file")
    st.dataframe(
        updated_invoices[["invoice_no", "customer", "sales_status", "correction_note"]],
        use_container_width=True, hide_index=True,
    )

    if st.button("Merge into master dataset"):
        merged_inv, merged_lines, warnings = exchange.merge_salesperson_update(
            st.session_state["invoices"], st.session_state["line_items"],
            updated_invoices, updated_line_items,
        )
        st.session_state["invoices"] = merged_inv
        st.session_state["line_items"] = merged_lines
        if warnings:
            st.warning("Merged, with some notes:\n\n" + "\n".join(f"- {w}" for w in warnings), icon="⚠️")
        else:
            st.success("Merged cleanly - these invoices are now ready for Finance Approval.")
else:
    st.info("Upload a file (or pick a salesperson above) to preview and merge their updates.")
