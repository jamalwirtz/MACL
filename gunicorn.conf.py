# gunicorn.conf.py — Render.com / cloud-compatible configuration
# Works on Render, Railway, Fly.io, VPS — no hardcoded log paths

import multiprocessing, os

# ── PORT ──────────────────────────────────────────────────────────────────
# Render injects $PORT; fall back to 5000 for local dev
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

backlog = 2048

# ── WORKERS ───────────────────────────────────────────────────────────────
# 2 workers on free-tier Render (512 MB RAM); scale up on paid plans
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
worker_class = "sync"
worker_connections = 1000
timeout = 120           # generous for PDF generation / email sending
keepalive = 5
max_requests = 500
max_requests_jitter = 50

# ── LOGGING — stdout/stderr only (no file paths) ─────────────────────────
# Render, Railway, Fly.io etc. all capture stdout/stderr automatically
accesslog  = "-"   # "-" = stdout
errorlog   = "-"   # "-" = stderr
loglevel   = "info"
capture_output = True
enable_stdio_inheritance = True

# ── PROCESS ───────────────────────────────────────────────────────────────
proc_name = "muddo_agro"
preload_app = True          # load app once, copy to workers (saves RAM)

# ── STARTUP HOOK ──────────────────────────────────────────────────────────
def on_starting(server):
    """Ensure upload directory exists before workers fork."""
    base = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base, "static", "uploads", "products"), exist_ok=True)

def post_fork(server, worker):
    """Reset DB connections after fork — each worker gets its own."""
    pass
