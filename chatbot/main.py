import streamlit as st
from core.db.Database import Database
from core.processing.security import verify_password
from core.stt.transcriber import Transcriber
from core.agent.agent import Agent, LLM
import random

# === Streamlit Page Setup ===
st.set_page_config(page_title="Teller.ai", page_icon="🏦")
st.image("assets/teller_logo.png", width=100) 
st.title("🤖 Teller.ai - Your Secure Banking Assistant")
st.markdown(
    """
    <div style="text-align: center;">
        <img src="./assets/teller_logo.png" width="120"/>
    </div>
    """,
    unsafe_allow_html=True
)

# === Session Setup ===
if "user" not in st.session_state:
    st.session_state.user = None
if "welcome_spoken" not in st.session_state:
    st.session_state.welcome_spoken = False
if "agent_model" not in st.session_state:
    st.session_state.agent_model = LLM.MISTRAL
if "agent" not in st.session_state:
    st.session_state.agent = None
if "loaded_model" not in st.session_state:
    st.session_state.loaded_model = None
if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# === Core Setup ===
db = Database()
transcriber = Transcriber()

# === Generate Unique Account Number ===
def generate_unique_account_number():
    while True:
        acc_num = str(random.randint(10**9, 10**10 - 1))
        if not db.getUser(acc_num):
            return acc_num

# === Already Logged In ===
if st.session_state.user:
    user = st.session_state.user
    st.success(f"Welcome back, {user.name}!")

    if not st.session_state.welcome_spoken:
        try:
            if st.session_state.agent is None:
                st.session_state.agent = Agent(model=st.session_state.agent_model)
                st.session_state.loaded_model = st.session_state.agent_model
            st.session_state.agent.speak(f"Welcome back, {user.name}!")
        except RuntimeError:
            st.warning("🔇 Could not play welcome audio.")
        st.session_state.welcome_spoken = True

    # === Lazy Agent Load ===
    if st.session_state.agent is None or st.session_state.agent_model != st.session_state.loaded_model:
        st.session_state.agent = Agent(model=st.session_state.agent_model)
        st.session_state.loaded_model = st.session_state.agent_model

    agent = st.session_state.agent

    st.markdown("---")
    st.subheader("💬 Ask Teller.ai")

    query_mode = st.radio("Choose input method:", ["🎤 Voice", "⌨️ Text"])

    if query_mode == "🎤 Voice":
        if st.button("🎧 Start Listening"):
            with st.spinner("Listening..."):
                try:
                    result = transcriber.listen()
                    transcript = result.get("text", "").strip()
                    if not transcript:
                        st.warning("🔝 Could not transcribe. Please try again.")
                        st.stop()
                    st.session_state.user_query = transcript
                    st.success(f"You said: {transcript}")
                except Exception as e:
                    st.error(f"⚠️ Speech recognition error: {e}")
                    st.stop()
    else:
        st.session_state.user_query = st.text_area("Type your query below:", value=st.session_state.get("user_query", ""))

    if st.button("💬 Get Response") and st.session_state.user_query.strip():
        with st.spinner("Teller.ai is thinking..."):
            intent, response = agent.get_intent_and_response(st.session_state.user_query)
            db.addQuery(st.session_state.user_query, intent)

        st.subheader("🤖 Teller.ai Responds")
        st.success(response)

        if st.checkbox("🔊 Read aloud"):
            try:
                agent.speak(response)
            except RuntimeError:
                st.warning("🔇 Could not play audio.")
                st.text_area("Assistant Response", response, height=150)

        st.markdown(f"**Intent Detected:** `{intent}`")

    # === Logout Option ===
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.welcome_spoken = False
        st.session_state.user_query = ""
        st.session_state.agent = None
        st.session_state.loaded_model = None
        st.rerun()

    st.stop()

# === LOGIN / REGISTER ===
st.header("🔐 Login or Register to Teller.ai")
mode = st.radio("Choose mode:", ["🔐 Login", "🆕 Register"])

# === Model Selector ===
model_choice = st.selectbox("Select AI model for Teller.ai:", ["Mistral", "TinyLlama"])
st.session_state.agent_model = LLM.MISTRAL if model_choice == "Mistral" else LLM.TINYLLAMA

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

    st.success("🎉 Registration successful!")
    st.info(f"🪪 Your Account Number is: `{new_user.account_number}`")
    st.session_state.user = new_user
    st.session_state.welcome_spoken = False
    st.rerun()

# === LOGIN ===
user = db.getUser(account_number)
if not user or not verify_password(password, user.password_hash):
    st.error("Invalid account number or password.")
    st.stop()

st.session_state.user = user
db.setUser(user)
st.session_state.welcome_spoken = False
st.rerun()