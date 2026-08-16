"""Mapping characters to their portrait images.

Portrait files are named after the character in lowercase, so the mapping is by
convention rather than stored on the model. Characters without a portrait fall
back to a default image.

Resolving these server side matters: production serves static files with
content-hashed names, and asking for a file that was never collected raises
ValueError. Development storage returns a URL for anything, so an unchecked
name would pass tests and only fail in production.
"""

from pathlib import Path

PORTRAIT_DIR = Path(__file__).resolve().parent / "static" / "calculator" / "portraits"
STATIC_PREFIX = "calculator/portraits"
DEFAULT_PORTRAIT = "default.png"


def portrait_slug(character_name: str) -> str:
    """Return the portrait basename for a character.

    Any parenthesised suffix is dropped, so the Sothe variants
    ("Sothe (Fixed Blossom)", "Sothe (Random Blossom)") share one portrait.
    """
    return character_name.split("(")[0].strip().lower()


def available_portraits() -> set[str]:
    """Filenames present on disk. Read once per request and passed around,
    rather than hitting the filesystem for every character."""
    return {path.name for path in PORTRAIT_DIR.glob("*.png")}


def portrait_path(character_name: str, available: set[str]) -> str:
    """Static path for a character, falling back to the default portrait."""
    filename = f"{portrait_slug(character_name)}.png"
    if filename not in available:
        filename = DEFAULT_PORTRAIT
    return f"{STATIC_PREFIX}/{filename}"


def default_portrait_path() -> str:
    """Static path shown when no character is selected."""
    return f"{STATIC_PREFIX}/{DEFAULT_PORTRAIT}"
