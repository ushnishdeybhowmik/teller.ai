import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
from typing import Tuple, Optional, Dict, Any, List
import json
import os
from pathlib import Path
import sys

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

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
import re

# === Constants ===
RATE_LIMIT = 60  # Maximum requests per minute
MAX_LOGIN_ATTEMPTS = 5  # Maximum login attempts before timeout
LOGIN_TIMEOUT = 300  # Timeout duration in seconds (5 minutes)

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

# === Database Setup ===
try:
    db = Database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    st.error("Failed to initialize database. Please try again later.")
    st.stop()

# === Core Components Setup ===
try:
    if not hasattr(st, 'transcriber'):
        st.transcriber = Transcriber()
    if not hasattr(st, 'geo'):
        st.geo = Geolocation()
    logger.info("Successfully initialized core components")
except Exception as e:
    logger.error(f"Failed to initialize core components: {e}")
    st.error("Failed to initialize application. Please try again later.")
    st.stop()

# === Session Setup ===
def init_session_state():
    """Initialize session state variables with default values."""
    defaults = {
        "user": None,
        "welcome_spoken": False,
        "agent_model": "mistral",
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
        "location": None,
        "model_initialized": False,
        "chat_history": [],
        "profile_picture": None
    }
    
    # Initialize each key if it doesn't exist
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state at the start
init_session_state()

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
    /* Global Styles */
    :root {
        --primary-color: #2E7D32;
        --secondary-color: #1565C0;
        --accent-color: #E65100;
        --background-color: #1a1a1a;
        --text-color: #ffffff;
        --error-color: #d32f2f;
        --success-color: #2E7D32;
        --warning-color: #E65100;
        --info-color: #1565C0;
    }

    /* Main Container */
    .main {
        padding: 2rem;
        background-color: var(--background-color);
        min-height: 100vh;
        color: var(--text-color);
    }

    /* Navigation */
    .nav-button {
        width: 100%;
        margin: 5px 0;
        padding: 10px;
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .nav-button:hover {
        background-color: #1B5E20;
        transform: translateY(-1px);
    }

    /* Forms */
    .stForm {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stForm .stButton>button {
        width: 100%;
        margin-top: 10px;
    }

    /* Cards */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        margin: 5px 0;
        background-color: var(--primary-color);
        color: white;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
        transform: translateY(-1px);
    }

    /* Form Elements */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 8px 12px;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);
    }

    /* Chat Interface */
    .chat-container {
        padding: 20px;
        background-color: var(--background-color);
        min-height: 100vh;
        color: var(--text-color);
    }
    .chat-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .chat-history {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .chat-message {
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        max-width: 80%;
        position: relative;
        word-wrap: break-word;
    }
    .user-message {
        background-color: var(--primary-color);
        color: white;
        margin-left: auto;
        margin-right: 0;
        border-bottom-right-radius: 5px;
    }
    .bot-message {
        background-color: #e9ecef;
        color: #212529;
        margin-right: auto;
        margin-left: 0;
        border-bottom-left-radius: 5px;
    }
    .chat-timestamp {
        font-size: 0.75rem;
        color: #6c757d;
        margin-top: 5px;
        text-align: right;
    }
    .message-meta {
        font-size: 0.8rem;
        color: #6c757d;
        margin-top: 5px;
        padding-top: 5px;
        border-top: 1px solid rgba(0,0,0,0.1);
    }
    .chat-input {
        padding: 20px;
        background-color: var(--background-color);
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    </style>
""", unsafe_allow_html=True)

def show_dashboard():
    """Show the analytics dashboard."""
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Dashboard header
    st.markdown("""
        <div class="dashboard-header">
            <h1>📊 Analytics Dashboard</h1>
            <p>Your banking insights and statistics</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        if st.session_state.user.is_admin:
            # Admin dashboard
            analytics = db.get_analytics_data()
            
            # Date range selector
            col1, col2 = st.columns([3, 1])
            with col1:
                date_range = st.selectbox(
                    "Time Range",
                    ["Last 7 days", "Last 30 days", "Last 90 days", "Last year", "All time"],
                    index=1
                )
            with col2:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()

            # User Statistics
            st.markdown('<div class="metric-section">', unsafe_allow_html=True)
            st.subheader("👥 User Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Total Users</div>
                    </div>
                """.format(analytics['user_stats']['total_users']), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Active Users (30d)</div>
                    </div>
                """.format(analytics['user_stats']['active_users']), unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">New Users (30d)</div>
                    </div>
                """.format(analytics['user_stats']['new_users_30d']), unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{:.1f}%</div>
                        <div class="metric-label">Growth Rate</div>
                    </div>
                """.format(analytics['user_stats'].get('growth_rate', 0)), unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Query Statistics
            st.markdown('<div class="chart-section">', unsafe_allow_html=True)
            st.subheader("💬 Query Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.subheader("Query Volume Over Time")
                
                time_series = pd.DataFrame(
                    list(analytics['query_stats']['time_series'].items()),
                    columns=['date', 'count']
                )
                fig = px.line(
                    time_series,
                    x='date',
                    y='count',
                    title="Daily Query Volume",
                    template="plotly_white"
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Queries",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.subheader("Location Distribution")
                
                location_data = pd.DataFrame(
                    list(analytics['query_stats']['location_distribution'].items()),
                    columns=['location', 'count']
                )
                fig = px.bar(
                    location_data,
                    x='location',
                    y='count',
                    title="Queries by Location",
                    template="plotly_white"
                )
                fig.update_layout(
                    xaxis_title="Location",
                    yaxis_title="Number of Queries",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        else:
            # User dashboard
            analytics = db.get_user_analytics(st.session_state.user.id)
            
            # User Info
            st.markdown('<div class="user-info-section">', unsafe_allow_html=True)
            st.subheader("👤 Your Profile")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Total Queries</div>
                    </div>
                """.format(analytics['query_stats']['total_queries']), unsafe_allow_html=True)
                
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{:.1f} ⭐</div>
                        <div class="metric-label">Average Rating</div>
                    </div>
                """.format(analytics['query_stats']['avg_rating']), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Login Count</div>
                    </div>
                """.format(analytics['user_info']['login_count']), unsafe_allow_html=True)
                
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Last Login</div>
                    </div>
                """.format(analytics['user_info']['last_login'].strftime('%Y-%m-%d %H:%M') if analytics['user_info']['last_login'] else 'N/A'), unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Query Analysis
            st.markdown('<div class="chart-section">', unsafe_allow_html=True)
            st.subheader("💬 Your Query Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.subheader("Intent Distribution")
                
                intent_data = pd.DataFrame(
                    list(analytics['query_stats']['intent_distribution'].items()),
                    columns=['intent', 'count']
                )
                fig = px.pie(
                    intent_data,
                    values='count',
                    names='intent',
                    title="Your Query Intents",
                    template="plotly_white"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.subheader("Sentiment Analysis")
                
                sentiment_data = pd.DataFrame(
                    list(analytics['query_stats']['sentiment_distribution'].items()),
                    columns=['sentiment', 'count']
                )
                fig = px.pie(
                    sentiment_data,
                    values='count',
                    names='sentiment',
                    title="Your Query Sentiment",
                    template="plotly_white"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        st.error("Failed to load dashboard. Please try again later.")

    st.markdown('</div>', unsafe_allow_html=True)

def show_user_profile():
    """Show the user's profile information and recent chats."""
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    
    # Profile header
    st.markdown("""
        <div class="profile-header">
            <h1>👤 My Profile</h1>
            <p>Manage your account settings and preferences</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        # Refresh user object from database
        refreshed_user = db.refresh_user(st.session_state.user)
        if refreshed_user:
            st.session_state.user = refreshed_user
        else:
            st.error("Failed to load user profile. Please try logging in again.")
            reset_session()
            st.rerun()
            return

        # Profile sections
        col1, col2 = st.columns([2, 3])
        
        with col1:
            # Profile picture and basic info
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            
            # Profile picture
            if st.session_state.profile_picture:
                st.image(st.session_state.profile_picture, width=150)
            else:
                st.markdown("""
                    <div class="profile-avatar">
                        {initial}
                    </div>
                """.format(initial=st.session_state.user.name[0].upper()), unsafe_allow_html=True)
            
            # Upload new profile picture
            uploaded_file = st.file_uploader("Change Profile Picture", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                try:
                    st.session_state.profile_picture = uploaded_file
                except Exception as e:
                    logger.error(f"Failed to update profile picture: {e}")
                    st.error("Failed to update profile picture. Please try again.")
            
            # Basic info
            st.markdown("""
                <div class="profile-info">
                    <h3>Basic Information</h3>
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Account:</strong> {account}</p>
                    <p><strong>Member since:</strong> {created}</p>
                </div>
            """.format(
                name=st.session_state.user.name,
                email=st.session_state.user.email,
                phone=st.session_state.user.phone,
                account=st.session_state.user.account_number,
                created=st.session_state.user.created_at.strftime('%Y-%m-%d')
            ), unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Account settings
            st.markdown('<div class="settings-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Account Settings")
            
            # Change password
            with st.expander("Change Password"):
                with st.form("change_password"):
                    current_password = st.text_input("Current Password", type="password")
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    
                    if st.form_submit_button("Update Password"):
                        if not current_password or not new_password or not confirm_password:
                            st.error("Please fill in all fields")
                        elif new_password != confirm_password:
                            st.error("New passwords do not match")
                        elif not st.session_state.user.verify_password(current_password):
                            st.error("Current password is incorrect")
                        else:
                            try:
                                db.update_password(st.session_state.user.id, new_password)
                            except Exception as e:
                                logger.error(f"Failed to update password: {e}")
                                st.error("Failed to update password. Please try again.")
            
            # Notification preferences
            with st.expander("Notification Preferences"):
                email_notifications = st.toggle("Email Notifications", value=True)
                sms_notifications = st.toggle("SMS Notifications", value=True)
                push_notifications = st.toggle("Push Notifications", value=True)
                
                if st.button("Save Preferences"):
                    try:
                        pass
                    except Exception as e:
                        logger.error(f"Failed to update notification preferences: {e}")
                        st.error("Failed to update preferences. Please try again.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Recent activity
            st.markdown('<div class="activity-card">', unsafe_allow_html=True)
            st.subheader("📊 Recent Activity")
            
            # Activity timeline
            try:
                activities = db.get_user_activities(st.session_state.user.id)
                for activity in activities:
                    with st.expander(f"{activity['type']} - {activity['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                        st.markdown(f"**{activity['title']}**")
                        st.markdown(activity['description'])
                        if activity.get('metadata'):
                            st.json(activity['metadata'])
            except Exception as e:
                logger.error(f"Failed to load activities: {e}")
                st.error("Failed to load recent activities")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Recent conversations
            st.markdown('<div class="conversations-card">', unsafe_allow_html=True)
            st.subheader("💬 Recent Conversations")
            
            try:
                queries = db.get_user_queries(st.session_state.user.id)
                if queries:
                    for query in sorted(queries, key=lambda x: x['timestamp'], reverse=True)[:5]:
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
        
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Profile error: {e}")
        st.error("Failed to load profile. Please try again later.")

def show_chat_interface():
    """Show the chat interface."""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Chat header with model info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("💬 Chat with Teller.ai")
    with col2:
        st.info(f"🤖 Using {st.session_state.agent_model} model")

    # Initialize agent if needed
    initialize_agent()

    # Chat history container with scrolling
    st.markdown("""
        <style>
        .chat-container {
            padding: 20px;
            background-color: var(--background-color);
            min-height: 100vh;
            color: var(--text-color);
        }
        .chat-history {
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .chat-message {
            padding: 15px;
            border-radius: 15px;
            margin: 10px 0;
            max-width: 80%;
            position: relative;
            word-wrap: break-word;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .user-message {
            background-color: var(--primary-color);
            color: white;
            margin-left: auto;
            margin-right: 0;
            border-bottom-right-radius: 5px;
        }
        .bot-message {
            background-color: #e9ecef;
            color: #212529;
            margin-right: auto;
            margin-left: 0;
            border-bottom-left-radius: 5px;
        }
        .chat-timestamp {
            font-size: 0.75rem;
            color: #6c757d;
            margin-top: 5px;
            text-align: right;
        }
        .message-meta {
            font-size: 0.8rem;
            color: #6c757d;
            margin-top: 5px;
            padding-top: 5px;
            border-top: 1px solid rgba(0,0,0,0.1);
        }
        .chat-input {
            padding: 20px;
            background-color: var(--background-color);
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .stTextArea>div>div>textarea {
            background-color: #f8f9fa;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 10px;
            padding: 10px;
        }
        .stButton>button {
            border-radius: 10px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Chat history
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        if message["type"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div class="message-content">{message["content"]}</div>
                    <div class="chat-timestamp">{message["timestamp"]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # For bot messages, include intent and sentiment if available
            meta_info = ""
            if "intent" in message:
                meta_info += f'<div class="message-meta">Intent: {message["intent"]}</div>'
            if "sentiment" in message:
                meta_info += f'<div class="message-meta">Sentiment: {message["sentiment"]}</div>'
            
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <div class="message-content">{message["content"]}</div>
                    {meta_info}
                    <div class="chat-timestamp">{message["timestamp"]}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    
    # Input method selection
    input_col1, input_col2 = st.columns([3, 1])
    with input_col1:
        query_mode = st.radio(
            "Input Method",
            ["⌨️ Text", "🎧 Voice"],
            horizontal=True,
            label_visibility="collapsed",
            key="chat_input_mode"
        )
    
    with input_col2:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
            st.session_state.chat_history = []
            st.info("Chat history cleared")
            st.rerun()

    # Input handling
    if query_mode == "🎧 Voice":
        if st.button("🎧 Start Listening", use_container_width=True, key="start_listening"):
            with st.spinner("Listening..."):
                try:
                    result = st.transcriber.listen()
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
            "Type your message",
            value=st.session_state.get("user_query", ""),
            height=100,
            placeholder="Ask me anything about banking...",
            key="chat_text_input"
        )

    # Send button
    if st.button("💬 Send", use_container_width=True, key="send_message") and st.session_state.user_query.strip():
        if not check_rate_limit():
            st.error("⚠️ Rate limit exceeded. Please wait a moment before trying again.")
            st.stop()

        # Add user message to history
        st.session_state.chat_history.append({
            "type": "user",
            "content": st.session_state.user_query,
            "timestamp": datetime.now().strftime("%H:%M")
        })

        with st.spinner("Teller.ai is thinking..."):
            try:
                # Process query and get response
                intent, response = st.session_state.agent.get_intent_and_response(
                    st.session_state.user_query
                )
                
                # Log the raw response for debugging
                logger.info(f"Raw LLM response - Intent: {intent}, Response: {response}")
                
                # Validate response
                if not response or not intent:
                    raise ValueError("Empty response from LLM")
                
                # Store the query and response
                st.session_state.query_id = db.addQuery(
                    query=st.session_state.user_query,
                    intent=intent,
                    response=response,
                    metadata={
                        "user_id": st.session_state.user.id,
                        "location": st.session_state.user.last_location,
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": st.session_state.agent_model
                    }
                )
                
                # Get sentiment
                sentiment = st.session_state.agent.analyze_sentiment(response)
                
                # Add bot response to history with metadata
                st.session_state.chat_history.append({
                    "type": "bot",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "intent": intent,
                    "sentiment": sentiment
                })

                # Try to speak the response
                try:
                    if st.session_state.agent.speak(response):
                        logger.info("Successfully spoke response")
                    else:
                        logger.warning("Failed to speak response")
                except Exception as e:
                    logger.error(f"Error speaking response: {e}")
                    # Continue execution even if speech fails

                logger.info(f"Successfully processed query with intent: {intent} and sentiment: {sentiment}")
                
                # Clear the input field
                st.session_state.user_query = ""
                st.rerun()

            except Exception as e:
                logger.error(f"Error processing query: {e}")
                error_message = "I apologize, but I'm having trouble processing your request. Please try again."
                st.session_state.chat_history.append({
                    "type": "bot",
                    "content": error_message,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                st.error("An error occurred while processing your query. Please try again.")
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

def show_auth_interface():
    """Show the authentication interface."""
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    # Auth header
    st.markdown("""
        <div class="auth-header">
            <h1>🔐 Welcome to Teller.ai</h1>
            <p>Your secure banking assistant</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Auth form container
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # Mode selection with unique key
    mode = st.radio(
        "Choose mode:",
        ["🔐 Login", "🤞 Register"],
        horizontal=True,
        label_visibility="collapsed",
        key="auth_mode"
    )

    # Registration form
    if mode == "🤞 Register":
        with st.form("registration_form", clear_on_submit=True):
            st.subheader("Create New Account")
            
            name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                help="Your full name as it appears on your bank account",
                key="reg_name"
            )
            
            phone = st.text_input(
                "Phone Number",
                placeholder="Enter 10-digit phone number",
                help="Your registered mobile number",
                key="reg_phone"
            )
            
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                help="Your primary email address",
                key="reg_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Must be at least 8 characters with numbers and special characters",
                key="reg_password"
            )
            
            # Password strength indicator
            if password:
                strength, _ = validate_password_strength(password)
                if strength:
                    st.success("✅ Strong password")
                else:
                    st.error("❌ Weak password")
            
            # Terms and conditions
            terms = st.checkbox(
                "I agree to the Terms and Conditions",
                help="Please read our terms and conditions before proceeding",
                key="reg_terms"
            )
            
            # Submit button for registration
            register_submitted = st.form_submit_button(
                "✔️ Create Account",
                use_container_width=True,
                type="primary"
            )
            
            if register_submitted:
                if not terms:
                    st.error("Please accept the terms and conditions to continue")
                    st.stop()
                
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

                # Get user's location
                try:
                    lat, long = st.geo.get_location()
                    location = f"{lat}, {long}" if lat and long else None
                except Exception as e:
                    logger.error(f"Failed to get location: {e}")
                    lat, long, location = None, None, None

                # Check if user exists
                user_exists = db.getUserFromPhoneNo(phone) or db.getUserFromEmail(email)
                if user_exists:
                    st.error("User already registered with this phone or email.")
                    st.stop()

                # Create user
                try:
                    hashed_password = hash_password(password)
                    user = db.addUser(name, phone, email, hashed_password, lat, long)
                    if user:
                        user.last_location = location
                        st.session_state.user = user
                        st.success("Registration successful!")
                        st.rerun()
                    else:
                        st.error("Failed to create user account. Please try again.")
                except Exception as e:
                    logger.error(f"Registration error: {e}")
                    st.error("An error occurred during registration. Please try again.")
                st.stop()

    # Login form
    else:
        with st.form("login_form", clear_on_submit=True):
            st.subheader("Login to Your Account")
            
            identifier = st.text_input(
                "Email or Phone",
                placeholder="Enter your email or phone number",
                help="Use the email or phone number you registered with",
                key="login_identifier"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your account password",
                help="Enter your account password",
                key="login_password"
            )
            
            # Remember me option
            remember = st.checkbox("Remember me", key="login_remember")
            
            # Submit button for login
            login_submitted = st.form_submit_button(
                "✔️ Login",
                use_container_width=True,
                type="primary"
            )
            
            if login_submitted:
                if not handle_login_attempt():
                    st.stop()

                if not identifier or not password:
                    st.error("Please enter both email/phone and password")
                    st.stop()

                # Get user's location
                try:
                    lat, long = st.geo.get_location()
                    location = f"{lat}, {long}" if lat and long else None
                except Exception as e:
                    logger.error(f"Failed to get location: {e}")
                    lat, long, location = None, None, None

                # Attempt login
                try:
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
                    logger.error(f"Login error: {e}")
                    st.error("An error occurred during login. Please try again.")
                st.stop()

    st.markdown('</div></div>', unsafe_allow_html=True)

def check_rate_limit() -> bool:
    """Check if the user has exceeded the rate limit."""
    try:
        current_time = time.time()
        
        # Initialize rate limit tracking if not exists
        if not hasattr(st.session_state, 'last_request_time'):
            st.session_state.last_request_time = current_time
            st.session_state.request_count = 0
        
        if not hasattr(st.session_state, 'request_count'):
            st.session_state.request_count = 0
            st.session_state.last_request_time = current_time
        
        # Ensure we have valid values
        if st.session_state.last_request_time is None:
            st.session_state.last_request_time = current_time
            st.session_state.request_count = 0
        
        time_diff = current_time - st.session_state.last_request_time
        
        # Reset counter after 1 minute
        if time_diff >= 60:
            st.session_state.request_count = 0
            st.session_state.last_request_time = current_time
            return True
        
        # Check if rate limit exceeded
        if st.session_state.request_count >= RATE_LIMIT:
            return False
        
        # Increment counter
        st.session_state.request_count += 1
        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Reset rate limit tracking on error
        st.session_state.last_request_time = time.time()
        st.session_state.request_count = 0
        return True

def initialize_agent() -> None:
    """Initialize the agent if not already done."""
    try:
        if not hasattr(st.session_state, 'model_initialized'):
            st.session_state.model_initialized = False
        
        if not st.session_state.model_initialized:
            # Convert string model name to LLM enum
            model = LLM.from_name(st.session_state.agent_model)
            
            # Initialize agent with proper error handling
            try:
                st.session_state.agent = Agent(model=model)
                st.session_state.loaded_model = model.value
                st.session_state.model_initialized = True
                logger.info(f"Successfully initialized {model.value} model")
            except FileNotFoundError as e:
                logger.error(f"Model file not found: {e}")
                st.error(f"Could not find the model file for {model.value}. Please ensure the model files are in the correct location.")
                st.stop()
            except Exception as e:
                logger.error(f"Failed to initialize {model.value} model: {e}")
                st.error(f"Failed to initialize {model.value} model. Please try a different model or check the logs for details.")
                st.stop()
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        st.error("Failed to initialize AI model. Please try again later.")
        st.stop()

def get_geolocation() -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Get user's geolocation."""
    try:
        if not hasattr(st.session_state, 'location'):
            st.session_state.location = None
            
        if st.session_state.location is None:
            lat, long = st.geo.get_location()
            location = st.geo.get_location_name(lat, long) if lat and long else None
            st.session_state.location = (lat, long, location)
            logger.info(f"Successfully retrieved location: {lat}, {long}, {location}")
        return st.session_state.location
    except Exception as e:
        logger.error(f"Failed to get location: {e}")
        return None, None, None

def handle_login_attempt() -> bool:
    """Handle login attempt tracking and rate limiting."""
    try:
        if not hasattr(st.session_state, 'login_attempts'):
            st.session_state.login_attempts = 0
            st.session_state.last_login_attempt = None
            
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
    except Exception as e:
        logger.error(f"Login attempt handling failed: {e}")
        return False

def reset_session() -> None:
    """Reset session state."""
    try:
        for key in list(st.session_state.keys()):
            if key != "show_dashboard" and key != "show_profile":
                del st.session_state[key]
        init_session_state()
        logger.info("Session state reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset session: {e}")
        st.error("Failed to reset session. Please refresh the page.")

# === Main Application Logic ===
def main() -> None:
    """Main application entry point."""
    try:
        # Initialize session state first
        init_session_state()
        
        st.image("assets/teller_logo.png", width=100)
        st.title("🤖 Teller.ai - Your Secure Banking Assistant")

        # Main content area
        if st.session_state.user is not None:
            try:
                # Refresh user object from database
                refreshed_user = db.refresh_user(st.session_state.user)
                if refreshed_user:
                    st.session_state.user = refreshed_user
                else:
                    st.error("Failed to load user data. Please try logging in again.")
                    reset_session()
                    st.rerun()
                    return

                # Show sidebar only when user is logged in
                with st.sidebar:
                    st.header("Navigation")
                    
                    # Navigation buttons in column direction
                    if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
                        st.session_state.show_dashboard = False
                        st.session_state.show_profile = False
                        st.rerun()
                    
                    if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
                        st.session_state.show_dashboard = True
                        st.session_state.show_profile = False
                        st.rerun()
                    
                    if st.button("👤 Profile", use_container_width=True, key="nav_profile"):
                        st.session_state.show_dashboard = False
                        st.session_state.show_profile = True
                        st.rerun()

                    st.markdown("---")
                    
                    # Settings
                    st.header("⚙️ Settings")
                    
                    # Model selection
                    st.markdown("### 🤖 AI Model")
                    model_choice = st.selectbox(
                        "Select Model",
                        LLM.get_values(),
                        index=LLM.get_index(st.session_state.agent_model),
                        format_func=lambda x: {
                            "mistral": "Mistral-7B",
                            "gpt": "ChatGPT-3.5",
                            "tinyllama": "TinyLlama-1.1B"
                        }.get(x, x),
                        key="model_selector"
                    )

                    if model_choice != st.session_state.agent_model:
                        st.session_state.agent_model = model_choice
                        st.session_state.agent = None
                        st.session_state.model_initialized = False
                        st.info(f"Switched to {model_choice} model")
                        st.rerun()

                    # Logout button
                    if st.button("🚪 Logout", use_container_width=True, key="nav_logout"):
                        reset_session()
                        st.success("Logged out successfully")
                        st.rerun()

                # Show main content
                if st.session_state.show_dashboard:
                    show_dashboard()
                elif st.session_state.show_profile:
                    show_user_profile()
                else:
                    show_chat_interface()
            except Exception as e:
                logger.error(f"Error in main content area: {e}")
                st.error("An error occurred. Please try refreshing the page.")
                reset_session()
                st.rerun()
        else:
            show_auth_interface()
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        st.error("A critical error occurred. Please refresh the page.")
        reset_session()
        st.rerun()

if __name__ == "__main__":
    main()
