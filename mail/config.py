import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL", "lerhinoo@gmail.com")
PASSWORD = os.getenv("PASSWORD", "frvv rzox qmgn mkvq")
SMTP_HOST = 'smtp.gmail.com'
IMAP_HOST = 'imap.gmail.com'
CONV_FILE = "conversations.json" 