import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import extract  # noqa: E402

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "invoice-northwind.pdf"


class FakeClient:
    """Stands in for Anthropic(): records the request and returns a fixed invoice."""

    def __init__(self, stop_reason="end_turn"):
        self.calls = []
        invoice = extract.Invoice(vendor_name="Northwind", customer_name=None, invoice_number="INV-1",
                                  invoice_date="2026-03-01", due_date=None, currency="USD",
                                  subtotal=100, tax=10, total=110)
        parsed = None if stop_reason == "refusal" else invoice
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self._parse))
        self._response = SimpleNamespace(stop_reason=stop_reason, parsed_output=parsed)

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


def test_pdf_becomes_json(capsys):
    client = FakeClient()
    assert extract.main([str(SAMPLE)], client=client) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["total"] == 110 and out["file"] == SAMPLE.name
    block = client.calls[0]["messages"][0]["content"][0]
    assert block["type"] == "document" and block["source"]["media_type"] == "application/pdf"


def test_jsonl_output(tmp_path):
    out = tmp_path / "r.jsonl"
    assert extract.main([str(SAMPLE), str(SAMPLE), "--out", str(out)], client=FakeClient()) == 0
    assert len(out.read_text().splitlines()) == 2


def test_unsupported_file_and_refusal_fail_cleanly(tmp_path):
    txt = tmp_path / "a.txt"
    txt.write_text("hi")
    assert extract.main([str(txt)], client=FakeClient()) == 1
    assert extract.main([str(SAMPLE)], client=FakeClient("refusal")) == 1
