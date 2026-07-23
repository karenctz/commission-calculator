import streamlit as st

import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import PO List", layout="wide")
ensure_state()
require_finance()

st.title("Import PO List (optional)")
st.caption(
    "A record like your e-invoice tracking sheet already links each invoice to its PO/quotation "
    "number - useful for confirming the right PO even when its PDF is hard to auto-match by name. "
    "But this list alone doesn't have cost figures on it: Auto-Match still needs the **actual PO "
    "PDF** (found via the folder scan below, or uploaded by the salesperson if it's missing) to "
    "get the real cost for margin/commission. Both pieces work together, not as alternatives."
)

st.subheader("1. Upload the PO/invoice linkage list")
uploaded = st.file_uploader(
    "PO list or e-invoice tracking export (.xlsx/.csv)",
    type=["xlsx", "csv"],
    key="po_upload",
)
use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

st.subheader("2. Folder to scan for the actual PO PDFs")
st.caption(
    "This is the same shared folder used for invoice PDFs - Auto-Match & Extract's \"Scan folder "
    "now\" button is what actually reads it (see Settings). Listed here too since both pieces feed "
    "the same matching step."
)
st.text_input(
    "Folder to scan for PO PDFs",
    value=st.session_state.get("root_folder", ""),
    placeholder=r"C:\Users\KarenYeung\OneDrive - Cactoz\Commission App",
    help="Not actually scanned from this page in this prototype - go to Auto-Match & Extract to trigger the scan.",
    disabled=True,
)

st.divider()

if uploaded or use_sample:
    raw, mapping = mock_data.po_list_preview()
    st.session_state["po_list_imported"] = True

    st.subheader("3. Detected column mapping")
    st.caption("Same flexible mapping approach as the BC import - confirm or correct.")
    target_fields = ["invoice_no", "invoice_date", "po_ref", "delivered", "scanned", "emailed_date"]
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

    st.subheader("5. Working linkage list (after mapping)")
    mapped = raw.rename(columns=mapping)
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.success(
        f"{len(mapped)} invoice↔PO links imported. Auto-Match & Extract uses these to know which "
        "PO number to look for - it still needs that PO's PDF (from the folder scan) for the "
        "actual cost."
    )
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview. Skip this page entirely if you don't have a separate PO list.")
