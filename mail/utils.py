import json
import os
import uuid
from datetime import datetime
from config import CONV_FILE

def generate_question_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"IDQ-{timestamp}-{uid}"

def load_conversations():
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_conversations(conversations):
    with open(CONV_FILE, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False) 