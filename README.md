# Claude Invoice Extraction: PDF and photo to JSON

Turn invoices into clean JSON with Claude. Point the script at a PDF or a phone photo and get back vendor, customer, invoice number, dates, currency, subtotal, tax, total and every line item, validated against a Pydantic schema.

One Python file, built with the official **Anthropic Python SDK** and **structured outputs** (`messages.parse` with a Pydantic model), so the answer always matches the schema. No OCR library, no templates per vendor.

> Need a team tool instead of a script, with a review screen, total checks, Vietnamese VAT invoices, CSV/Excel export, webhooks and a one-command AWS deploy? See **[DocSift: Document Extraction Kit](https://kimhoang36.gumroad.com/l/invoice-extraction-kit?utm_source=github&utm_medium=readme&utm_campaign=claude-invoice-extraction)**.

## Run it

```bash
git clone https://github.com/shipready-ai/claude-invoice-extraction
cd claude-invoice-extraction
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

python extract.py samples/invoice-northwind.pdf
python extract.py invoices/*.pdf receipts/*.jpg --out results.jsonl
```

Output:

```json
{
  "file": "invoice-northwind.pdf",
  "vendor_name": "Northwind Design Studio",
  "customer_name": "Sample Trading Pte Ltd",
  "invoice_number": "NW-2026-0117",
  "invoice_date": "2026-02-12",
  "due_date": "2026-03-14",
  "currency": "USD",
  "subtotal": 2070.0,
  "tax": 186.3,
  "total": 2256.3,
  "line_items": [
    { "description": "Logo design, 3 concepts", "quantity": 1, "unit_price": 1200.0, "amount": 1200.0 },
    { "description": "Brand guidelines (hours)", "quantity": 6, "unit_price": 95.0, "amount": 570.0 },
    { "description": "Business card layout", "quantity": 2, "unit_price": 150.0, "amount": 300.0 }
  ]
}
```

## How it works

1. The file is sent to Claude as a `document` block (PDF) or an `image` block (PNG, JPG, WEBP). Claude reads PDFs page by page, including scanned ones.
2. `client.beta.messages.parse(output_format=Invoice)` turns the `Invoice` Pydantic model into a JSON schema. Claude's reply is constrained to it, then parsed back into an `Invoice` object.
3. The system prompt says **copy, do not guess**: a field that is not printed comes back as `null` instead of an invented value.

Change the fields by editing the `Invoice` class. Add `purchase_order: str | None = None` and Claude starts filling it in.

## Cost

About 1 to 3 US cents per one-page invoice with `claude-opus-5-5` at low effort. Set `CLAUDE_MODEL` to try another model.

## Tests

```bash
pip install pytest
pytest -q      # uses a fake Claude client, no API key needed
```

## Lite version vs the full kit

| | This repo (free) | [DocSift kit](https://kimhoang36.gumroad.com/l/invoice-extraction-kit?utm_source=github&utm_medium=readme&utm_campaign=claude-invoice-extraction) |
|---|---|---|
| PDF and photo to JSON | ✅ | ✅ |
| Document types | Invoice | Invoice, receipt, Vietnamese VAT invoice (hóa đơn GTGT), add your own |
| Checks that totals add up and flags uncertain fields | | ✅ |
| Web app: upload, queue, side-by-side review and edit | | ✅ |
| Export to CSV and Excel, webhook on approve | | ✅ |
| Passwords, cost log and daily spend cap | | ✅ |
| Docker, HTTPS, one-command AWS deploy, backups | | ✅ |

## More starter kits

Production-ready Claude projects with one-command AWS deploys: [all ShipReady AI kits](https://shipready-ai.github.io/?utm_source=github&utm_medium=readme&utm_campaign=claude-invoice-extraction).

## License

MIT. See [LICENSE](LICENSE).
