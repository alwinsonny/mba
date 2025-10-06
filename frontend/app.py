import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="InnovateTech Support Chat",
    page_icon="🤖",
    layout="centered"
)

# --- App Title and Description ---
st.title("🤖 InnovateTech Customer Support")
st.markdown("Welcome! I'm here to help. Please describe your issue, and I'll do my best to assist you.")

# --- Configuration ---
# This is the URL where your FastAPI backend is running.
# Make sure it matches the host and port of your uvicorn server.
FASTAPI_URL = "http://127.0.0.1:8000/chat"

# --- Session State Initialization ---
# This keeps track of the chat history.
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        ("bot", "Hello! How can I help you today?")
    ]

# --- Display Chat History ---
for author, message in st.session_state.messages:
    with st.chat_message(author):
        st.markdown(message)

# --- Handle User Input ---
if user_prompt := st.chat_input("Your message..."):
    # Add user message to chat history and display it
    st.session_state.messages.append(("user", user_prompt))
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # --- Call the FastAPI Backend ---
    with st.spinner("Thinking..."):
        try:
            # Prepare the data payload for the API
            payload = {"message": user_prompt}
            
            # Send the request to the backend
            response = requests.post(FASTAPI_URL, json=payload)
            response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)

            # --- Process the response from the backend ---
            data = response.json()
            
            # **HERE IS THE FIX:** We use the correct keys from the FastAPI response
            detected_emotion = data.get("detected_emotion", "unknown")
            bot_reply = data.get("reply", "Sorry, I had trouble generating a response.")
            
            # Create a formatted response for the UI
            formatted_response = f"""
            {bot_reply}
            
            ---
            *Detected Emotion: {detected_emotion.capitalize()}*
            """
            
            # Add bot response to chat history and display it
            st.session_state.messages.append(("bot", formatted_response))
            with st.chat_message("bot"):
                st.markdown(formatted_response)

        except requests.exceptions.RequestException as e:
            # Handle network errors (e.g., backend is not running)
            error_message = f"**Error:** Could not connect to the chatbot server. Please ensure the backend is running. ({e})"
            st.error(error_message)
            st.session_state.messages.append(("bot", error_message))
        except Exception as e:
            # Handle other potential errors
            error_message = f"**An unexpected error occurred:** {e}"
            st.error(error_message)
            st.session_state.messages.append(("bot", error_message))

