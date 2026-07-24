from datetime import datetime

import streamlit as st

import commission
import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import PO List", layout="wide")
ensure_state()
require_finance()

st.title("Import PO List")
st.caption(
    "One row per supplier PO. `Sales Order No.` joins back to the Sales Invoice List's "
    "`Order No.` - this join is also **where salesperson-per-invoice actually comes from** "
    "(via `Assigned User ID`), since the invoice list itself carries no salesperson column. "
    "The PO's own PDF is still linked here purely as a sanity-check reference, not as the cost "
    "source - real cost comes from the Sales Commission Worksheet."
)

up_col, scan_col = st.columns(2)
with up_col:
    st.subheader("1. Upload the PO list")
    uploaded = st.file_uploader(
        "PO list export (.xlsx/.csv)",
        type=["xlsx", "csv"],
        key="po_upload",
    )
    use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

with scan_col:
    st.subheader("2. Scan folder for supplier PO PDFs (sanity check)")
    st.caption(
        "Links each invoice to its supplier PO's PDF as a reference to open and double-check - "
        "doesn't drive cost. Professional-service invoices have no PO by design, so those stay "
        "unmatched."
    )
    scan_label = "🔍 Scan folder now" if not st.session_state.get("po_folder_scanned") else "🔄 Rescan folder"
    if st.button(scan_label, type="primary", key="scan_po_pdfs"):
        st.session_state["po_folder_scanned"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["po_folder_scan_count"] = st.session_state.get("po_folder_scan_count", 0) + 1
    last = st.session_state.get("po_folder_scanned")
    if last:
        st.success(f"Last scanned {last} - {len(mock_data.PO_FILES)} supplier PO PDF(s) found (scan #{st.session_state['po_folder_scan_count']}).")
    else:
        st.warning("Folder hasn't been scanned yet this session.", icon="📁")

if uploaded or use_sample:
    st.session_state["po_list_imported"] = True
    st.session_state["po_raw"], st.session_state["po_mapping"] = mock_data.po_list_preview()

if st.session_state.get("po_folder_scanned"):
    invoices = st.session_state["invoices"]
    scan_df = invoices[["customer", "po_pdf_path", "match_confidence"]].reset_index()
    scan_df["po_pdf_path"] = scan_df["po_pdf_path"].replace("", "(no PO match)")
    scan_df["match_confidence"] = scan_df["match_confidence"].apply(commission.confidence_badge)
    st.caption("Confirm or override the auto-matched supplier PO PDF per invoice.")
    po_options = ["(no PO match)"] + mock_data.PO_FILES
    edited_scan = st.data_editor(
        scan_df,
        key="po_pdf_editor",
        hide_index=True,
        use_container_width=True,
        column_config={
            "invoice_no": st.column_config.TextColumn("Invoice", disabled=True),
            "customer": st.column_config.TextColumn(disabled=True),
            "po_pdf_path": st.column_config.SelectboxColumn("Linked supplier PO PDF", options=po_options),
            "match_confidence": st.column_config.TextColumn("Confidence", disabled=True),
        },
    )
    for _, row in edited_scan.iterrows():
        linked = "" if row["po_pdf_path"] == "(no PO match)" else row["po_pdf_path"]
        invoices.loc[row["invoice_no"], "po_pdf_path"] = linked
    st.session_state["invoices"] = invoices

st.divider()

if st.session_state.get("po_list_imported"):
    raw, mapping = st.session_state["po_raw"], st.session_state["po_mapping"]

    st.subheader("3. Detected column mapping")
    st.caption("Same flexible mapping approach as the invoice list import - confirm or correct.")
    target_fields = [
        "po_no", "your_reference", "vendor_no", "sales_order_no", "vendor_name",
        "assigned_user_id", "po_date", "amount", "amount_incl_gst",
    ]
    map_cols = st.columns(len(mapping))
    for col, (raw_col, guessed_field) in zip(map_cols, mapping.items()):
        with col:
            st.selectbox(
                f"`{raw_col}` maps to",
                options=target_fields,
                index=target_fields.index(guessed_field),
                key=f"po_map_{raw_col}",
            )

    st.subheader("4. Raw file preview")
    st.dataframe(raw, use_container_width=True, hide_index=True)

    st.subheader("5. Working PO list (after mapping)")
    mapped = raw.rename(columns=mapping)
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.success(
        f"{len(mapped)} PO(s) imported. Joining `sales_order_no` to each invoice's `order_no` "
        "assigns its salesperson (via `assigned_user_id`). Go to **Auto-Match & Extract** next "
        "to review each invoice's worksheet-sourced line items."
    )
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview.")
