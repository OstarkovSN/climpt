"""simple utilities"""
import pyperclip


def insert_prompt(content):
    """
    Copy prompt content to clipboard.

    Args:
        content (str): Prompt content to copy.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        pyperclip.copy(content)
        return True
    except Exception as e:
        logger.error(f"Error copying to clipboard: {e}")
        return False
