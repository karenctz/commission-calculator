import pandas as pd
import streamlit as st

import commission
import exchange
import mock_data
from state import current_salesperson, ensure_state, require_salesperson

st.set_page_config(page_title="My Invoices", layout="wide")
ensure_state()
require_salesperson()

me = current_salesperson()
st.title("My Invoices")
st.caption(
    f"Signed in as **{me}**. This page only ever works from a file Finance sent you - it never "
    "reads the master dataset, so there's nothing here to leak even by accident."
)

session_key = f"my_invoices_{me}"
lines_key = f"my_line_items_{me}"

if session_key not in st.session_state:
    st.subheader("Import my review file")
    st.write("Load the file Finance sent you (or use the sample below to try this out).")
    uploaded = st.file_uploader("Your exchange file (.xlsx)", type=["xlsx"], key="my_upload")
    use_sample = st.button(
        f"Use a sample file for {me} instead",
        help="Prototype shortcut - simulates having received and opened Finance's export",
    )
    if uploaded:
        inv, lines = exchange.read_export(uploaded.read())
        st.session_state[session_key] = inv
        st.session_state[lines_key] = lines
        st.rerun()
    elif use_sample:
        master_inv = st.session_state["invoices"]
        master_lines = st.session_state["line_items"]
        xlsx_bytes = exchange.build_export(master_inv, master_lines, me)
        inv, lines = exchange.read_export(xlsx_bytes)
        st.session_state[session_key] = inv
        st.session_state[lines_key] = lines
        st.rerun()
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

order = {"Needs correction": 0, "Not yet reviewed": 1, "Ready for finance": 2}
sort_rank = invoices["sales_status"].map(lambda s: order.get(s, 3))
sorted_invoices = invoices.loc[sort_rank.sort_values().index]

for invoice_no, inv in sorted_invoices.iterrows():
    status = statuses.get(invoice_no)
    with st.container(border=True):
        title = f"**{invoice_no}** — {inv['customer']} — {inv['invoice_date']}"
        if inv["ignored"]:
            st.markdown(f":gray[{title}]  🚫 *ignored: {inv['ignore_reason']}*")
            continue
        elif inv["sales_status"] == "Needs correction":
            st.markdown(f":red[🔁 {title}  — sent back by finance]")
            st.error(f"**Finance's note:** {inv['correction_note']}", icon="📝")
        elif inv["sales_status"] == "Not yet reviewed":
            st.markdown(f":orange[🆕 {title}  — not yet reviewed]")
        else:
            st.markdown(f"✅ {title}  — ready for finance")

        if status == "needs_review":
            st.warning(f"Auto-match flagged this one: {inv['notes']}", icon="⚠️")

        lines = line_items[line_items["invoice_no"] == invoice_no].copy()
        lines.insert(0, "review", [
            "⚠️ " + "; ".join(reasons) if (reasons := commission.line_review_flags(r)) else "✅"
            for r in lines.to_dict("records")
        ])

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
        st.session_state[lines_key] = pd.concat([other_lines, new_lines], ignore_index=True)

        rollup = commission.invoice_rollup(st.session_state[lines_key], invoice_no)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Selling", f"${rollup['selling_total']:,.2f}")
        m2.metric("Cost", f"${rollup['cost_total']:,.2f}")
        m3.metric("Margin", f"${rollup['margin_total']:,.2f}")
        m4.metric("Commission", f"${rollup['commission_total']:,.2f}")

        if inv["sales_status"] != "Ready for finance":
            if st.button("Mark ready for finance", key=f"ready_{invoice_no}"):
                invoices.loc[invoice_no, "sales_status"] = "Ready for finance"
                invoices.loc[invoice_no, "correction_note"] = ""
                st.session_state[session_key] = invoices
                st.rerun()

st.divider()
st.subheader("Export my updates")
st.caption("Once you're done, download this and send it back to Finance.")
out_bytes = exchange.write_workbook(st.session_state[session_key], st.session_state[lines_key])
st.download_button(
    "Download my updates (.xlsx)",
    data=out_bytes,
    file_name=f"{me.replace(' ', '_')}_commission_updates.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

if st.button("Start over (discard imported file)"):
    del st.session_state[session_key]
    del st.session_state[lines_key]
    st.rerun()
