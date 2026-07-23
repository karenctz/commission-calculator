# Commission app — rough mock-up, want your eyes on it

Hey — put together a click-through mock-up of the commission tool idea.
Nothing real in it, all made-up numbers, but I want your take on the flow
before I actually build it for real.

Link: *(paste the Streamlit URL here once deployed)*

Quick context in case it's not obvious: right now commission means copying
numbers off invoices and POs by hand, redoing the margin math, and me
chasing you to confirm what's actually been paid before payout. This is
meant to fix that — auto-match invoices to their POs, do the margin/
commission math automatically, and give you one place to approve everything
across all the salespeople, not just me. One thing I really wanted from the
start: a salesperson should never see anyone else's numbers. You'll see
everyone's, obviously.

## How to poke around it

Open the link, go to **Settings** first — there's a role switch, start on
**Finance**. Then work through the Finance tabs top to bottom:

- Import BC Invoices → Import PO List → Auto-Match & Extract (the first
  pass, checking everything against what's on file)
- Export for Salesperson — this is how a salesperson's file actually gets
  sent to them, try picking each name and see what they'd get
- Import Salesperson Updates
- Finance Approval — this is the one that matters most, try approving an
  invoice and also try kicking one back with a note
- Export Payout Report — the actual output you'd use to run payout

Then flip back to Settings, switch role to Salesperson, try both Karen and
John, and open My Invoices — you'll notice you only ever see that person's
stuff, nothing from the other one leaks through.

## What I actually want to know

- Does Finance Approval feel right, or is a step missing / in the wrong order?
- Is "kick back with a note" clear, or would you rather handle corrections differently?
- Approved and paid are two separate things in here — does that match how you actually think about it, or should it just be one?
- Anything missing from the payout report that you'd actually need for a real run?
- Anything that just feels off or confusing, even if you can't say why.

Don't hold back — this is the cheap stage to tell me it's wrong.
