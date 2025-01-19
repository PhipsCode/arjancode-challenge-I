import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API")

# API_KEY = "demo"
BASE_URL = "https://www.alphavantage.co/query"

API_URL = f"apikey={API_KEY}"

