"""Validate the published snapshot and its exact 5% discount using decimal arithmetic."""

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
    assert data["discount_percent"] == 5
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
        assert nodara["discount_percent"] == 5
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
                assert amount(nodara[field]) == amount(reference[field]) * Decimal("0.95"), (
                    f"{model['id']} {field} must be exactly 5% cheaper"
                )


def validate_images(data):
    assert data['comparison_policy']['quality_equivalence_required_for_direct_comparison'] is True
    assert data['currency']=='USD' and data['billing_unit']=='completed_image'
    assert data['discount_percent']==5 and data['usd_per_ai_credit']=='1'
    assert data['extra_credit_multiplier']=='1'
    assert data['token_accounting']=='not_applicable_no_synthetic_image_tokens'
    ids=set();profiles=set()
    for row in data['models']:
        comparison = row['quality_comparison']
        assert comparison['status'] in {'not_evaluated', 'not_equivalent', 'verified_equivalent'}
        verified = comparison['status'] == 'verified_equivalent'
        assert comparison['direct_comparison_allowed'] is verified
        if verified:
            assert comparison['reference_model']
            settings = comparison['matched_settings']
            for field in data['comparison_policy']['required_matches']:
                assert settings[field]['nodara'] == settings[field]['reference']
                assert settings[field]['nodara'] is not None
            assert settings['width']['nodara'] == row['width']
            assert settings['height']['nodara'] == row['height']
            assert settings['operation']['nodara'] == row['operation']
            evidence = comparison['evaluation']
            for field in data['comparison_policy']['required_evidence']:
                assert evidence[field], 'Direct quality comparison lacks evidence'
            assert evidence['evaluation_results']['passed'] is True
            date.fromisoformat(evidence['evaluation_date'])
        assert row['id'] not in ids;ids.add(row['id'])
        for profile in row['profile_ids']:
            assert profile not in profiles;profiles.add(profile)
        assert all(type(row[k]) is int and row[k]>0 for k in ('width','height','steps'))
        reference=row['common_market_price'];price=row['nodara_price']['usd_per_image']
        assert row['nodara_price']['discount_percent']==5
        if reference is None:
            assert price is None and row['status']=='needs_fixed_preset_reference'
        else:
            assert row['status']=='verified_market_reference'
            assert amount(price)==amount(reference['usd_per_image'])*Decimal('0.95')
            assert urlparse(reference['source_url']).scheme=='https'
            date.fromisoformat(reference['verified_on'])


if __name__ == "__main__":
    snapshot = json.loads((ROOT / "model-pricing.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "model-pricing.schema.json").read_text(encoding="utf-8"))
    validate(snapshot)
    images=json.loads((ROOT / "image-pricing.json").read_text(encoding="utf-8"))
    validate_images(images)
    print("Validated image presets without synthetic token accounting")
    print(f"Validated {len(snapshot['models'])} model/variant rows and exact 5% discounts")
