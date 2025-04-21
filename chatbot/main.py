import streamlit as st
from core.db.Database import Database
from core.processing.security import verify_password
from core.processing.geolocation import Geolocation
from core.stt.transcriber import Transcriber
from core.agent.agent import Agent, LLM
import random
import pandas as pd
import plotly.express as px     

# === Streamlit Page Setup ===
st.set_page_config(page_title="Teller.ai", page_icon="🏦")
st.image("assets/teller_logo.png", width=100) 
st.title("🤖 Teller.ai - Your Secure Banking Assistant")

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
if "query_id" not in st.session_state:
    st.session_state.query_id = 0
if "response" not in st.session_state:
    st.session_state.response = ""
if "rating_submitted" not in st.session_state:
    st.session_state.rating_submitted = False
if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

print("\n\nSession Setup Complete.\n\n")
# === Core Setup ===
db = Database()
transcriber = Transcriber()
geo = Geolocation()
lat, long = geo.get_location()

# === Already Logged In ===
if st.session_state.user:
    user = st.session_state.user
    db.setUser(user)
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

    query_mode = st.radio("Choose input method:", ["🎧 Voice", "⌨️ Text"])

    if query_mode == "🎧 Voice":
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
            st.session_state.query_id = db.addQuery(st.session_state.user_query, intent, response)
            st.session_state.response = response
            st.session_state.rating_submitted = False

        st.subheader("🤖 Teller.ai Responds")
        st.success(st.session_state.response)

        try:
            agent.speak(st.session_state.response)
        except RuntimeError:
            st.warning("🔇 Could not play audio.")
            st.text_area("Assistant Response", st.session_state.response, height=150)

        st.markdown(f"**Intent Detected:** `{intent}`")
        
    if st.button("📊 Go to Dashboard"):
        st.session_state.show_dashboard = True
        st.rerun()
        
    if st.session_state.get("show_dashboard", False):
        st.title("📊 Banking Assistant Dashboard")

        engine = db.getEngine()

        users = pd.read_sql_table("users", engine)
        queries = pd.read_sql_table("user_queries", engine)

        st.sidebar.header("🔎 Filters")
        # ---- INTENT FILTER ----
        intent_options = queries['intent'].dropna().unique().tolist()
        selected_intents = st.sidebar.multiselect("Filter by Intent", options=intent_options, default=intent_options)

        # ---- DATE FILTER ----
        if 'timestamp' in queries.columns:
            queries['timestamp'] = pd.to_datetime(queries['timestamp'])
            min_date = queries['timestamp'].min().date()
            max_date = queries['timestamp'].max().date()

            start_date, end_date = st.sidebar.date_input(
                "Filter by Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            if isinstance(start_date, tuple):
                start_date, end_date = start_date
        else:
            start_date = end_date = None

        # === FILTERING ===
        filtered_queries = queries[queries['intent'].isin(selected_intents)]
        if start_date and end_date:
            date_mask = (filtered_queries['timestamp'].dt.date >= start_date) & (filtered_queries['timestamp'].dt.date <= end_date)
            filtered_queries = filtered_queries[date_mask]

        st.subheader("📍 User Locations")
        if not users.empty and 'latitude' in users and 'longitude' in users:
            try:
                users[['latitude', 'longitude']] = users[['latitude', 'longitude']].astype(float)
                st.map(users[['latitude', 'longitude']])
            except ValueError:
                st.warning("Invalid coordinate data in database.")
        else:
            st.warning("No location data available to display on map.")

        st.subheader("📈 Summary Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", len(users))
        col2.metric("Total Queries", len(filtered_queries))
        avg_rating = filtered_queries['rating'].mean() if 'rating' in filtered_queries.columns else None
        col3.metric("Average Rating", f"{avg_rating:.2f}" if avg_rating else "N/A")

        st.subheader("🧠 Common Intents")
        if 'intent' in filtered_queries.columns:
            intent_counts = filtered_queries['intent'].value_counts().reset_index()
            intent_counts.columns = ['Intent', 'Count']
            fig = px.bar(intent_counts, x='Intent', y='Count', title="Intent Frequency")
            st.plotly_chart(fig, use_container_width=True)

        if 'rating' in filtered_queries.columns:
            st.subheader("⭐ Ratings Distribution")
            fig2 = px.histogram(filtered_queries, x='rating', nbins=5, title="Query Ratings")
            st.plotly_chart(fig2, use_container_width=True)

        if 'timestamp' in filtered_queries.columns:
            st.subheader("🕒 Query Volume Over Time")
            time_series = filtered_queries.groupby(pd.Grouper(key='timestamp', freq='D')).size().reset_index(name='count')
            fig3 = px.line(time_series, x='timestamp', y='count', title="Daily Query Count")
            st.plotly_chart(fig3, use_container_width=True)

        if st.button("⬅️ Back to Assistant"):
            st.session_state.show_dashboard = False
            st.rerun()

    if st.session_state.response and not st.session_state.rating_submitted:
        rating = st.radio("How would you rate this response?", [1, 2, 3, 4, 5], horizontal=True)
        if st.button("Submit Rating") and rating:
            db.updateRating(st.session_state.query_id, rating)
            st.success("✅ Thank you for your feedback!")
            print("Rating submitted for query:", st.session_state.query_id)
            st.markdown("---")
            st.session_state.user_query = ""
            st.session_state.query_id = 0
            st.session_state.response = ""
            st.session_state.rating_submitted = True
            st.rerun()

    # === Logout Option ===
    if st.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.welcome_spoken = False
        st.session_state.user_query = ""
        st.session_state.agent = None
        st.session_state.loaded_model = None
        st.session_state.query_id = 0
        st.session_state.response = ""
        st.session_state.rating_submitted = False
        st.rerun()

    st.stop()
    
else:
# === LOGIN / REGISTER ==
    
    st.header("🔐 Login or Register to Teller.ai")
    mode = st.radio("Choose mode:", ["🔐 Login", "🤞 Register"])

    # === Model Selector ===
    model_choice = st.selectbox("Select AI model for Teller.ai:", ["Mistral", "TinyLlama", "ChatGPT"])
    if model_choice == "Mistral":
        st.session_state.agent_model = LLM.MISTRAL
    elif model_choice == "TinyLlama":
        st.session_state.agent_model = LLM.TINYLLAMA
    else:
        st.session_state.agent_model = LLM.CHATGPT

    with st.form("auth_form"):
        if mode == "🤞 Register":
            name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")

        if mode == "🔐 Login":
            account_number = st.text_input("Account Number")

        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("✔️ Submit")

    if not submitted:
        st.stop()

    # === REGISTER ===
    if mode == "🤞 Register":
        user_exists = db.getUserFromPhoneNo(phone)
        if user_exists:
            st.error("User already exists. Please log in.")
            st.stop()

        new_user = db.userExistOrCreate(name, phone, password)

        st.success("🎉 Registration successful!")
        st.info(f"🧪 Your Account Number is: `{new_user.account_number}`")
        if st.button("Let's Chat!"):
            st.session_state.user = new_user
            db.setUser(new_user)
            db.updateLocation(lat, long)
            st.session_state.welcome_spoken = False
            st.rerun()

    # === LOGIN ===
    else:
        user = db.getUser(account_number)
        if not user or not verify_password(password, user.password_hash):
            st.error("Invalid account number or password.")
            st.stop()

        st.session_state.user = user
        db.setUser(user)
        db.updateLocation(lat, long)
        print("User logged in:", user.name, "\nAccount Number:", user.account_number, "\nLatitude:", user.latitude, "\nLongitude:", user.longitude)
        st.session_state.welcome_spoken = False
        st.rerun()
