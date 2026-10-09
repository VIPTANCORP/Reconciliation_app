import os

import pytest
from streamlit.testing.v1 import AppTest

import fakes

HARNESS = os.path.join(os.path.dirname(__file__), "harness_app.py")
SECRETS = ["OPENAI_API_KEY", "EMAIL_SENDER", "EMAIL_PASSWORD", "EMAIL_RECEIVER",
           "TWILIO_SID", "TWILIO_AUTH_TOKEN"]
WHATSAPP_LABEL = "Enter WhatsApp number"
QUESTION_LABEL = "Type your question"


def button(at, label):
    return next(b for b in at.button if b.label == label)


def text_input(at, label):
    return next(t for t in at.text_input if t.label.startswith(label))


@pytest.fixture
def app():
    fakes.reset()
    at = AppTest.from_file(HARNESS, default_timeout=30)
    for key in SECRETS:
        at.secrets[key] = "dummy"
    at.run()
    assert not at.exception
    return at


@pytest.fixture
def reconciled(app):
    button(app, "🧾 Reconcile Now").click().run()
    assert not app.exception
    return app


def test_no_results_before_reconcile(app):
    assert len(app.dataframe) == 0


def test_reconcile_flags_mismatches(reconciled):
    df = reconciled.session_state["reconciled_df"]
    assert dict(zip(df["key"], df["status"])) == {
        "100": "Match", "200": "Mismatch", "300": "Mismatch", "400": "Mismatch",
    }
    # AI explanations are only requested for mismatched rows.
    assert len(fakes.calls["ai"]) == 3
    assert (df["ai_explanation"] != "").sum() == 3


def test_results_survive_other_interactions(reconciled):
    text_input(reconciled, WHATSAPP_LABEL).input("+15550001111").run()
    reconciled.run()

    assert not reconciled.exception
    assert len(reconciled.dataframe) == 1
    # Explanations are generated once, not on every rerun.
    assert len(fakes.calls["ai"]) == 3


def test_email_sends_once_per_click(reconciled):
    button(reconciled, "📧 Email this report").click().run()
    reconciled.run()
    text_input(reconciled, WHATSAPP_LABEL).input("+15550001111").run()

    assert len(fakes.calls["email"]) == 1
    assert "reconciliation_output.xlsx" in fakes.calls["email"][0]["attachments"]
    assert len(reconciled.dataframe) == 1


def test_whatsapp_needs_a_number(reconciled):
    button(reconciled, "📱 Send WhatsApp summary").click().run()

    assert fakes.calls["whatsapp"] == []
    assert [w.value for w in reconciled.warning] == ["Enter a WhatsApp number first."]


def test_whatsapp_sends_once_per_click(reconciled):
    text_input(reconciled, WHATSAPP_LABEL).input("+15550001111").run()
    button(reconciled, "📱 Send WhatsApp summary").click().run()
    reconciled.run()

    assert len(fakes.calls["whatsapp"]) == 1
    message = fakes.calls["whatsapp"][0]
    assert message["to"] == "whatsapp:+15550001111"
    # 200: credit off by 10, 300: debit 50 missing in Focus, 400: debit 10 missing in Xero.
    assert message["body"] == "Reconciliation done. 3 mismatches found. Total difference: 70.00."


def test_each_question_is_asked_once(reconciled):
    text_input(reconciled, QUESTION_LABEL).input("Why does 200 differ?")
    button(reconciled, "Ask").click().run()
    reconciled.run()
    # The form clears on submit, so pressing Ask again sends nothing.
    button(reconciled, "Ask").click().run()
    text_input(reconciled, QUESTION_LABEL).input("And 300?")
    button(reconciled, "Ask").click().run()

    assert len(fakes.calls["ai"]) == 3 + 2
    assert reconciled.session_state["chat_history"] == [
        ("Why does 200 differ?", fakes.AI_ANSWER),
        ("And 300?", fakes.AI_ANSWER),
    ]


def test_new_reconciliation_clears_chat(reconciled):
    text_input(reconciled, QUESTION_LABEL).input("Why does 200 differ?")
    button(reconciled, "Ask").click().run()
    button(reconciled, "🧾 Reconcile Now").click().run()

    assert reconciled.session_state["chat_history"] == []
    assert len(fakes.calls["ai"]) == 3 + 1 + 3
