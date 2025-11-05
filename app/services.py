import os
from pymongo import MongoClient
from supabase import create_client, Client
from openai import OpenAI

try:
    SUPABASE_URL = os.environ["SUPABASE_URL"]
    SUPABASE_KEY = os.environ["SUPABASE_KEY"]
    MONGO_URI = os.environ["MONGO_URI"]
    HF_TOKEN = os.environ["HF_TOKEN"]
except KeyError as e:
    print(f"FATAL ERROR: Environment variable {e} not set. Please check your .env file.")
    exit()

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized.")
except Exception as e:
    print(f"Supabase client failed: {e}")

try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["resume_db"]
    candidates_collection = db["candidates"]
    mongo_client.server_info()
    print("MongoDB client initialized.")
except Exception as e:
    print(f"MongoDB client failed: {e}")

try:
    openai_client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=HF_TOKEN
    )

    HF_MODEL = "inclusionAI/Ling-1T:featherless-ai"
    print(f"Hugging Face client initialized for model: {HF_MODEL}")
except Exception as e:
    print(f"HF client failed: {e}")