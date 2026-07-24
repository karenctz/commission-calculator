import streamlit as st

import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Import Commission Worksheet", layout="wide")
ensure_state()
require_finance()

st.title("Import Sales Commission Worksheet")
st.caption(
    "The primary line-item source: real, admin-keyed cost per line, already computed to gross "
    "profit and a 10% commission amount. This is what actually populates each invoice's line "
    "items now - no PDF extraction needed for anything covered here. The direct BC record link "
    "each row carries (and any invoice/PO PDF from the folder scan) stays available purely as a "
    "sanity check, not as the source of the numbers."
)
st.info(
    "A line's cost type still matters: **Standard** lines trust this worksheet's `total cost` "
    "directly (there's a PO/invoice to sanity-check it against). **Professional service** lines "
    "(item code `PS` here) have no PO to check a keyed-in cost against, so those always use the "
    "Infra/HW-PS 30% / Apps-PS 70% rule instead - the worksheet's cost is ignored for them. "
    "Classification is a best-effort default from the item code column and stays editable per "
    "line, same as today.",
    icon="💡",
)

uploaded = st.file_uploader(
    "Sales commission worksheet export (.xlsx/.csv)",
    type=["xlsx", "csv"],
    key="commission_worksheet_upload",
)
use_sample = st.button("Use a sample export instead", help="Prototype shortcut - loads canned mock data")

if uploaded or use_sample:
    st.session_state["commission_worksheet_imported"] = True
    st.session_state["cw_raw"], st.session_state["cw_mapping"] = mock_data.commission_worksheet_preview()

if st.session_state.get("commission_worksheet_imported"):
    raw, mapping = st.session_state["cw_raw"], st.session_state["cw_mapping"]

    st.subheader("1. Detected column mapping")
    st.caption(
        "Confirm or correct. The worksheet's header row is easy to lose when re-saved without "
        "it - always re-upload a version with row 1 intact rather than guessing column order."
    )
    target_fields = [
        "invoice_no", "posting_date", "customer", "item_code", "part_no", "description",
        "qty", "unit_price", "amount", "invoice_remaining_amount", "total_cost",
        "gross_profit", "commission_amount", "sales_person_code", "salesperson", "keyed_in_by",
    ]
    map_cols = st.columns(4)
    for i, (raw_col, guessed_field) in enumerate(mapping.items()):
        with map_cols[i % 4]:
            st.selectbox(
                f"`{raw_col}` maps to",
                options=target_fields,
                index=target_fields.index(guessed_field),
                key=f"cw_map_{raw_col}",
            )

    st.subheader("2. Raw file preview")
    st.dataframe(raw, use_container_width=True, hide_index=True)

    st.subheader("3. Working line-item list (after mapping)")
    mapped = raw.rename(columns=mapping)
    mapped["cost_type_default"] = mapped["item_code"].apply(
        lambda c: "Professional service (choose Infra/HW or Apps)" if c == "PS" else "Standard"
    )
    mapped["wht_pct"] = mapped["customer"].apply(mock_data.wht_rate_for_customer)
    st.dataframe(mapped, use_container_width=True, hide_index=True)
    st.caption(
        "`keyed_in_by` (the admin's own name/login) is shown for reference only - it isn't used "
        "in any commission or salesperson logic. `wht_pct` is auto-detected from the customer "
        "name (Thailand 5%, Taiwan 20%) - this worksheet's own `gross_profit`/`commission_amount` "
        "columns are the raw pre-WHT figures as exported; Auto-Match & Extract recalculates both "
        "net of WHT once imported."
    )

    ps_count = int((mapped["item_code"] == "PS").sum())
    wht_count = int((mapped["wht_pct"] > 0).sum())
    st.success(
        f"{len(mapped)} line item(s) imported across {mapped['invoice_no'].nunique()} invoice(s) "
        f"- {ps_count} flagged as professional service (cost will use the %-rule, not this "
        f"worksheet's total cost); {wht_count} flagged for withholding tax (Thailand/Taiwan) and "
        "will need a manual double-check before approving. Go to **Import Sales Invoice List** "
        "next, which is also where you'll scan the folder for invoice PDFs to link as a sanity check."
    )
else:
    st.info("Upload a file (or click the sample button) to see the mapping and preview.")
