"""Extract invoice data from a PDF or a photo into JSON with Claude.

    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    python extract.py samples/invoice-northwind.pdf            # prints JSON
    python extract.py invoices/*.pdf --out results.jsonl        # many files, one JSON line each
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from pydantic import BaseModel, Field

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
MEDIA_TYPES = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

SYSTEM = """You copy details from invoices into fields, exactly as printed.
- Copy, do not guess. If a field is not on the document, use null.
- Numbers are plain numbers with no currency signs or thousands separators.
- Dates are YYYY-MM-DD.
- List every line item in order, including discounts as negative amounts."""


class LineItem(BaseModel):
    description: str
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class Invoice(BaseModel):
    vendor_name: str | None = Field(description="Who issued the invoice")
    customer_name: str | None = Field(description="Who the invoice is billed to")
    invoice_number: str | None = None
    invoice_date: str | None = Field(description="YYYY-MM-DD")
    due_date: str | None = Field(description="YYYY-MM-DD")
    currency: str | None = Field(description="ISO code such as USD, EUR, VND")
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    line_items: list[LineItem] = []


class ExtractionError(RuntimeError):
    pass


def file_block(path: Path) -> dict:
    media_type = MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        raise ExtractionError(f"{path.name}: only PDF, PNG, JPG and WEBP files are supported")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    kind = "document" if media_type == "application/pdf" else "image"
    return {"type": kind, "source": {"type": "base64", "media_type": media_type, "data": data}}


def extract(client: Anthropic, path: Path) -> Invoice:
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": [file_block(path), {"type": "text", "text": "Fill in the invoice fields."}]}],
        output_format=Invoice,
        output_config={"effort": "low"},
        # If the model declines on safety grounds, the API retries on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise ExtractionError(f"{path.name}: Claude declined to read this file")
    if response.parsed_output is None:
        raise ExtractionError(f"{path.name}: the answer was cut off or could not be parsed")
    return response.parsed_output


def main(argv: list[str] | None = None, client: Anthropic | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract invoice fields to JSON with Claude")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, help="write one JSON line per file to this .jsonl file")
    args = parser.parse_args(argv)
    client = client or Anthropic()

    failures = 0
    out = args.out.open("a", encoding="utf-8") if args.out else None
    try:
        for path in args.files:
            try:
                invoice = extract(client, path)
            except ExtractionError as e:
                print(f"error: {e}", file=sys.stderr)
                failures += 1
                continue
            record = {"file": path.name, **invoice.model_dump()}
            if out:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"ok: {path.name}", file=sys.stderr)
            else:
                print(json.dumps(record, ensure_ascii=False, indent=2))
    finally:
        if out:
            out.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
