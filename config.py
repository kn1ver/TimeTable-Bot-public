import os
import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
PORT = os.getenv("PORT")
URL = os.getenv("URL")

MESSAGES = {}

