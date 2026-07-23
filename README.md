# Commission Calculator — Phase 0 Prototype

Clickable UI prototype using **mock data only** — nothing is read from or
written to disk. This exists purely to get sign-off on the screens and
workflow before building the real PDF parsing, folder scanning, BC/PO
import, and matching logic underneath.

## Running it

```
pip install -r requirements.txt
streamlit run app.py
```

## What's mocked vs. what's real

- Real numbers: taken from `PO-S26070005-KY_R2 - Elush.pdf`,
  `INV-S260392 - ESAB.pdf`, and several historical rows from
  `Karen - Commission - Payment on 26 Jul 26.xlsx` (see `mock_data.py`).
- The "TechNova" invoice is synthesized (clearly marked in its `notes`
  field) to demonstrate a folder-matched supplier PO with multiple cost
  line items, since no real customer invoice against the Elush PO exists.
- File uploads on the Import pages accept a real file but always show the
  same canned preview/mapping regardless of what you upload — the point is
  to react to the *shape* of the column-mapping UI, not real parsing yet.
- "Open PDF" buttons on Commission Records are inert — real file linking
  comes with `file_store.py`/`folder_index.py` in the next phase.

## Next steps after sign-off

See the approved plan for the full phase breakdown (Phase 1 onward): real
`extractor.py`/`matcher.py` reuse from `po-quote-matcher`, `file_store.py`,
`folder_index.py`, `bc_import.py`, `po_import.py`, `auto_match.py`.
