import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import google.generativeai as genai
import logging

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="Emotion-Aware Generative Chatbot API",
    description="An API that uses a local model for emotion detection and Gemini for response generation.",
    version="1.0.0"
)

# --- Load Local Emotion Classifier ---
# This uses your highly accurate, fine-tuned model for fast analysis.
try:
    logging.info("Loading local emotion classification model...")
    emotion_classifier = pipeline("text-classification", model="./emotion_model")
    logging.info("Local model loaded successfully!")
except Exception as e:
    logging.error(f"Fatal error: Could not load local emotion model. {e}")
    # In a real app, you might not want to start if the core model fails.
    emotion_classifier = None

# --- Configure the Gemini LLM ---
# This is the powerful generative part of our chatbot.
try:
    api_key = 'AIzaSyDfFuOHcTvfwegkELpJrY1kG6JVHsfnlkQ'
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please set the key to run the application.")
    genai.configure(api_key=api_key)
    llm_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    logging.info("Gemini LLM configured successfully!")
except Exception as e:
    logging.error(f"Fatal error: Could not configure Gemini LLM. {e}")
    llm_model = None

# --- Function to Generate a High-Quality LLM Response ---
def generate_llm_response(user_message: str, emotion: str) -> str:
    """
    Constructs a detailed prompt and gets a generative response from the Gemini LLM.
    """
    if not llm_model:
        raise HTTPException(status_code=503, detail="Advanced reasoning capabilities are currently offline.")

    # The "meta-prompt" defines the chatbot's persona and instructions.
    # This is where you can customize your bot's personality.
    system_prompt = f"""
    You are an advanced customer support AI for a company named 'InnovateTech'.
    Your primary goal is to be helpful, empathetic, and concise.
    A customer has sent the following message. My internal analysis suggests the customer is feeling '{emotion}'.
    
    Based on their message and this emotional context, please provide a supportive and helpful response.
    - If the emotion is negative (like anger, sadness, fear), be extra reassuring and offer clear next steps.
    - If the emotion is positive (like joy or admiration), share in their positivity before addressing their query.
    - Keep your response to 2-3 sentences maximum.
    
    Customer's message: "{user_message}"
    """
    
    try:
        logging.info(f"Generating Gemini response for emotion: {emotion}")
        response = llm_model.generate_content(system_prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error during Gemini API call: {e}")
        # Provide a safe, generic fallback response
        raise HTTPException(status_code=500, detail="I encountered an issue while processing your request.")

# --- Define the request and response models for our API ---
class UserInput(BaseModel):
    message: str

class ChatResponse(BaseModel):
    detected_emotion: str
    reply: str

# --- Main Chat API Endpoint ---
@app.post("/chat", response_model=ChatResponse)
def chat(user_input: UserInput):
    if not emotion_classifier:
        raise HTTPException(status_code=503, detail="Emotion detection service is currently unavailable.")

    # Step 1: Detect emotion using your fast local model
    try:
        emotion_result = emotion_classifier(user_input.message)[0]
        emotion = emotion_result['label']
        logging.info(f"Detected emotion: {emotion}")
    except Exception as e:
        logging.error(f"Error during emotion classification: {e}")
        raise HTTPException(status_code=500, detail="Could not analyze message emotion.")

    # Step 2: Generate a dynamic, empathetic response using Gemini
    bot_reply = generate_llm_response(user_input.message, emotion)

    # Step 3: Return the structured response
    return ChatResponse(detected_emotion=emotion, reply=bot_reply)

# --- Root endpoint for health check ---
@app.get("/")
def read_root():
    return {"status": "InnovateTech Chatbot API is running."}

