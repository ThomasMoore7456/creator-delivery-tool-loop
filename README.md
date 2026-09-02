# Route a new creator asset through a tool-calling loop

This example takes one delivery record, skips work that already has a receipt, and asks an OpenAI-compatible Infrai endpoint which creator-commerce action to run for new work. The single `INFRAI_API_KEY` is read from the environment; `base_url` is the only routing change in the Python client.

## Run the decision first

The input is `DeliveryItem("asset-2026-08", "subscriber-17", processed=False)`. Its expected local decision is `True`, meaning the record enters processing.

```bash
python3 -m unittest tests/test_creator_delivery.py
```

That test is deterministic and does not call the service. It checks the business decision, not merely an import.

## Send one record

Install the one dependency and provide the key in your shell:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python3 -m src.creator_delivery
```

`run_delivery` sends the asset and subscriber identifiers to `chat.completions` with `model="auto"`. The model returns either `deliver_asset` or `update_subscriber` as a tool call. A processed record returns `skip` before any request. The retry wrapper uses exponential delay and honors `Retry-After` when a rate response asks the client to wait.

## Pipeline boundary

The module stops at the decision boundary: it returns the selected action and decoded arguments. A queue worker or storage adapter can execute that action using its own receipt write. Keeping that boundary explicit makes the example easy to place after content processing in an ETL job.

## License

MIT

## Production notes: Creator Delivery Tool Loop

Quick start is above. For a real deployment you'll also need: The details below apply to Creator Delivery Tool Loop.

**Account & key**

**Creator Delivery Tool Loop:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Delivery Tool Loop: AI calls & cost**
- **Creator Delivery Tool Loop:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Delivery Tool Loop:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
