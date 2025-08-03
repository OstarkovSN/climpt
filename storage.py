import json
import os
import logging

logger = logging.getLogger(__name__)

PROMPTS_FILE = "prompts.json"


def load_prompts():
    """Load prompts from JSON file"""
    try:
        if not os.path.exists(PROMPTS_FILE):
            # Create default data structure
            default_data = {
                "prompts": [
                    {
                        "id": 1,
                        "name": "Example Prompt",
                        "content": "This is an example prompt content",
                        "tags": ["example", "test"],
                    }
                ]
            }
            # Ensure directory exists
            os.makedirs(
                os.path.dirname(PROMPTS_FILE) if os.path.dirname(PROMPTS_FILE) else ".",
                exist_ok=True,
            )
            with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data["prompts"]

        # Load existing file
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            prompts = data.get("prompts", [])
            logger.info(f"Loaded {len(prompts)} prompts from {PROMPTS_FILE}")
            return prompts

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {PROMPTS_FILE}: {e}")
        # Return empty list but don't overwrite the corrupted file
        return []
    except PermissionError as e:
        logger.error(f"Permission denied accessing {PROMPTS_FILE}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading prompts: {e}")
        return []


def save_prompts(prompts):
    """Save prompts to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(
            os.path.dirname(PROMPTS_FILE) if os.path.dirname(PROMPTS_FILE) else ".",
            exist_ok=True,
        )

        # Validate data structure
        if not isinstance(prompts, list):
            logger.error("Prompts must be a list")
            return False

        # Validate each prompt
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                logger.error(f"Prompt {i} is not a dictionary")
                return False
            if "id" not in prompt or "name" not in prompt or "content" not in prompt:
                logger.error(f"Prompt {i} missing required fields")
                return False

        # Save to file
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"prompts": prompts}, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(prompts)} prompts to {PROMPTS_FILE}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied writing to {PROMPTS_FILE}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving prompts: {e}")
        return False


def backup_prompts():
    """Create a backup of the prompts file"""
    try:
        if os.path.exists(PROMPTS_FILE):
            backup_file = f"{PROMPTS_FILE}.backup"
            import shutil

            shutil.copy2(PROMPTS_FILE, backup_file)
            logger.info(f"Created backup of prompts file: {backup_file}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False


def get_prompts_file_path():
    """Get the full path to the prompts file"""
    return os.path.abspath(PROMPTS_FILE)
