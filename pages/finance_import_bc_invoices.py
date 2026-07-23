import pandas as pd
import streamlit as st

import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import BC Invoices", layout="wide")
ensure_state()
require_finance()

st.title("Import BC Invoices")
st.caption(
    "This is the source of truth for which invoices exist - the folder scan later just finds "
    "the matching PDF for each row here, it doesn't decide what counts as an invoice."
)

uploaded = st.file_uploader(
    "Business Central posted-invoices export (.xlsx/.csv)",
    type=["xlsx", "csv"],
    key="bc_upload",
)
use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

if uploaded or use_sample:
    raw, mapping = mock_data.bc_import_preview()
    st.session_state["bc_imported"] = True

    st.subheader("1. Detected column mapping")
    st.caption("Confirm or correct - BC export column names vary by company configuration.")
    map_cols = st.columns(len(mapping))
    target_fields = ["invoice_no", "invoice_date", "customer", "salesperson", "amount"]
    for col, (raw_col, guessed_field) in zip(map_cols, mapping.items()):
        with col:
            st.selectbox(
                f"`{raw_col}` maps to",
                options=target_fields,
                index=target_fields.index(guessed_field),
                key=f"bc_map_{raw_col}",
            )

    st.subheader("2. Raw file preview")
    st.dataframe(raw, use_container_width=True, hide_index=True)

    st.subheader("3. Working invoice list (after mapping)")
    mapped = raw.rename(columns=mapping)
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.success(f"{len(mapped)} invoices imported. Go to **Auto-Match & Extract** next.")
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview.")
