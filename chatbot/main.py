import streamlit as st
from core.db.Database import Database
from core.processing.security import (
    verify_password, hash_password, sanitize_input,
    validate_name, validate_phone, validate_email,
    validate_account_number, validate_password_strength
)
from core.processing.geolocation import Geolocation
from core.stt.transcriber import Transcriber
from core.agent.agent import Agent, LLM
import random
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta
import re
import logging
from typing import Optional, Tuple

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tellerai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Constants ===
MAX_LOGIN_ATTEMPTS = 3
LOGIN_TIMEOUT = 300  # 5 minutes
RATE_LIMIT = 10  # requests per minute

# === Streamlit Page Setup ===
st.set_page_config(
    page_title="Teller.ai",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Custom CSS ===
st.markdown("""
    <style>
    /* Global text colors */
    .stMarkdown, .stText, .stTextInput, .stTextArea {
        color: #1a1a1a;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #efefef !important;
    }
    
    /* Main container */
    .main {
        padding: 2rem;
        background-color: #f0f2f6;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        margin: 5px 0;
        background-color: #2E7D32;
        color: #ffffff;
        border: none;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
        color: #ffffff;
    }
    
    /* Alerts and Messages */
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
    }
    .element-container .stAlert {
        color: #1a1a1a;
    }
    
    /* Form Container */
    .form-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 1rem;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Error Messages */
    .error-message {
        color: #d32f2f;
        font-size: 0.9rem;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    
    /* Profile Card */
    .profile-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .profile-header {
        color: #1a1a1a;
        font-size: 24px;
        margin-bottom: 15px;
        font-weight: 600;
    }
    .profile-info {
        color: #2c3e50;
        font-size: 16px;
        margin: 5px 0;
        font-weight: 500;
    }
    
    /* Recent Chats */
    .recent-chats {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Form Elements */

    .stSelectbox > div > div {
        color: #1a1a1a;
    }
    .stRadio > div {
        color: #1a1a1a;
    }
    
    /* Metrics */
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stMetric > div > div {
        color: #1a1a1a;
    }
    .stMetric > div > div > div {
        color: #2E7D32;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        color: #1a1a1a;
        font-weight: 500;
    }
    
    /* Charts */
    .js-plotly-plot {
        background-color: #ffffff;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #ffffff;
    }
    .css-1d391kg .stButton>button {
        background-color: #2E7D32;
        color: #ffffff;
    }
    
    /* Success Messages */
    .stSuccess {
        background-color: #E8F5E9;
        color: #1B5E20;
    }
    
    /* Warning Messages */
    .stWarning {
        background-color: #FFF3E0;
        color: #E65100;
    }
    
    /* Error Messages */
    .stError {
        background-color: #FFEBEE;
        color: #C62828;
    }
    
    /* Info Messages */
    .stInfo {
        background-color: #E3F2FD;
        color: #1565C0;
    }
    </style>
""", unsafe_allow_html=True)

# === Session Setup ===
def init_session_state():
    defaults = {
        "user": None,
        "welcome_spoken": False,
        "agent_model": LLM.MISTRAL,
        "agent": None,
        "loaded_model": None,
        "user_query": "",
        "query_id": 0,
        "response": "",
        "rating_submitted": False,
        "show_dashboard": False,
        "show_profile": False,
        "login_attempts": 0,
        "last_login_attempt": None,
        "request_count": 0,
        "last_request_time": None,
        "location": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# === Rate Limiting ===
def check_rate_limit() -> bool:
    current_time = time.time()
    if st.session_state.last_request_time is None:
        st.session_state.last_request_time = current_time
        st.session_state.request_count = 1
        return True
    
    time_diff = current_time - st.session_state.last_request_time
    if time_diff >= 60:  # Reset counter after 1 minute
        st.session_state.request_count = 1
        st.session_state.last_request_time = current_time
        return True
    
    if st.session_state.request_count >= RATE_LIMIT:
        return False
    
    st.session_state.request_count += 1
    return True

# === Core Setup ===
try:
    db = Database()
    transcriber = Transcriber()
    geo = Geolocation()
    logger.info("Successfully initialized core components")
except Exception as e:
    logger.error(f"Failed to initialize core components: {e}")
    st.error("Failed to initialize application. Please try again later.")
    st.stop()

# === Helper Functions ===
def get_geolocation() -> Tuple[Optional[float], Optional[float]]:
    """Get user's geolocation."""
    try:
        if st.session_state.location is None:
            lat, long = geo.get_location()
            st.session_state.location = (lat, long)
            logger.info(f"Successfully retrieved location: {lat}, {long}")
        return st.session_state.location
    except Exception as e:
        logger.error(f"Failed to get location: {e}")
        return None, None

def handle_login_attempt() -> bool:
    """Handle login attempt tracking and rate limiting."""
    if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        if st.session_state.last_login_attempt:
            time_diff = time.time() - st.session_state.last_login_attempt
            if time_diff < LOGIN_TIMEOUT:
                remaining_time = int(LOGIN_TIMEOUT - time_diff)
                st.error(f"Too many login attempts. Please try again in {remaining_time} seconds.")
                return False
            else:
                st.session_state.login_attempts = 0
                logger.info("Login attempt counter reset")
    return True

def reset_session():
    """Reset session state."""
    try:
        for key in st.session_state:
            if key != "show_dashboard" and key != "show_profile":
                st.session_state[key] = None
        init_session_state()
        logger.info("Session state reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset session: {e}")
        st.error("Failed to reset session. Please refresh the page.")

# === Main Application Logic ===
def main():
    st.image("assets/teller_logo.png", width=100)
    st.title("🤖 Teller.ai - Your Secure Banking Assistant")

    # === Already Logged In ===
    if st.session_state.user:
        user = st.session_state.user
        db.setUser(user)
        
        # Sidebar for navigation and settings
        with st.sidebar:
            st.header("Navigation")
            if st.button("💬 Chat"):
                st.session_state.show_dashboard = False
                st.session_state.show_profile = False
                st.rerun()
            if st.button("📊 Dashboard"):
                st.session_state.show_dashboard = True
                st.session_state.show_profile = False
                st.rerun()
            if st.button("👤 My Profile"):
                st.session_state.show_dashboard = False
                st.session_state.show_profile = True
                st.rerun()
            
            st.header("Settings")
            st.info("🤖 AI Model Settings")
            st.markdown("""
            The AI model is used for:
            - Processing your banking queries
            - Understanding your intent
            - Generating responses
            - Analyzing sentiment
            """)
            model_choice = st.selectbox(
                "Select AI Model",
                LLM.get_values(),
                index=LLM.get_index(st.session_state.agent_model)
            )
            if model_choice != st.session_state.agent_model.value:
                st.session_state.agent_model = LLM.from_name(model_choice)
                st.session_state.agent = None
                st.rerun()

        if not st.session_state.welcome_spoken:
            try:
                # Simple welcome message without LLM
                welcome_message = f"Welcome back, {user.name}!"
                st.info(welcome_message)
                
                # Initialize agent for future use
                if st.session_state.agent is None:
                    st.session_state.agent = Agent(model=st.session_state.agent_model)
                    st.session_state.loaded_model = st.session_state.agent_model
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                st.warning("⚠️ Could not initialize AI model. Please try again later.")
            st.session_state.welcome_spoken = True

        # === Main Content ===
        if st.session_state.show_dashboard:
            show_dashboard()
        elif st.session_state.show_profile:
            show_user_profile()
        else:
            show_chat_interface()

        # === Logout ===
        if st.sidebar.button("🚪 Logout"):
            reset_session()
            st.rerun()

    # === Login/Register ===
    else:
        show_auth_interface()

def show_chat_interface():
    """Show the chat interface."""
    st.markdown("---")
    st.subheader("💬 Ask Teller.ai")

    # Show current model and its capabilities
    st.info(f"""
    🤖 Using {st.session_state.agent_model.value} model
    
    This model will:
    1. Process your banking query
    2. Detect the intent of your question
    3. Generate a relevant response
    4. Analyze the sentiment of the response
    """)

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
                    st.session_state.user_query = sanitize_input(transcript)
                    st.success(f"You said: {st.session_state.user_query}")
                    logger.info(f"Successfully transcribed: {st.session_state.user_query}")
                except Exception as e:
                    logger.error(f"Speech recognition error: {e}")
                    st.error("⚠️ Speech recognition error. Please try again.")
                    st.stop()
    else:
        st.session_state.user_query = st.text_area(
            "Type your query below:",
            value=st.session_state.get("user_query", ""),
            height=100
        )

    if st.button("💬 Get Response") and st.session_state.user_query.strip():
        if not check_rate_limit():
            st.error("⚠️ Rate limit exceeded. Please wait a moment before trying again.")
            st.stop()

        with st.spinner("Teller.ai is thinking..."):
            try:
                # Initialize agent if not already done
                if st.session_state.agent is None:
                    st.session_state.agent = Agent(model=st.session_state.agent_model)
                    st.session_state.loaded_model = st.session_state.agent_model
                    logger.info(f"Initialized {st.session_state.agent_model.value} model")

                # Process query
                intent, response = st.session_state.agent.get_intent_and_response(
                    st.session_state.user_query
                )
                
                # Store the query and response
                st.session_state.query_id = db.addQuery(
                    st.session_state.user_query,
                    intent,
                    response
                )
                st.session_state.response = response
                st.session_state.rating_submitted = False

                st.subheader("🤖 Teller.ai Responds")
                st.success(st.session_state.response)

                # Display intent and sentiment
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Intent Detected:** `{intent}`")
                with col2:
                    sentiment = st.session_state.agent.analyze_sentiment(response)
                    st.markdown(f"**Response Sentiment:** `{sentiment}`")

                logger.info(f"Successfully processed query with intent: {intent} and sentiment: {sentiment}")

            except Exception as e:
                logger.error(f"Error processing query: {e}")
                st.error("An error occurred while processing your query. Please try again.")

    # === Rating System ===
    if st.session_state.response and not st.session_state.rating_submitted:
        st.markdown("---")
        st.subheader("⭐ Rate this Response")
        rating = st.radio(
            "How would you rate this response?",
            [1, 2, 3, 4, 5],
            horizontal=True,
            format_func=lambda x: "⭐" * x
        )
        if st.button("Submit Rating") and rating:
            try:
                db.updateRating(st.session_state.query_id, rating)
                st.success("✅ Thank you for your feedback!")
                logger.info(f"Rating submitted for query: {st.session_state.query_id}")
                st.session_state.rating_submitted = True
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to submit rating: {e}")
                st.error("Failed to submit rating. Please try again.")

def show_auth_interface():
    """Show the authentication interface."""
    st.header("🔐 Login or Register to Teller.ai")
    
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        # Auth Form
        mode = st.radio("Choose mode:", ["🔐 Login", "🤞 Register"])
        
        with st.form("auth_form"):
            if mode == "🤞 Register":
                name = st.text_input("Full Name", placeholder="Enter your full name")
                phone = st.text_input("Phone Number", placeholder="Enter 10-digit phone number")
                email = st.text_input("Email Address", placeholder="Enter your email address")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
            else:  # Login
                identifier = st.text_input("Email or Phone", placeholder="Enter your email or phone number")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("✔️ Submit")
        
        st.markdown('</div>', unsafe_allow_html=True)

    if not submitted:
        st.stop()

    if not handle_login_attempt():
        st.stop()

    # Get user's location
    try:
        lat, long = get_geolocation()
        location = geo.get_location_name(lat, long) if lat and long else None
    except Exception as e:
        logger.error(f"Failed to get location: {e}")
        lat, long, location = None, None, None

    try:
        if mode == "🤞 Register":
            # Validate all fields
            name_valid, name_error = validate_name(name)
            if not name_valid:
                st.error(name_error)
                st.stop()

            phone_valid, phone_error = validate_phone(phone)
            if not phone_valid:
                st.error(phone_error)
                st.stop()

            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(email_error)
                st.stop()

            password_valid, password_error = validate_password_strength(password)
            if not password_valid:
                st.error(password_error)
                st.stop()

            # Check if user exists
            user_exists = db.getUserFromPhoneNo(phone) or db.getUserFromEmail(email)
            if user_exists:
                st.error("User already registered with this phone or email.")
                st.stop()

            # Create user
            hashed_password = hash_password(password)
            user = db.addUser(name, phone, email, hashed_password, lat, long)
            user.last_location = location
            st.session_state.user = user
            st.success("Registration successful!")
            st.rerun()

        else:  # Login
            if not identifier or not password:
                st.error("Please enter both email/phone and password")
                st.stop()

            # Attempt login
            user = db.authenticate_user(identifier, password)
            if not user:
                st.session_state.login_attempts += 1
                st.session_state.last_login_attempt = time.time()
                st.error("Invalid credentials.")
                st.stop()

            # Update user location
            user.last_location = location
            st.session_state.user = user
            st.success("Login successful!")
            st.rerun()

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        st.error("An error occurred during authentication. Please try again.")

def show_dashboard():
    """Show the analytics dashboard."""
    st.title("📊 Your Analytics Dashboard")
    
    try:
        if st.session_state.user.is_admin:
            # Show admin dashboard
            analytics = db.get_analytics_data()
            
            # User Statistics
            st.header("👥 User Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", analytics['user_stats']['total_users'])
            with col2:
                st.metric("Active Users (30d)", analytics['user_stats']['active_users'])
            with col3:
                st.metric("New Users (30d)", analytics['user_stats']['new_users_30d'])

            # Query Statistics
            st.header("💬 Query Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Query Volume Over Time")
                time_series = pd.DataFrame(
                    list(analytics['query_stats']['time_series'].items()),
                    columns=['date', 'count']
                )
                fig = px.line(time_series, x='date', y='count', title="Daily Query Volume")
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Intent Distribution")
                intent_data = pd.DataFrame(
                    list(analytics['query_stats']['intent_distribution'].items()),
                    columns=['intent', 'count']
                )
                fig = px.pie(intent_data, values='count', names='intent', title="Query Intents")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Location Distribution")
                location_data = pd.DataFrame(
                    list(analytics['query_stats']['location_distribution'].items()),
                    columns=['location', 'count']
                )
                fig = px.bar(location_data, x='location', y='count', title="Queries by Location")
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Sentiment Analysis")
                sentiment_data = pd.DataFrame(
                    list(analytics['query_stats']['sentiment_distribution'].items()),
                    columns=['sentiment', 'count']
                )
                fig = px.pie(sentiment_data, values='count', names='sentiment', title="Query Sentiment")
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Show user-specific dashboard
            analytics = db.get_user_analytics(st.session_state.user.id)
            
            # User Info
            st.header("👤 Your Profile")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", analytics['query_stats']['total_queries'])
                st.metric("Average Rating", f"{analytics['query_stats']['avg_rating']:.1f} ⭐")
            with col2:
                st.metric("Login Count", analytics['user_info']['login_count'])
                st.metric("Last Login", analytics['user_info']['last_login'].strftime('%Y-%m-%d %H:%M') if analytics['user_info']['last_login'] else 'N/A')

            # Query Analysis
            st.header("💬 Your Query Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Intent Distribution")
                intent_data = pd.DataFrame(
                    list(analytics['query_stats']['intent_distribution'].items()),
                    columns=['intent', 'count']
                )
                fig = px.pie(intent_data, values='count', names='intent', title="Your Query Intents")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Sentiment Analysis")
                sentiment_data = pd.DataFrame(
                    list(analytics['query_stats']['sentiment_distribution'].items()),
                    columns=['sentiment', 'count']
                )
                fig = px.pie(sentiment_data, values='count', names='sentiment', title="Your Query Sentiment")
                st.plotly_chart(fig, use_container_width=True)

            # Regional Insights
            st.header("🌍 Regional Insights")
            for key, stats in analytics['regional_stats'].items():
                intent, location = key.split('_')
                with st.expander(f"Similar queries in {location} about {intent}"):
                    st.metric("Total Similar Queries", stats['total_queries'])
                    st.metric("Average Rating", f"{stats['avg_rating']:.1f} ⭐")
                    
                    if stats['sentiment_distribution']:
                        st.subheader("Sentiment Distribution")
                        sentiment_data = pd.DataFrame(
                            list(stats['sentiment_distribution'].items()),
                            columns=['sentiment', 'count']
                        )
                        fig = px.pie(sentiment_data, values='count', names='sentiment')
                        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        st.error("Failed to load dashboard. Please try again later.")

def show_user_profile():
    """Show the user's profile information and recent chats."""
    st.title("👤 My Profile")
    
    # User Information Card
    st.markdown("""
        <style>
        .profile-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .profile-header {
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 15px;
        }
        .profile-info {
            color: #34495e;
            font-size: 16px;
            margin: 5px 0;
        }
        .recent-chats {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # User Details
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="profile-header">Account Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="profile-info">👤 <strong>Name:</strong> {st.session_state.user.name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-info">📧 <strong>Email:</strong> {st.session_state.user.email}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="profile-info">📱 <strong>Phone:</strong> {st.session_state.user.phone}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-info">🏦 <strong>Account Number:</strong> {st.session_state.user.account_number}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent Chats
    st.markdown('<div class="recent-chats">', unsafe_allow_html=True)
    st.subheader("💬 Recent Conversations")
    
    try:
        # Get user's recent queries
        queries = db.get_user_queries(st.session_state.user.id)
        if queries:
            # Sort by timestamp and get last 4
            recent_queries = sorted(queries, key=lambda x: x['timestamp'], reverse=True)[:4]
            
            for query in recent_queries:
                with st.expander(f"Query from {query['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"**Your Question:** {query['query']}")
                    st.markdown(f"**Intent:** {query['intent']}")
                    st.markdown(f"**Response:** {query['response']}")
                    if query['rating']:
                        st.markdown(f"**Rating:** {'⭐' * query['rating']}")
                    if query['sentiment']:
                        st.markdown(f"**Sentiment:** {query['sentiment']}")
        else:
            st.info("No recent conversations found.")
    except Exception as e:
        logger.error(f"Error fetching recent chats: {e}")
        st.error("Failed to load recent conversations.")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
