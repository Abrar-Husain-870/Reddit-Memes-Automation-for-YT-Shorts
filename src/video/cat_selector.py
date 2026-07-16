import json
import random
from pathlib import Path
from typing import List, Optional
import config
from src.logger import logger

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}

def load_cat_history() -> List[str]:
    """Load the list of recently used cat reaction clip filenames."""
    if config.CAT_HISTORY_FILE.exists():
        try:
            with open(config.CAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(x) for x in data]
        except Exception as e:
            logger.warning(f"Failed to read cat history: {e}. Starting fresh.")
    return []

def save_cat_history(history: List[str]) -> None:
    """Save the recently used cat reaction clip filenames to history."""
    try:
        config.CAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(config.CAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save cat history: {e}")

def get_cat_reaction_clip() -> Optional[Path]:
    """
    Selects a cat reaction clip from the configured directory.
    Implements repeat prevention based on a history of recently used clips.
    """
    folder = Path(config.CAT_REACTION_FOLDER)
    if not folder.exists():
        logger.warning(f"Cat reaction folder does not exist: {folder}. Creating it.")
        folder.mkdir(parents=True, exist_ok=True)
        return None

    # Discover all supported video clips
    clips = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    ]

    if not clips:
        logger.warning(f"No supported video clips found in cat reaction folder: {folder}")
        return None

    logger.info(f"Discovered {len(clips)} cat reaction clip(s) in {folder.name}")

    if len(clips) == 1:
        logger.info(f"Only one cat clip found: '{clips[0].name}'. Using it.")
        return clips[0]

    # Load history
    history = load_cat_history()
    
    # Define repeat prevention limit (never exclude all clips; leave at least 1)
    max_history_len = max(1, len(clips) - 1)
    
    # Truncate history if it's too long
    if len(history) > max_history_len:
        history = history[-max_history_len:]

    # Filter out recently used clips if requested
    candidates = clips
    if config.CAT_AVOID_REPEAT:
        candidates = [c for c in clips if c.name not in history]
        if not candidates:
            # If all clips have been used, reset history and choose from all
            logger.info("All cat clips have been used recently. Resetting history filter.")
            candidates = clips
            history = []

    # Choose clip based on selection mode
    if config.CAT_SELECTION_MODE.lower() == "sequential":
        # Pick the one that is oldest in history, or alphabetical if none are in history
        candidates_sorted = sorted(candidates, key=lambda c: history.index(c.name) if c.name in history else -1)
        chosen = candidates_sorted[0]
    else:
        # Default: random
        chosen = random.choice(candidates)

    # Update and save history
    if chosen.name in history:
        history.remove(chosen.name)
    history.append(chosen.name)
    
    # Enforce history limit
    if len(history) > max_history_len:
        history = history[-max_history_len:]
        
    save_cat_history(history)
    logger.info(f"Selected cat clip: '{chosen.name}' (saved to history, current history size: {len(history)}/{max_history_len})")
    return chosen
