"""
Script to run the FastAPI application

Usage:
    python scripts/run_api.py
    python scripts/run_api.py --host 0.0.0.0 --port 8000
    python scripts/run_api.py --reload  # Development mode
"""

import argparse
import uvicorn
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(description="Run PIKA Memory API")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    args = parser.parse_args()
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    main()

