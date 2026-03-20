"""FastAPI application factory for ai-ir local web UI."""
import re
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

_RE_NUMBERED_STEP = re.compile(r"(?<!\A)(?<!\n)\s+(\d+\.\s)")


def _strip_at(name: str) -> str:
    """Strip a leading '@' from a username.

    LLMs sometimes return usernames with a leading '@' (copied from the
    '@username' mention syntax in Slack messages). Templates add their own '@'
    prefix, so this filter prevents double '@@' in the display.
    """
    return name.lstrip("@") if name else name


def _format_steps(text: str) -> str:
    """Insert newlines before numbered steps in procedure/observations text.

    LLMs often return multi-step procedures as a single string like
    "1. First step. 2. Second step." — this filter inserts a newline before
    each step number so the text renders readably in a <pre> block.
    """
    if not text:
        return text
    return _RE_NUMBERED_STEP.sub(r"\n\1", text)


def create_app(data_dir: Path) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        data_dir: Directory to scan for report JSON and tactic YAML files.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(title="ai-ir UI", docs_url=None, redoc_url=None)

    templates_dir = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    # Add Jinja2 filters
    templates.env.filters["urlencode"] = quote
    templates.env.filters["format_steps"] = _format_steps
    templates.env.filters["strip_at"] = _strip_at

    # Store data_dir on app state
    app.state.data_dir = data_dir
    app.state.templates = templates

    from aiir.server.routes import router
    app.include_router(router)

    return app
