import streamlit as st
import bcrypt
from database import init_db, User, Search
from ai_models import ModelManager
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

# Initialize database and model manager
db = init_db()
model_manager = ModelManager()

# Password Hashing Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def login_user(username: str, password: str) -> bool:
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        st.session_state.user = {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
        return True
    return False

def register_user(username: str, password: str, is_admin: bool = False) -> bool:
    if db.query(User).filter(User.username == username).first():
        return False
    
    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password, is_admin=is_admin)
    db.add(new_user)
    db.commit()
    return True

def main():
    # Custom CSS for a professional look
    st.markdown("""
        <style>
            /* Gradient Background */
            .main {
                background: linear-gradient(135deg, #121212, #222);
                padding: 30px;
                border-radius: 10px;
            }

            /* Glassmorphism Card */
            .glass-card {
                background: rgba(255, 255, 255, 0.05);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0px 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(8px);
            }

            /* Flex container for logo and title */
            .title-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }

            /* Logo */
            .logo img {
                width: 60px;
                height: auto;
                border-radius: 50%;
            }

            /* Title */
            .title-text {
                font-size: 2rem;
                font-weight: bold;
                color: #ffffff;
                margin: 0;
            }

            /* Subtitle */
            .subtitle {
                font-size: 1.3rem;
                color: #dddddd;
                text-align: center;
                margin-top: 5px;
            }

            /* Sidebar Dark Theme */
            section[data-testid="stSidebar"] {
                background: #111 !important;
                color: white;
            }

        </style>
    """, unsafe_allow_html=True)

    # Aligning logo & title perfectly in one line
    st.markdown("""
        <div class="title-container">
            <div class="logo">
                <img src="https://your-logo-url.com/logo.png" alt="logo">
            </div>
            <h1 class="title-text">MixAlture</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="subtitle">Welcome to the MixAI world</div>', unsafe_allow_html=True)
    st.write("We’ve trained a model called **MixAlture** that interacts in a conversational way. It is a mixture of **Gemini and Hugging Face**.")

    # Sidebar for login/register
    with st.sidebar:
        if st.session_state.user is None:
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                st.subheader("Login")
                login_username = st.text_input("Username", key="login_username")
                login_password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login"):
                    if login_user(login_username, login_password):
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            with tab2:
                st.subheader("Register")
                reg_username = st.text_input("Username", key="reg_username")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                is_admin = st.checkbox("Register as admin")
                if st.button("Register"):
                    if register_user(reg_username, reg_password, is_admin):
                        st.success("Registration successful!")
                    else:
                        st.error("Username already exists")
        else:
            st.write(f"Logged in as: {st.session_state.user['username']}")
            if st.button("Logout"):
                st.session_state.user = None
                st.rerun()

    # Main chat interface
    if st.session_state.user:
        if st.session_state.user['is_admin']:
            tab1, tab2 = st.tabs(["Chat", "User Searches"])
            
            with tab1:
                display_chat_interface()
            
            with tab2:
                display_admin_view()
        else:
            display_chat_interface()
    else:
        st.info("Please login or register to use the chat interface")

def display_chat_interface():
    st.subheader("Chat Interface")
    user_input = st.text_area("Enter your message:")
    
    if st.button("Send"):
        if user_input:
            with st.spinner("Getting response..."):
                response = asyncio.run(model_manager.get_interactive_response(user_input))
                
                search = Search(
                    user_id=st.session_state.user['id'],
                    query=user_input,
                    response=response['response'],
                    model_used=','.join(response['models_used']),
                    timestamp=datetime.utcnow()
                )
                db.add(search)
                db.commit()
                
                st.write("Response:", response['response'])

def display_admin_view():
    st.subheader("User Searches")
    
    searches = db.query(Search).join(User).all()
    
    for search in searches:
        with st.expander(f"Query by {search.user.username} at {search.timestamp}"):
            st.write("Query:", search.query)
            st.write("Response:", search.response)
            st.write("Models Used:", search.model_used)

if __name__ == "__main__":
    main()
