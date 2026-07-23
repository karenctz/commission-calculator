import pandas as pd
import streamlit as st

import commission
import mock_data
from state import current_salesperson, ensure_state, require_salesperson

st.set_page_config(page_title="My Invoices", layout="wide")
ensure_state()
require_salesperson()

me = current_salesperson()
st.title("My Invoices")
st.caption(f"Signed in as **{me}**.")

session_key = f"my_invoices_{me}"
lines_key = f"my_line_items_{me}"

if session_key not in st.session_state:
    st.warning("Nothing imported yet - go to **Import Finance Report** first.", icon="📥")
    st.stop()

invoices = st.session_state[session_key]
line_items = st.session_state[lines_key]

statuses = {no: commission.invoice_status(inv) for no, inv in invoices.iterrows()}
needing_attention = [no for no, inv in invoices.iterrows() if inv["sales_status"] in ("Not yet reviewed", "Needs correction") and not inv["ignored"]]

s1, s2, s3 = st.columns(3)
s1.metric("Your invoices", len(invoices))
s2.metric("Need your attention", len(needing_attention))
s3.metric("Ready for finance", int((invoices["sales_status"] == "Ready for finance").sum()))

st.divider()

eligible = [
    no for no, inv in invoices.iterrows()
    if not inv["ignored"] and inv["sales_status"] != "Ready for finance"
]
if eligible:
    st.subheader("Mark multiple as ready")
    st.caption("Tick the invoices below, or select all, then mark them ready together.")
    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button(f"☑️ Select all {len(eligible)}"):
            for no in eligible:
                st.session_state[f"bulk_ready_{me}_{no}"] = True
            st.rerun()
    with b2:
        if st.button("☐ Clear selection"):
            for no in eligible:
                st.session_state[f"bulk_ready_{me}_{no}"] = False
            st.rerun()

    selected = [no for no in eligible if st.session_state.get(f"bulk_ready_{me}_{no}", False)]
    if st.button(f"Mark selected ready for finance ({len(selected)})", disabled=not selected, type="primary"):
        for no in selected:
            invoices.loc[no, "sales_status"] = "Ready for finance"
            invoices.loc[no, "correction_note"] = ""
            st.session_state[f"bulk_ready_{me}_{no}"] = False
        st.session_state[session_key] = invoices
        st.success(f"Marked {len(selected)} invoice(s) ready for finance.")
        st.rerun()
    st.divider()

order = {"Needs correction": 0, "Not yet reviewed": 1, "Ready for finance": 2}
sort_rank = invoices["sales_status"].map(lambda s: order.get(s, 3))
sorted_invoices = invoices.loc[sort_rank.sort_values().index]

for invoice_no, inv in sorted_invoices.iterrows():
    status = statuses.get(invoice_no)
    title = f"**{invoice_no}** — {inv['customer']} — {inv['invoice_date']}"
    can_act = not inv["ignored"] and inv["sales_status"] != "Ready for finance"

    chk_col, ready_col, title_col = st.columns([0.05, 0.14, 0.81])
    with chk_col:
        if can_act:
            st.checkbox(
                f"Select {invoice_no} for bulk mark-ready",
                key=f"bulk_ready_{me}_{invoice_no}",
                label_visibility="collapsed",
            )
    with ready_col:
        if can_act:
            if st.button("Mark ready", key=f"ready_{invoice_no}"):
                invoices.loc[invoice_no, "sales_status"] = "Ready for finance"
                invoices.loc[invoice_no, "correction_note"] = ""
                st.session_state[session_key] = invoices
                st.rerun()
    with title_col:
        if inv["ignored"]:
            st.markdown(f":gray[{title}]  🚫 *ignored: {inv['ignore_reason']}*")
        elif inv["sales_status"] == "Needs correction":
            st.markdown(f":red[{title}  — sent back by finance]")
        elif inv["sales_status"] == "Not yet reviewed":
            st.markdown(f":orange[🆕 {title}  — not yet reviewed]")
        else:
            st.markdown(f"✅ {title}  — ready for finance")

    if inv["ignored"]:
        continue

    with st.container(border=True):
        if inv["sales_status"] == "Needs correction":
            st.error(f"**Finance's note:** {inv['correction_note']}", icon="📝")

        if status == "needs_review":
            st.warning(f"Auto-match flagged this one: {inv['notes']}", icon="⚠️")

        lines = line_items[line_items["invoice_no"] == invoice_no].copy()
        lines.insert(0, "review", [
            "⚠️ " + "; ".join(reasons) if (reasons := commission.line_review_flags(r)) else "✅"
            for r in lines.to_dict("records")
        ])

        summary_slot = st.container()

        edited = st.data_editor(
            lines.drop(columns=["invoice_no"]),
            key=f"my_editor_{invoice_no}",
            hide_index=True,
            use_container_width=True,
            column_config={
                "review": st.column_config.TextColumn("⚠ Review", disabled=True, width="small"),
                "cost_type": st.column_config.SelectboxColumn(options=mock_data.COST_TYPES),
                "cost_pct_override": st.column_config.NumberColumn(help="Only used for PS cost types"),
                "commission_pct": st.column_config.NumberColumn(format="%.1f%%"),
                "selling_amount": st.column_config.NumberColumn(disabled=True),
                "cost_unit_price": st.column_config.NumberColumn(help="Editable for Standard-cost lines once you know the real cost"),
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
        st.session_state[lines_key] = pd.concat([other_lines, new_lines], ignore_index=True)

        rollup = commission.invoice_rollup(st.session_state[lines_key], invoice_no)
        with summary_slot:
            m1, m2, m3, m4, _spacer = st.columns([1, 1, 1, 1, 4])
            m1.markdown(f"**Selling**  \n${rollup['selling_total']:,.2f}")
            m2.markdown(f"**Cost**  \n${rollup['cost_total']:,.2f}")
            m3.markdown(f"**Margin**  \n${rollup['margin_total']:,.2f}")
            m4.markdown(f"**Commission**  \n${rollup['commission_total']:,.2f}")

st.divider()
st.info("Once you're done, head to **Export My Updates** to send everything back to Finance.", icon="📤")
