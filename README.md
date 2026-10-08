# Reconciliation_app

Streamlit app that reconciles a Xero trial balance against a Focus trial balance,
explains mismatches with OpenAI, and can email the report or send a WhatsApp summary.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secrets

Create `.streamlit/secrets.toml` (it is git-ignored) with:

```toml
OPENAI_API_KEY = "..."
EMAIL_SENDER = "..."
EMAIL_PASSWORD = "..."
EMAIL_RECEIVER = "..."
TWILIO_SID = "..."
TWILIO_AUTH_TOKEN = "..."
```

## Input files

- Xero TB CSV: `Account Code`, `Debit`, `Credit` columns
- Focus TB CSV: `GL Code`, `Debit`, `Credit` columns

## Tests

The tests drive the app with Streamlit's `AppTest`, with file uploads, OpenAI,
email and Twilio replaced by fakes (`tests/fakes.py`), so no secrets or network
access are needed.

```bash
pip install -r requirements-dev.txt
pytest
```
