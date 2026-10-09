"""Streamlit script for the tests: runs ../app.py with file uploads, OpenAI,
email and Twilio swapped for the fakes in fakes.py."""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fakes
import openai
import streamlit as st
import twilio.rest
import yagmail

st.file_uploader = fakes.file_uploader
openai.ChatCompletion.create = fakes.chat_completion_create
yagmail.SMTP = fakes.SMTP
twilio.rest.Client = fakes.TwilioClient

runpy.run_path(os.path.join(HERE, "..", "app.py"), run_name="__main__")
