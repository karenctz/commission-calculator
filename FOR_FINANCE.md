# Commission Calculator — Prototype for Your Feedback

## What this is for

Right now, commission is tracked in a manual spreadsheet — copying numbers
off invoices and POs by hand, recalculating margins, and chasing confirmation
on which invoices have actually been paid before payout. We're building a
small app to handle this instead: it'll auto-match invoices to their supplier
POs, calculate margin and commission automatically, and give you a clear
queue of what needs your approval — across every salesperson, not just one.

**A key design goal:** each salesperson should only ever see their own
commission, never anyone else's. You'll see everything, across all
salespeople.

## What you're looking at

This is a **click-through mock-up** — every number on it is fake/sample
data, nothing is connected to real invoices yet. Nothing you do in it saves
anywhere permanent or affects real records. The point is to get your
reaction to the **workflow and screens** before we build the real thing
underneath — much cheaper to change now than after it's wired up to actual
data.

**Link:** *(paste the Streamlit URL here once deployed)*

## How to try it

1. Open the link. On the **Settings** page, you'll see a role switch —
   start as **Finance** (that's the default).
2. Click through Finance's side of the flow, in order:
   - **Import BC Invoices** → **Import PO List** → **Auto-Match & Extract**
     (this is the first-pass check across everyone)
   - **Export for Salesperson** (this is how a salesperson's file gets sent
     to them — pick either salesperson to see what they'd receive)
   - **Finance Approval** (the main one to react to — try approving an
     invoice, and try "kick back with a note" on another one)
   - **Export** (the final payout report — try toggling the salesperson
     filter and the approved/paid checkboxes)
3. Then go back to **Settings**, switch role to **Salesperson**, pick a name
   (try both Karen and John), and open **My Invoices** to see what a
   salesperson would see — notice it's a completely different set of
   invoices for each one, and nothing overlaps.

## What feedback would help most

- Does the **Finance Approval** flow match how you'd actually want to
  review and sign off commission — anything missing, or in the wrong order?
- Is the **"kick back with a note"** flow clear, or would you want to
  handle corrections differently?
- Does having **"commission approved"** and **"paid by customer"** as two
  separate things make sense, or would you rather they be combined?
- Anything on the final **Export** report that doesn't match what you'd
  actually need for a payout run (columns, groupings, totals)?
- Anything confusing, missing, or that just feels like the wrong screen for
  the job.

No need to be gentle — this is the cheap stage to say "actually, this
should work differently."
