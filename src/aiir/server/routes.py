"""Route handlers for ai-ir local web UI."""
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from aiir.server.loader import load_report, load_tactic, scan_reports, scan_tactics

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Dashboard showing all reports and knowledge summary statistics."""
    data_dir = request.app.state.data_dir
    reports = scan_reports(data_dir)
    tactics = scan_tactics(data_dir)

    # Stats
    severity_counts: dict[str, int] = {}
    for r in reports:
        sev = r.get("summary", {}).get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    category_counts: dict[str, int] = {}
    for t in tactics:
        cat = t.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {
            "reports": reports,
            "tactics": tactics,
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "data_dir": str(data_dir),
        },
    )


@router.get("/reports", response_class=HTMLResponse)
async def reports_list(request: Request) -> HTMLResponse:
    """Redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")


@router.get("/report", response_class=HTMLResponse)
async def report_view(request: Request, path: str = "") -> HTMLResponse:
    """Display a single incident report by relative path."""
    data_dir = request.app.state.data_dir
    report = load_report(data_dir, unquote(path))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return request.app.state.templates.TemplateResponse(
        request,
        "report.html",
        {"report": report, "path": path},
    )


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_view(
    request: Request, category: str = "", tag: str = ""
) -> HTMLResponse:
    """Knowledge library with optional category and tag filtering."""
    data_dir = request.app.state.data_dir
    all_tactics = scan_tactics(data_dir)

    # Collect filter options
    categories = sorted(set(t.get("category", "other") for t in all_tactics))
    all_tags = sorted(set(tg for t in all_tactics for tg in t.get("tags", [])))

    # Apply filters
    filtered = all_tactics
    if category:
        filtered = [t for t in filtered if t.get("category") == category]
    if tag:
        filtered = [t for t in filtered if tag in t.get("tags", [])]

    return request.app.state.templates.TemplateResponse(
        request,
        "knowledge.html",
        {
            "tactics": filtered,
            "categories": categories,
            "all_tags": all_tags,
            "selected_category": category,
            "selected_tag": tag,
        },
    )


@router.get("/tactic", response_class=HTMLResponse)
async def tactic_view(request: Request, path: str = "") -> HTMLResponse:
    """Display a single tactic detail by relative path."""
    data_dir = request.app.state.data_dir
    tactic = load_tactic(data_dir, unquote(path))
    if not tactic:
        raise HTTPException(status_code=404, detail="Tactic not found")
    return request.app.state.templates.TemplateResponse(
        request,
        "tactic.html",
        {"tactic": tactic, "path": path},
    )


@router.get("/api/reports")
async def api_reports(request: Request) -> JSONResponse:
    """JSON API: list all reports with metadata."""
    reports = scan_reports(request.app.state.data_dir)
    return JSONResponse(
        [
            {
                "path": r["_path"],
                "filename": r["_filename"],
                "title": r.get("summary", {}).get("title", ""),
                "severity": r.get("summary", {}).get("severity", ""),
                "channel": r.get("channel", ""),
            }
            for r in reports
        ]
    )


@router.get("/api/knowledge")
async def api_knowledge(request: Request) -> JSONResponse:
    """JSON API: list all tactics with metadata."""
    tactics = scan_tactics(request.app.state.data_dir)
    return JSONResponse(
        [
            {
                "path": t["_path"],
                "id": t.get("id"),
                "title": t.get("title"),
                "category": t.get("category"),
                "tags": t.get("tags", []),
            }
            for t in tactics
        ]
    )
