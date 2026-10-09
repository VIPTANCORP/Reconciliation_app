"""Fake uploads and external services for the app tests.

Every call to OpenAI, email or Twilio is recorded in `calls`, so tests can
check that each action fires exactly once.
"""
import io

UPLOADS = {
    "📤 Upload Xero TB (CSV)": "Account Code,Debit,Credit\n100,500,0\n200,0,250\n300,50,0\n",
    "📤 Upload Focus TB (CSV)": "GL Code,Debit,Credit\n100,500,0\n200,0,240\n400,10,0\n",
}

AI_ANSWER = "fake answer"

calls = {"ai": [], "email": [], "whatsapp": []}


def reset():
    for recorded in calls.values():
        recorded.clear()


class AttrDict(dict):
    """Like openai<1.0 responses: supports both item and attribute access."""
    __getattr__ = dict.__getitem__


def file_uploader(label, **kwargs):
    return io.BytesIO(UPLOADS[label].encode())


def chat_completion_create(**kwargs):
    calls["ai"].append(kwargs)
    return AttrDict(choices=[AttrDict(message=AttrDict(content=AI_ANSWER))])


class SMTP:
    def __init__(self, *args, **kwargs):
        pass

    def send(self, **kwargs):
        calls["email"].append(kwargs)


class TwilioClient:
    def __init__(self, *args, **kwargs):
        self.messages = self

    def create(self, **kwargs):
        calls["whatsapp"].append(kwargs)
        return AttrDict(sid="SM123")
