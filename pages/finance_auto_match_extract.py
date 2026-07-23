from datetime import datetime

import pandas as pd
import streamlit as st

import commission
import mock_data
from state import ensure_state, require_finance

st.set_page_config(page_title="Auto-Match & Extract", layout="wide")
ensure_state()
require_finance()

st.title("Auto-Match & Extract")
st.caption(
    "Finance only. For each imported invoice, across every salesperson at once: the app looks "
    "for its PDF and its supplier PO (from the folder scan or the imported PO list), scores the "
    "match, and lets you confirm or override before extracting/editing line items. This first-pass "
    "check is what produces the flags each salesperson deals with next - it isn't the place to do "
    "their line-by-line commission work for them."
)

invoices = st.session_state["invoices"]
line_items = st.session_state["line_items"]

st.subheader("1. Scan the shared folder")
st.caption(
    "The folder is only scanned when you click this - never automatically or in the background, "
    "and never while a salesperson has the app open."
)
sc1, sc2 = st.columns([1, 3])
with sc1:
    scan_label = "🔍 Scan folder now" if not st.session_state.get("folder_last_scanned") else "🔄 Rescan folder"
    if st.button(scan_label, type="primary"):
        st.session_state["folder_last_scanned"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["folder_scan_count"] = st.session_state.get("folder_scan_count", 0) + 1
with sc2:
    last = st.session_state.get("folder_last_scanned")
    if last:
        found = 13  # mock count - Phase 1+ replaces this with folder_index.py's real scan
        st.success(f"Last scanned {last} - {found} PDF(s) found (scan #{st.session_state['folder_scan_count']}).")
    else:
        st.warning(
            "Folder hasn't been scanned yet this session - click **Scan folder now** to check "
            "for new/updated invoice and PO PDFs before matching.",
            icon="📁",
        )

if not st.session_state.get("folder_last_scanned"):
    st.stop()

st.divider()
st.subheader("2. Confirm matches")
st.caption("Collapsed by default - only invoices needing review open automatically. Expand any others you want to double-check.")

ALL_FILES = [
    "Invoices/INV-S260043.pdf", "Invoices/INV-S260392 - ESAB.pdf",
    "Invoices/INV-S260410 - TechNova.pdf", "Invoices/INV-S260421.pdf",
    "Invoices/CR-S260009.pdf", "Invoices/INV-S260159.pdf",
    "Invoices/INV-S260500 - Straits Marine.pdf", "Invoices/INV-S260510 - Nordic.pdf",
    "Invoices/INV-S260488 - Straits Marine.pdf",
    "Supplier POs/PO-S26070005-KY_R2 - Elush.pdf", "Supplier POs/PO 36002531.pdf",
    "Supplier POs/PO 36002656-A.pdf", "Supplier POs/PO-S26070080-JT.pdf",
    "Quotes/QUO-S260201 - unrelated.pdf",
    "(no PO match)",
]
INVOICE_FILES = ALL_FILES[:9]
PO_FILES = ALL_FILES[9:14]


def confidence_badge(score):
    if score is None or pd.isna(score):
        return "⚪ n/a"
    if score >= 0.85:
        return f"🟢 {score:.0%}"
    if score >= 0.6:
        return f"🟡 {score:.0%}"
    return f"🔴 {score:.0%}"


statuses = {no: commission.invoice_status(inv) for no, inv in invoices.iterrows()}
total_n = len(invoices)
ignored_n = sum(1 for s in statuses.values() if s == "ignored")
needs_review_n = sum(1 for s in statuses.values() if s == "needs_review")
resolved_n = sum(1 for s in statuses.values() if s == "resolved")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Invoices to match", total_n)
s2.metric("✅ Matched", resolved_n)
s3.metric("⚠️ Needs review", needs_review_n)
s4.metric("🚫 Ignored", ignored_n)
if needs_review_n:
    st.warning(
        f"{needs_review_n} invoice(s) need manual confirmation before you rely on their numbers: "
        + ", ".join(no for no, s in statuses.items() if s == "needs_review"),
        icon="⚠️",
    )
st.divider()

active_ids = [no for no in invoices.index if not invoices.loc[no, "ignored"]]

st.subheader("Bulk update commission %")
st.caption(
    "Tick the invoices below (or select all), set a %, and apply it to just those - "
    "doesn't touch anything else. Not a single flat rate forced onto everyone."
)
bb1, bb2 = st.columns([1, 1])
with bb1:
    if st.button(f"☑️ Select all {len(active_ids)}"):
        for no in active_ids:
            st.session_state[f"bulk_comm_{no}"] = True
        st.rerun()
with bb2:
    if st.button("☐ Clear selection"):
        for no in active_ids:
            st.session_state[f"bulk_comm_{no}"] = False
        st.rerun()

selected_for_comm = [no for no in active_ids if st.session_state.get(f"bulk_comm_{no}", False)]
bc1, bc2 = st.columns([1, 1])
with bc1:
    bulk_pct = st.number_input("Commission % to apply", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
with bc2:
    st.write("")
    st.write("")
    apply_bulk = st.button(
        f"Apply {bulk_pct}% to {len(selected_for_comm)} selected invoice(s)",
        disabled=not selected_for_comm,
        type="primary",
    )

if apply_bulk:
    mask = line_items["invoice_no"].isin(selected_for_comm)
    updated_rows = []
    for r in line_items[mask].to_dict("records"):
        r["commission_pct"] = bulk_pct
        updated_rows.append(commission.recompute_line(r))
    new_rows = pd.DataFrame(updated_rows)
    line_items = pd.concat([line_items[~mask], new_rows], ignore_index=True)
    st.session_state["line_items"] = line_items
    for no in selected_for_comm:
        st.session_state[f"bulk_comm_{no}"] = False
    st.success(f"Applied {bulk_pct}% commission to {len(selected_for_comm)} invoice(s).")
    st.rerun()

st.divider()

for invoice_no, inv in invoices.iterrows():
    status = statuses[invoice_no]
    if status == "ignored":
        header = f"🚫 {invoice_no} — {inv['customer']} — _{inv['salesperson']}_ — ignored"
    elif status == "needs_review":
        header = f"⚠️ {invoice_no} — {inv['customer']} — _{inv['salesperson']}_ — needs review"
    else:
        header = f"✅ {invoice_no} — {inv['customer']} — _{inv['salesperson']}_"

    if not inv["ignored"]:
        st.checkbox("Select for bulk commission update", key=f"bulk_comm_{invoice_no}")

    with st.expander(header, expanded=(status == "needs_review")):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            st.selectbox(
                "Matched invoice PDF",
                options=INVOICE_FILES,
                index=INVOICE_FILES.index(inv["invoice_pdf_path"]) if inv["invoice_pdf_path"] in INVOICE_FILES else 0,
                key=f"inv_pdf_{invoice_no}",
            )
        with c2:
            po_options = ["(no PO match)"] + PO_FILES
            current_po = inv["po_pdf_path"] if inv["po_pdf_path"] else "(no PO match)"
            st.selectbox(
                "Matched supplier PO",
                options=po_options,
                index=po_options.index(current_po) if current_po in po_options else 0,
                key=f"po_pdf_{invoice_no}",
            )
        with c3:
            st.metric("Match confidence", confidence_badge(inv["match_confidence"]))

        if pd.notna(inv["match_confidence"]) and inv["match_confidence"] < 0.6:
            st.warning(
                f"Low-confidence match ({inv['notes']}). Confirm the dropdowns above are correct "
                "before extracting line items.",
                icon="⚠️",
            )
        if inv["notes"] and pd.isna(inv["match_confidence"]) and not inv["ignored"]:
            st.info(inv["notes"], icon="ℹ️")
        if inv["ignored"]:
            st.error(f"Ignored: {inv['ignore_reason']}", icon="🚫")
            continue

        lines = line_items[line_items["invoice_no"] == invoice_no].copy()
        lines.insert(0, "review", [
            "⚠️ " + "; ".join(reasons) if (reasons := commission.line_review_flags(r)) else "✅"
            for r in lines.to_dict("records")
        ])
        flagged_before = [r for r in lines.to_dict("records") if r["review"] != "✅"]

        st.markdown("**Extracted / editable line items**")
        if flagged_before:
            st.warning(
                f"{len(flagged_before)} line item(s) need a manual look: "
                + "; ".join(f"\"{r['description'][:40]}\" ({r['review'][2:]})" for r in flagged_before),
                icon="🔎",
            )
        edited = st.data_editor(
            lines.drop(columns=["invoice_no"]),
            key=f"editor_{invoice_no}",
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "review": st.column_config.TextColumn("⚠ Review", disabled=True, width="small"),
                "cost_type": st.column_config.SelectboxColumn(options=mock_data.COST_TYPES),
                "cost_pct_override": st.column_config.NumberColumn(help="Only used for PS cost types; overrides the category default %"),
                "commission_pct": st.column_config.NumberColumn(format="%.1f%%"),
                "selling_amount": st.column_config.NumberColumn(disabled=True),
                "cost_unit_price": st.column_config.NumberColumn(disabled=True),
                "cost_amount": st.column_config.NumberColumn(disabled=True),
                "margin_amount": st.column_config.NumberColumn(disabled=True),
                "margin_pct": st.column_config.NumberColumn(disabled=True, format="%.1f%%"),
                "commission_amount": st.column_config.NumberColumn(disabled=True),
            },
        )

        recomputed = [commission.recompute_line(r) for r in edited.drop(columns=["review"]).to_dict("records")]
        for r in recomputed:
            r["invoice_no"] = invoice_no
        new_lines = pd.DataFrame(recomputed)

        other_lines = line_items[line_items["invoice_no"] != invoice_no]
        st.session_state["line_items"] = pd.concat([other_lines, new_lines], ignore_index=True)

        rollup = commission.invoice_rollup(st.session_state["line_items"], invoice_no)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selling total", f"${rollup['selling_total']:,.2f}")
        m2.metric("Cost total", f"${rollup['cost_total']:,.2f}")
        m3.metric("Margin (GP)", f"${rollup['margin_total']:,.2f}")
        m4.metric("Commission", f"${rollup['commission_total']:,.2f}")

st.divider()
st.success(
    "This is the master dataset - next, go to **Export for Salesperson** to send each "
    "salesperson their own filtered file so they can review and fix their flagged items."
)
