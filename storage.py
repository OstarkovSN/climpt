import json
import os

PROMPTS_FILE = "prompts.json"

def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        default_data = {
            "prompts": [
                {
                    "id": 1,
                    "name": "Example Prompt",
                    "content": "This is an example prompt content",
                    "tags": ["example", "test"]
                }
            ]
        }
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("prompts", [])
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return []

def save_prompts(prompts):
    try:
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"prompts": prompts}, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving prompts: {e}")
        return False