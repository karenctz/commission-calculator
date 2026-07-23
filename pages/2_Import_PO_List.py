import streamlit as st

import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import PO List", layout="wide")
ensure_state()
require_finance()

st.title("Import PO List (optional)")
st.caption(
    "Supplements folder-matched supplier POs - useful when a PO's PDF isn't in the shared folder "
    "but you have a PO export with the numbers. Either source can supply an invoice's cost side."
)

uploaded = st.file_uploader(
    "PO list export (.xlsx/.csv)",
    type=["xlsx", "csv"],
    key="po_upload",
)
use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

if uploaded or use_sample:
    raw, mapping = mock_data.po_list_preview()
    st.session_state["po_list_imported"] = True

    st.subheader("1. Detected column mapping")
    st.caption("Same flexible mapping approach as the BC import - confirm or correct.")
    target_fields = ["po_no", "po_date", "supplier", "amount", "linked_invoice_no"]
    map_cols = st.columns(len(mapping))
    for col, (raw_col, guessed_field) in zip(map_cols, mapping.items()):
        with col:
            st.selectbox(
                f"`{raw_col}` maps to",
                options=target_fields,
                index=target_fields.index(guessed_field),
                key=f"po_map_{raw_col}",
            )

    st.subheader("2. Raw file preview")
    st.dataframe(raw, use_container_width=True, hide_index=True)

    st.subheader("3. Working PO list (after mapping)")
    mapped = raw.rename(columns=mapping)
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.success(f"{len(mapped)} POs imported. These become candidates in Auto-Match & Extract, alongside folder-scanned PO PDFs.")
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview. Skip this page entirely if you don't have a separate PO list.")
