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
    "Finance only. Line items here already come from the imported Sales Commission Worksheet, "
    "and invoice/supplier-PO PDFs were already linked back in **Import Sales Invoice List** and "
    "**Import PO List** - this page doesn't scan or match anything itself anymore. What it does: "
    "across every salesperson at once, review those linked documents (as a sanity check "
    "alongside the worksheet's own direct BC record link) and review/edit the worksheet-sourced "
    "line items before they go to each salesperson. This first-pass check is what produces the "
    "flags each salesperson deals with next - it isn't the place to do their line-by-line "
    "commission work for them."
)

invoices = st.session_state["invoices"]
line_items = st.session_state["line_items"]

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

salespeople = sorted(invoices["salesperson"].unique().tolist())
filter_sp = st.selectbox("Salesperson", options=["All"] + salespeople)
visible_invoices = invoices if filter_sp == "All" else invoices[invoices["salesperson"] == filter_sp]

active_ids = [no for no in visible_invoices.index if not invoices.loc[no, "ignored"]]

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

if filter_sp != "All":
    st.caption(f"Showing {len(visible_invoices)} invoice(s) for **{filter_sp}**.")

for invoice_no, inv in visible_invoices.iterrows():
    status = statuses[invoice_no]

    lines = line_items[line_items["invoice_no"] == invoice_no].copy()
    lines.insert(0, "review", [
        "⚠️ " + "; ".join(reasons) if (reasons := commission.line_review_flags(r)) else "✅"
        for r in lines.to_dict("records")
    ])
    has_line_issues = status != "ignored" and (lines["review"] != "✅").any()

    if status == "ignored":
        header = f"🚫 {invoice_no} — {inv['customer']} — _{inv['salesperson']}_ — ignored"
    elif status == "needs_review" or has_line_issues:
        header = f"⚠️ {invoice_no} — {inv['customer']} — _{inv['salesperson']}_ — needs review"
    else:
        header = f"✅ {invoice_no} — {inv['customer']} — _{inv['salesperson']}_"

    chk_col, exp_col = st.columns([0.05, 0.95])
    with chk_col:
        st.write("")
        if not inv["ignored"]:
            st.checkbox(
                f"Select {invoice_no} for bulk commission update",
                key=f"bulk_comm_{invoice_no}",
                label_visibility="collapsed",
            )
    with exp_col:
        expander_ctx = st.expander(header, expanded=(status == "needs_review" or has_line_issues))

    with expander_ctx:
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            st.text_input(
                "Invoice PDF (sanity check)",
                value=inv["invoice_pdf_path"] or "(not linked yet)",
                disabled=True,
                key=f"inv_pdf_display_{invoice_no}",
                help="Linked in Import Sales Invoice List's folder scan - reference only, doesn't drive cost.",
            )
        with c2:
            st.text_input(
                "Supplier PO PDF (sanity check)",
                value=inv["po_pdf_path"] or "(no PO match)",
                disabled=True,
                key=f"po_pdf_display_{invoice_no}",
                help="Linked in Import PO List's folder scan. Reference only, and only exists for Standard-cost lines - PS lines have no PO by design.",
            )
        with c3:
            st.metric("Doc-link confidence", commission.confidence_badge(inv["match_confidence"]))

        if pd.notna(inv["match_confidence"]) and inv["match_confidence"] < 0.6:
            st.warning(
                f"Low-confidence document link ({inv['notes']}). Go back to **Import Sales "
                "Invoice List** / **Import PO List** to fix the linked PDF if it's wrong.",
                icon="⚠️",
            )
        if inv["notes"] and pd.isna(inv["match_confidence"]) and not inv["ignored"]:
            st.info(inv["notes"], icon="ℹ️")
        if inv["ignored"]:
            st.error(f"Ignored: {inv['ignore_reason']}", icon="🚫")
            continue

        flagged_before = [r for r in lines.to_dict("records") if r["review"] != "✅"]

        summary_slot = st.container()

        st.markdown("**Line items from the Commission Worksheet (editable)**")
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
                "cost_unit_price": st.column_config.NumberColumn(help="Editable for Standard-cost lines once you know the real cost"),
                "cost_amount": st.column_config.NumberColumn(disabled=True),
                "wht_pct": st.column_config.NumberColumn("WHT %", format="%.0f%%", help="Withholding tax - auto-set for Thailand (5%) / Taiwan (20%) customers, deducted before margin/commission. Verify before approving."),
                "wht_amount": st.column_config.NumberColumn("WHT Amt", disabled=True),
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
        with summary_slot:
            if rollup["wht_total"]:
                m1, m2, m3, m4, m5, _spacer2 = st.columns([1, 1, 1, 1, 1, 3])
                m5.markdown(f"**WHT**  \n${rollup['wht_total']:,.2f}")
            else:
                m1, m2, m3, m4, _spacer2 = st.columns([1, 1, 1, 1, 4])
            m1.markdown(f"**Selling total**  \n${rollup['selling_total']:,.2f}")
            m2.markdown(f"**Cost total**  \n${rollup['cost_total']:,.2f}")
            m3.markdown(f"**Margin (GP)**  \n${rollup['margin_total']:,.2f}")
            m4.markdown(f"**Commission**  \n${rollup['commission_total']:,.2f}")

st.divider()
st.success(
    "This is the master dataset - next, go to **Export for Salesperson** to send each "
    "salesperson their own filtered file so they can review and fix their flagged items."
)
