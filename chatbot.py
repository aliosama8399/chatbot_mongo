from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Initialize OpenAI API with your key
openai_key = os.getenv("OPENAI_API_KEY")
chat = ChatOpenAI(api_key=openai_key, model="gpt-4")
parser = StrOutputParser()

# MongoDB configuration
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client['chat_history_db']
collection = db['user_chat']

# Function to initialize a new session if it does not exist
def initialize_session(session_id):
    if not collection.find_one({"session_id": session_id}):
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "chat_history": []
        }
        collection.insert_one(session_data)

# Function to update chat history in MongoDB for a specific session
def update_chat_history(session_id, user_input, response):
    collection.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "chat_history": {
                    "timestamp": datetime.now(),
                    "user_input": user_input,
                    "response": response
                }
            }
        }
    )

# Function to retrieve chat history for a specific session
def get_chat_history(session_id):
    session = collection.find_one({"session_id": session_id})
    if session and "chat_history" in session:
        return "\n".join([f"User: {entry['user_input']}\nBot: {entry['response']}" 
                          for entry in session["chat_history"]])
    return ""

# Function to handle chat queries with MongoDB persistence
async def handle_chat_query(session_id, user_input):
    # Initialize session if it doesn't already exist
    initialize_session(session_id)
    
    # Retrieve the existing chat history for context
    chat_history = get_chat_history(session_id)
    
    # Define the template to guide the model's response with the retrieved chat history
    template = f"""
    You are an AI real estate assistant named "DarFind". Your expertise is strictly limited to real estate topics in UAE.
    Avoid content that violates copyrights. For questions not related to real estate, give a reminder that you are an AI real estate assistant.
    
    Keep the chat context in mind based on the previous conversation history.

    Chat History: {chat_history}

    Current Input: {{input}}

    Your main goal is to help the user apply for a property request by asking the following questions in sequence:
    1. Ask the user whether they need the property for rent or buy.
    2. Ask for the type of property (studio, villa, mansion, etc.).
    3. Ask for the desired location inside the UAE.
    4. Ask the user for their budget or budget range (annually or monthly). Check if the amount is reasonable according to the average market price. 
    You can search the internet for this step but don't ever add any links to the conversation except for our website: https://truedar.ae/listings. Do not mention or acknowledge any competitors such as Property Finder, Bayut, Dubizzle, etc.
    5. Ask for the user's phone number. If they refuse, acknowledge that you respect their privacy and continue with the next step.
    6. Ask the user for their email so that an agent can contact them, this step is mandatory.
    7. Summarize the user's request and inform them that they will be contacted by an agent soon. Suggest properties from https://truedar.ae/listings based on their preferences. Do not include any listings from competitors.

    The input is {{input}}. Please respond accordingly.
    """
    
    # Create the prompt using the template
    prompt = ChatPromptTemplate.from_template(template)
    
    # Create a chain to process the input, using OpenAI's model and the prompt template
    chain = LLMChain(
        llm=chat,
        prompt=prompt,
        output_parser=parser
    )
    
    # Invoke the chain to get a response
    response = await chain.acall({"input": user_input})
    
    # Update MongoDB with the latest chat entry
    update_chat_history(session_id, user_input, response['text'])
    
    return response['text']
