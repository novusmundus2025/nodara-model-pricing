"""Validate the published snapshot and its exact 10% discount using decimal arithmetic."""

import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRICE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")


def amount(value):
    assert isinstance(value, str) and PRICE.fullmatch(value), "Invalid decimal price"
    result = Decimal(value)
    assert result.is_finite() and result > 0, "Missing prices must be null, not zero"
    return result


def validate(data):
    assert data["schema_version"] == "1.0.0"
    assert data["currency"] == "USD" and data["token_unit"] == 1_000_000
    assert data["discount_percent"] == 10
    assert data["nodara_price_status"] == "reference_only_not_live_billing"
    date.fromisoformat(data["verified_on"])
    assert datetime.fromisoformat(data["generated_at"]).tzinfo is not None
    ids = set()
    assert data["models"], "Empty model list"
    for model in data["models"]:
        assert model["id"] not in ids, "Duplicate model ID"
        ids.add(model["id"])
        assert model["catalog_model_ids"] and model["name"]
        reference, nodara = model["common_market_price"], model["nodara_price"]
        assert nodara["discount_percent"] == 10
        for quote in model["market_quotes"]:
            assert quote["provider"] and quote["via"] in {"direct", "openrouter"}
            source = urlparse(quote["source_url"])
            assert source.scheme == "https" and source.netloc and not source.username
            date.fromisoformat(quote["verified_on"])
            for field in ("input", "output"):
                amount(quote[field])
        if reference is None:
            assert nodara["input"] is None and nodara["output"] is None
            assert nodara["status"] == "needs_market_reference"
        else:
            assert reference in model["market_quotes"], "Benchmark lacks provenance"
            assert nodara["status"] == "reference_only_not_live_billing"
            for field in ("input", "output"):
                assert amount(nodara[field]) == amount(reference[field]) * Decimal("0.90"), (
                    f"{model['id']} {field} must be exactly 10% cheaper"
                )


if __name__ == "__main__":
    snapshot = json.loads((ROOT / "model-pricing.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "model-pricing.schema.json").read_text(encoding="utf-8"))
    validate(snapshot)
    print(f"Validated {len(snapshot['models'])} model/variant rows and exact 10% discounts")
