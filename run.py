#!/usr/bin/env python3
"""Unified launcher for backend (FastAPI) and frontend (HTTP server)."""
from __future__ import annotations

import http.server
import os
import socket
import socketserver
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread

# Configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_HOST = "127.0.0.1"
FRONTEND_PORT = 5500
FRONTEND_DIR = Path(__file__).parent / "frontend"
BACKEND_DIR = Path(__file__).parent / "backend"


def check_port_available(host: str, port: int) -> bool:
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def check_dependencies() -> bool:
    """Verify that required Python packages are installed."""
    required = ["fastapi", "uvicorn", "sqlalchemy", "pydantic"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("🔧 To install: pip install -r requirements.txt")
        return False
    return True


def run_backend() -> None:
    """Start the FastAPI backend with uvicorn."""
    print(f"🚀 Starting Backend at http://{BACKEND_HOST}:{BACKEND_PORT}")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                BACKEND_HOST,
                "--port",
                str(BACKEND_PORT),
                "--reload",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend execution failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Backend stopped.")


def run_frontend() -> None:
    """Start a simple HTTP server for the frontend."""
    print(f"🌐 Starting Frontend at http://{FRONTEND_HOST}:{FRONTEND_PORT}")

    class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

        def log_message(self, format: str, *args: object) -> None:
            # Suppress default logging for cleaner output
            pass

    try:
        with socketserver.ThreadingTCPServer(
            (FRONTEND_HOST, FRONTEND_PORT),
            QuietHTTPRequestHandler,
        ) as httpd:
            httpd.allow_reuse_address = True
            print(f"✅ Frontend ready at: http://{FRONTEND_HOST}:{FRONTEND_PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⚠️  Frontend stopped.")
    except OSError as e:
        print(f"❌ Frontend execution failed: {e}")
        sys.exit(1)


def open_browser() -> None:
    """Open the frontend in the default web browser after a short delay."""
    time.sleep(2)  # Wait for servers to start
    url = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
    print(f"🌍 Opening browser: {url}")
    webbrowser.open(url)


def main() -> None:
    """Main entry point for the launcher."""
    print("=" * 60)
    print("  Library System - Unified Launcher")
    print("=" * 60)
    print()
    
    # Pre-flight checks
    if not check_dependencies():
        sys.exit(1)
    
    if not BACKEND_DIR.exists():
        print(f"❌ Backend directory not found: {BACKEND_DIR}")
        sys.exit(1)
    
    if not FRONTEND_DIR.exists():
        print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        sys.exit(1)
    
    if not check_port_available(BACKEND_HOST, BACKEND_PORT):
        print(f"❌ Port {BACKEND_PORT} is already in use")
        print("   Please stop the other process or change the port")
        sys.exit(1)
    
    if not check_port_available(FRONTEND_HOST, FRONTEND_PORT):
        print(f"❌ Port {FRONTEND_PORT} is already in use")
        print("   Please stop the other process or change the port")
        sys.exit(1)
    
    print("✅ All pre-flight checks passed")
    print()
    
    # Start backend in a separate thread
    backend_thread = Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(1)
    
    # Start frontend in a separate thread
    frontend_thread = Thread(target=run_frontend, daemon=True)
    frontend_thread.start()
    
    # Open browser
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print()
    print("=" * 60)
    print("🎉 System started successfully!")
    print("-" * 60)
    print(f"📡 Backend API:  http://{BACKEND_HOST}:{BACKEND_PORT}")
    print(f"   Docs:         http://{BACKEND_HOST}:{BACKEND_PORT}/docs")
    print(f"🌐 Frontend UI:  http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print("-" * 60)
    print("💡 To stop: Ctrl+C")
    print("=" * 60)
    print()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping system...")
        sys.exit(0)


if __name__ == "__main__":
    main()
