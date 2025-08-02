import os

# Create project structure
project_name = "reconciliation_app"
os.makedirs(f"/mnt/data/{project_name}", exist_ok=True)

# app.py content (simplified to save space, full script from earlier)
app_py_content = '''\
import streamlit as st
import pandas as pd
import openai
import yagmail
from io import BytesIO
from twilio.rest import Client

secrets = st.secrets

openai.api_key = secrets["OPENAI_API_KEY"]
EMAIL_SENDER = secrets["EMAIL_SENDER"]
EMAIL_PASSWORD = secrets["EMAIL_PASSWORD"]
EMAIL_RECEIVER = secrets["EMAIL_RECEIVER"]
TWILIO_SID = secrets["TWILIO_SID"]
TWILIO_AUTH_TOKEN = secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

def reconcile_data(xero_df, focus_df):
    xero_df.columns = xero_df.columns.str.strip().str.lower().str.replace(' ', '_')
    focus_df.columns = focus_df.columns.str.strip().str.lower().str.replace(' ', '_')
    xero_df['key'] = xero_df['account_code'].astype(str).str.strip()
    focus_df['key'] = focus_df['gl_code'].astype(str).str.strip()
    merged = pd.merge(xero_df, focus_df, on='key', how='outer', suffixes=('_xero', '_focus'))
    merged = merged.fillna(0)
    merged['debit_diff'] = merged['debit_xero'] - merged['debit_focus']
    merged['credit_diff'] = merged['credit_xero'] - merged['credit_focus']
    merged['status'] = merged.apply(lambda row: "Match" if abs(row['debit_diff']) < 1 and abs(row['credit_diff']) < 1 else "Mismatch", axis=1)
    return merged

def generate_ai_reason(row):
    if row['status'] != 'Mismatch':
        return ""
    prompt = f"""
    Mismatch found:
    - Account Code: {row['key']}
    - Xero \u2192 Debit: {row['debit_xero']}, Credit: {row['credit_xero']}
    - Focus \u2192 Debit: {row['debit_focus']}, Credit: {row['credit_focus']}
    Provide a likely reason in simple terms.
    """
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"AI Error: {str(e)}"

def send_email(file_buffer, filename):
    yag = yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
    yag.send(
        to=EMAIL_RECEIVER,
        subject="Xero vs Focus Reconciliation Report",
        contents="Please find attached the reconciliation output with AI analysis.",
        attachments={filename: file_buffer.getvalue()}
    )
    return "Email sent."

def send_whatsapp_message(to_number, message):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{to_number}"
    )
    return msg.sid

def ask_bot(question, reconciled_df):
    context = reconciled_df.to_csv(index=False)
    prompt = f"""
    You are a financial reconciliation assistant.
    Data:\\n{context}
    Question: {question}
    Answer shortly:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0
    )
    return response['choices'][0]['message']['content'].strip()

st.title("🔄 Xero vs Focus Reconciliation with AI + WhatsApp")

xero_file = st.file_uploader("📤 Upload Xero TB (CSV)", type=['csv'])
focus_file = st.file_uploader("📤 Upload Focus TB (CSV)", type=['csv'])

if st.button("🧾 Reconcile Now") and xero_file and focus_file:
    xero_df = pd.read_csv(xero_file)
    focus_df = pd.read_csv(focus_file)
    reconciled_df = reconcile_data(xero_df, focus_df)

    st.success("✅ Reconciliation Complete")

    with st.spinner("💡 Generating AI Explanations..."):
        reconciled_df['ai_explanation'] = reconciled_df.apply(generate_ai_reason, axis=1)

    st.dataframe(reconciled_df)

    towrite = BytesIO()
    reconciled_df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)

    st.download_button("📥 Download Excel", towrite, "reconciliation_output.xlsx", mime="application/vnd.ms-excel")

    if st.checkbox("📧 Email this report"):
        result = send_email(towrite, "reconciliation_output.xlsx")
        st.info(result)

    if st.checkbox("📱 Send WhatsApp summary"):
        mismatch_count = (reconciled_df['status'] == 'Mismatch').sum()
        total_diff = (reconciled_df['debit_diff'].abs() + reconciled_df['credit_diff'].abs()).sum()
        summary_msg = f"Reconciliation done. {mismatch_count} mismatches found. Total difference: {total_diff:.2f}."
        to_number = st.text_input("Enter WhatsApp number (with country code, e.g. +1234567890)")
        if to_number:
            sid = send_whatsapp_message(to_number, summary_msg)
            st.success(f"WhatsApp message sent! SID: {sid}")

    st.subheader("🤖 Ask the AI Assistant")
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Type your question here about the reconciliation")

    if user_input:
        answer = ask_bot(user_input, reconciled_df)
        st.session_state.chat_history.append((user_input, answer))

    for i, (q, a) in enumerate(st.session_state.chat_history):
        st.markdown(f"**Q:** {q}")
        st.markdown(f"**A:** {a}")
        st.markdown("---")
'''

requirements_txt = '''
streamlit
pandas
openai
openpyxl
yagmail
twilio
'''

# Write files
with open(f"/mnt/data/{project_name}/app.py", "w") as f:
    f.write(app_py_content)

with open(f"/mnt/data/{project_name}/requirements.txt", "w") as f:
    f.write(requirements_txt)

# Zip folder
import shutil
shutil.make_archive(f"/mnt/data/{project_name}", 'zip', f"/mnt/data/{project_name}")

"/mnt/data/reconciliation_app.zip"

