"""Simple utilities for the Climpt application"""

import pyperclip
import logging
import re

logger = logging.getLogger(__name__)


def insert_prompt(content):
    """
    Copy prompt content to clipboard.

    Args:
        content (str): Prompt content to copy.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        if not isinstance(content, str):
            logger.error("Content must be a string")
            return False

        if not content.strip():
            logger.warning("Attempted to copy empty content")
            return False

        pyperclip.copy(content)
        logger.debug(f"Successfully copied {len(content)} characters to clipboard")
        return True
    except pyperclip.PyperclipException as e:
        logger.error(f"Clipboard operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error copying to clipboard: {e}")
        return False


def get_clipboard_content():
    """
    Get current clipboard content.

    Returns:
        str: Current clipboard content, or empty string if error.
    """
    try:
        content = pyperclip.paste()
        return content if isinstance(content, str) else ""
    except pyperclip.PyperclipException as e:
        logger.error(f"Failed to read clipboard: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error reading clipboard: {e}")
        return ""


def clear_clipboard():
    """
    Clear clipboard content.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        pyperclip.copy("")
        logger.debug("Clipboard cleared")
        return True
    except pyperclip.PyperclipException as e:
        logger.error(f"Failed to clear clipboard: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error clearing clipboard: {e}")
        return False


def is_clipboard_empty():
    """
    Check if clipboard is empty or contains only whitespace.

    Returns:
        bool: True if clipboard is empty or whitespace only, False otherwise.
    """
    try:
        content = get_clipboard_content()
        return not content or not content.strip()
    except Exception as e:
        logger.error(f"Error checking clipboard status: {e}")
        return True


def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to specified length with suffix.

    Args:
        text (str): Text to truncate.
        max_length (int): Maximum length including suffix.
        suffix (str): Suffix to append if truncated.

    Returns:
        str: Truncated text.
    """
    if not isinstance(text, str):
        return ""

    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    return text[: max_length - len(suffix)] + suffix


def correct_qss(qss):
    qss = re.sub("{([^}\n]*)\n", r"{{\1\n", qss)
    qss = re.sub("\n([^{\n]*)}", r"\n\1}}", qss)
    return qss
