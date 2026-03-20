"""Cross-platform keyring integration for secure API key storage.

Uses the ``keyring`` library, which automatically selects the appropriate backend:

- **macOS**: Keychain Services (via macOS Security framework)
- **Linux**: SecretService (D-Bus / GNOME Keyring) or KWallet
- **Windows**: Windows Credential Manager

If no keyring backend is available (e.g., headless CI without SecretService),
operations return ``None`` (reads) or raise ``RuntimeError`` (writes) with
actionable error messages.

Security notes (macOS):
- Keys are stored under the ``aiir`` service name in the login keychain.
- Access is restricted to the current user session.
- The key is never written to disk by this module.
"""

from __future__ import annotations

from typing import Optional

_SERVICE_NAME = "aiir"
_API_KEY_ACCOUNT = "llm_api_key"


def is_keyring_available() -> bool:
    """Return True if keyring is installed and a working backend is available.

    Performs a lightweight probe read to confirm the backend is functional.
    Does not raise; returns False on any error.
    """
    try:
        import keyring  # noqa: F401

        keyring.get_password(_SERVICE_NAME, "__probe__")
        return True
    except ImportError:
        return False
    except Exception:
        # NoKeyringError or platform backend unavailable
        return False


def set_api_key(api_key: str) -> None:
    """Store the LLM API key in the system keyring.

    On macOS this writes to the login Keychain under the ``aiir`` service.

    Args:
        api_key: The API key string to store (must be non-empty).

    Raises:
        ValueError: If *api_key* is empty.
        ImportError: If the ``keyring`` package is not installed.
        RuntimeError: If no keyring backend is available or the write fails.
    """
    if not api_key:
        raise ValueError("api_key must not be empty")

    try:
        import keyring
    except ImportError as exc:
        raise ImportError(
            "keyring package is not installed.\n"
            "Install it with:  uv add keyring\n"
            "Or set AIIR_LLM_API_KEY in your environment / .env file instead."
        ) from exc

    try:
        keyring.set_password(_SERVICE_NAME, _API_KEY_ACCOUNT, api_key)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to store API key in keyring: {exc}\n"
            "Ensure a keyring backend is available (macOS Keychain, "
            "SecretService, or Windows Credential Manager)."
        ) from exc


def get_api_key() -> Optional[str]:
    """Retrieve the LLM API key from the system keyring.

    Returns:
        The stored API key, or ``None`` if not found or keyring is unavailable.
        Never raises; callers should handle ``None`` as "key not in keyring".
    """
    try:
        import keyring

        return keyring.get_password(_SERVICE_NAME, _API_KEY_ACCOUNT)
    except Exception:
        return None


def delete_api_key() -> None:
    """Remove the LLM API key from the system keyring.

    Args: (none)

    Raises:
        ImportError: If the ``keyring`` package is not installed.
        RuntimeError: If the key does not exist or the delete fails.
    """
    try:
        import keyring
    except ImportError as exc:
        raise ImportError(
            "keyring package is not installed. Install with: uv add keyring"
        ) from exc

    try:
        keyring.delete_password(_SERVICE_NAME, _API_KEY_ACCOUNT)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to delete API key from keyring: {exc}\n"
            "The key may not exist. Check with: aiir config show"
        ) from exc
