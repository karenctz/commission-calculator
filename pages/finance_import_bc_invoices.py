from datetime import datetime

import pandas as pd
import streamlit as st

import commission
import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import BC Invoices", layout="wide")
ensure_state()
require_finance()

st.title("Import Sales Invoice List")
st.caption(
    "This is the source of truth for which invoices exist - exported straight from Business "
    "Central. It doesn't carry a salesperson column itself; that comes from joining the PO "
    "List's Assigned User ID next. `Closed` drives paid-by-customer automatically on import "
    "(still editable after) - assumes this list and the Commission Worksheet are always pulled "
    "for the same date range, so nothing here should be a genuinely closed invoice missing from "
    "that worksheet."
)

up_col, scan_col = st.columns(2)
with up_col:
    st.subheader("1. Upload the invoice list")
    uploaded = st.file_uploader(
        "Sales invoice list export (.xlsx/.csv)",
        type=["xlsx", "csv"],
        key="bc_upload",
    )
    use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

with scan_col:
    st.subheader("2. Scan folder for invoice PDFs (sanity check)")
    st.caption(
        "Links each invoice to its PDF as a reference to open and double-check - doesn't drive "
        "cost, that already comes from the Commission Worksheet."
    )
    scan_label = "🔍 Scan folder now" if not st.session_state.get("invoice_folder_scanned") else "🔄 Rescan folder"
    if st.button(scan_label, type="primary", key="scan_invoice_pdfs"):
        st.session_state["invoice_folder_scanned"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["invoice_folder_scan_count"] = st.session_state.get("invoice_folder_scan_count", 0) + 1
    last = st.session_state.get("invoice_folder_scanned")
    if last:
        st.success(f"Last scanned {last} - {len(mock_data.INVOICE_FILES)} invoice PDF(s) found (scan #{st.session_state['invoice_folder_scan_count']}).")
    else:
        st.warning("Folder hasn't been scanned yet this session.", icon="📁")

if uploaded or use_sample:
    st.session_state["bc_imported"] = True
    st.session_state["bc_raw"], st.session_state["bc_mapping"] = mock_data.bc_import_preview()

if st.session_state.get("invoice_folder_scanned"):
    invoices = st.session_state["invoices"]
    scan_df = invoices[["customer", "invoice_pdf_path", "match_confidence"]].reset_index()
    scan_df["match_confidence"] = scan_df["match_confidence"].apply(commission.confidence_badge)
    st.caption("Confirm or override the auto-matched PDF per invoice.")
    edited_scan = st.data_editor(
        scan_df,
        key="invoice_pdf_editor",
        hide_index=True,
        use_container_width=True,
        column_config={
            "invoice_no": st.column_config.TextColumn("Invoice", disabled=True),
            "customer": st.column_config.TextColumn(disabled=True),
            "invoice_pdf_path": st.column_config.SelectboxColumn("Linked invoice PDF", options=mock_data.INVOICE_FILES),
            "match_confidence": st.column_config.TextColumn("Confidence", disabled=True),
        },
    )
    for _, row in edited_scan.iterrows():
        invoices.loc[row["invoice_no"], "invoice_pdf_path"] = row["invoice_pdf_path"]
    st.session_state["invoices"] = invoices

st.divider()

if st.session_state.get("bc_imported"):
    raw, mapping = st.session_state["bc_raw"], st.session_state["bc_mapping"]

    st.subheader("3. Detected column mapping")
    st.caption("Confirm or correct - real BC export column names vary by company configuration.")
    map_cols = st.columns(len(mapping))
    target_fields = [
        "invoice_no", "order_no", "invoice_date", "customer_no", "customer",
        "external_doc_no", "amount", "amount_incl_gst", "closed",
    ]
    for col, (raw_col, guessed_field) in zip(map_cols, mapping.items()):
        with col:
            st.selectbox(
                f"`{raw_col}` maps to",
                options=target_fields,
                index=target_fields.index(guessed_field),
                key=f"bc_map_{raw_col}",
            )

    st.subheader("4. Raw file preview")
    st.dataframe(raw, use_container_width=True, hide_index=True)

    st.subheader("5. Working invoice list (after mapping)")
    mapped = raw.rename(columns=mapping)
    mapped["paid_by_customer"] = mapped["closed"] == "Yes"
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.success(
        f"{len(mapped)} invoices imported ({int(mapped['paid_by_customer'].sum())} marked "
        "paid-by-customer from Closed=Yes). Go to **Import PO List** next for salesperson."
    )
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview.")
