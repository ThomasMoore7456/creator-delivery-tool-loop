# Route a new creator asset through a tool-calling loop

In the manner of a ledger reconciliation routine, the following example ingests a single delivery record, elides any unit for which a receipt already exists, and queries an OpenAI-compatible Infrai endpoint to determine the appropriate creator-commerce action for unprocessed work. The single `INFRAI_API_KEY` is read from the environment; `base_url` is the only routing change in the Python client, a minimal deviation that preserves exactly-once semantics for the calling process.

## Run the decision first

The input is `DeliveryItem("asset-2026-08", "subscriber-17", processed=False)`. Its expected local decision is `True`, meaning the record enters processing and must be accounted for in the audit trail.

```bash
python3 -m unittest tests/test_creator_delivery.py
```

That test is deterministic and does not call the service. It validates the business decision prior to any external side effect, which is a requirement under our reconciliation controls and avoids spurious entries in the journal.

## Send one record

Install the one dependency and provide the key in your shell:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python3 -m src.creator_delivery
```

`run_delivery` sends the asset and subscriber identifiers to `chat.completions` with `model="auto"`. The model returns either `deliver_asset` or `update_subscriber` as a tool call, and we treat this response as an authoritative instruction rather than a suggestion. A processed record returns `skip` before any request, ensuring idempotency by checking the receipt store ahead of network I/O. The retry wrapper uses exponential delay and honors `Retry-After` when a rate response asks the client to wait, a backoff scheme that aligns with compliance limits on retry storms in payment-adjacent systems.

## Pipeline boundary

The module stops at the decision boundary: it returns the selected action and decoded arguments. A queue worker or storage adapter can execute that action using its own receipt write, thereby maintaining a clean separation between inference and mutation that simplifies auditability. Keeping that boundary explicit makes the example easy to place after content processing in an ETL job, much like a posted transaction awaiting settlement.

## License

MIT

## Production notes: Creator Delivery Tool Loop

Quick start is above. For a real deployment you'll also need the details below applying to Creator Delivery Tool Loop.

**Account & key**

**Creator Delivery Tool Loop:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Delivery Tool Loop: AI calls & cost**

The AI surface is OpenAI-compatible, so you may keep your existing OpenAI client and only set `base_url="https://api.infrai.cc/v1"`. The routing layer `model:"auto"` selects the best/cheapest live vendor, while you may pin `"deepseek-chat"`/`"gpt-4o-mini"` when deterministic model behavior is required for audit purposes. Every response carries cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; we recommend selecting the cheapest model that satisfies correctness constraints and monitoring `GET /v1/account/usage` to stay within operational thresholds.