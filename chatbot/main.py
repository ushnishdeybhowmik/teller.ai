import streamlit as st
from core.db.Database import Database
from core.processing.security import verify_password, hash_password
from core.stt.transcriber import Transcriber
from core.agent.agent import Agent
import random

# === Session setup ===
if "user" not in st.session_state:
    st.session_state.user = None

# === Core Setup ===
st.set_page_config(page_title="BankBot", page_icon="🏦")
st.title("🏦 BankBot - Secure Banking Assistant")

db = Database()
transcriber = Transcriber()
agent = Agent()

# === Helper to generate account number ===
def generate_unique_account_number():
    while True:
        acc_num = str(random.randint(10**9, 10**10 - 1))  # 10-digit number
        if not db.getUser(acc_num):
            return acc_num

# === Already Logged In ===
if st.session_state.user:
    user = st.session_state.user
    st.success(f"Welcome back, {user.name}!")
    agent.speak(f"Welcome back, {user.name}!")
    st.markdown("---")

    # === CHAT INTERFACE ===
    query_mode = st.radio("Choose input method:", ["🎤 Voice", "⌨️ Text"])
    user_query = ""

    if query_mode == "🎤 Voice":
        if st.button("🎙️ Start Listening"):
            with st.spinner("Listening..."):
                user_query = transcriber.listen()["text"]
            st.success(f"You said: {user_query}")
    else:
        user_query = st.text_area("Type your query below:")

    if st.button("💬 Get Response") and user_query.strip():
        with st.spinner("Thinking..."):
            intent, response = agent.get_intent_and_response(user_query)

            # Store in DB
            db.addQuery(user_query, intent)

        st.subheader("🤖 Response")
        st.success(response)

        if st.checkbox("🔊 Read aloud"):
            agent.speak(response)

        st.markdown(f"**Intent Detected:** `{intent}`")

    # === Logout Option ===
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

    st.stop()

# === LOGIN / REGISTER ===
st.header("🔐 Login or Register")
mode = st.radio("Choose", ["🔐 Login", "🆕 Register"])

with st.form("auth_form"):
    if mode == "🆕 Register":
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")

    if mode == "🔐 Login":
        account_number = st.text_input("Account Number")

    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("✔️ Submit")

if not submitted:
    st.stop()

# === REGISTER ===
if mode == "🆕 Register":
    user_exists = db.getUserFromPhoneNo(phone)
    if user_exists:
        st.error("User already exists. Please log in.")
        st.stop()

    account_number = generate_unique_account_number()
    new_user = db.userExistOrCreate(name, phone, password, account_number=account_number)

    st.success("Registration successful! Your Account Number is: " + new_user.account_number)
    st.session_state.user = new_user
    st.rerun()

# === LOGIN ===
user = db.getUser(account_number)
if not user or not verify_password(password, user.password_hash):
    st.error("Invalid account number or password.")
    st.stop()

st.session_state.user = user
st.rerun()
