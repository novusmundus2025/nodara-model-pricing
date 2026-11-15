# Nodara model pricing JSON

JSON endpoint: https://novusmundus2025.github.io/nodara-model-pricing/model-pricing.json

Schema: https://novusmundus2025.github.io/nodara-model-pricing/model-pricing.schema.json

Prices are USD per **1,000,000 tokens**. `input` and `output` are decimal strings;
use decimal arithmetic. `nodara_price` is exactly 90% of `common_market_price`
for both input and output, without whole-cent rounding.

`common_market_price` means a selected, cited provider benchmark. It is **not a
market-wide average or a guaranteed minimum**. Each reference names its provider,
route, precision, source URL and verification date. Additional OpenRouter routes
are retained in `market_quotes`. Comparisons can differ from contributor
quantization and serving conditions.

The snapshot contains 12 model/variant rows, including Nemotron 3.5 Super VL
NVFP4 and BF16. SmolLM2 135M has null prices because no verified reference was
found. Null does not mean free. Provider request minimums are recorded where
known; cached-input discounts, taxes and credit-purchase fees are excluded.

These are published reference prices, **not connected to live Nodara billing**.
They do not change contributor rewards or
enable models that are pending runtime qualification. No model weights,
credentials, private application code or customer data are included.

## Example

```json
{
  "id": "nemotron-3.5-super-vl-120b-a12b-nvfp4",
  "common_market_price": {"input": "0.06", "output": "0.35"},
  "nodara_price": {"input": "0.054", "output": "0.315", "discount_percent": 10}
}
```

This example omits provenance and other fields; the endpoint contains complete
records. All example prices above are USD per million tokens.

## Updating

Update the verified provider quotes and their dates, then recalculate each
Nodara price with decimal arithmetic: `market_price * Decimal("0.90")`.
Run `python scripts/validate_pricing.py` before committing. The publishing
workflow validates again and deploys only the JSON, schema and entry page.
This is a dated snapshot; rates are not refreshed automatically.

## AI credit formula

AI credits consumed are the discounted input cost plus discounted output cost:

```text
(input_tokens * nodara_price.input + output_tokens * nodara_price.output) / 1,000,000
```

The rates already include the 10% discount; do not apply it again. There is no
additional credit multiplier. For example, Nemotron NVFP4 with 1M input and 1M
output consumes 0.054 + 0.315 = 0.369 AI credits. These credits measure
USD-equivalent model usage; this formula does not activate payments or billing.
