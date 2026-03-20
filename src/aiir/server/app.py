"""FastAPI application factory for ai-ir local web UI."""
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates


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

    # Add urlencode filter to Jinja2 environment
    templates.env.filters["urlencode"] = quote

    # Store data_dir on app state
    app.state.data_dir = data_dir
    app.state.templates = templates

    from aiir.server.routes import router
    app.include_router(router)

    return app
