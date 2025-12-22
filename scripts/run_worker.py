"""
Script helper để chạy worker.
Có thể chạy từ root directory: python scripts/run_worker.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from workers.main import start_extraction_worker, start_proactive_caching_scheduler
    import signal
    import threading
    import asyncio
    
    # Register signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down workers...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start extraction worker in background thread
    extraction_thread = threading.Thread(target=start_extraction_worker, daemon=True)
    extraction_thread.start()
    
    # Start proactive caching scheduler in main thread
    start_proactive_caching_scheduler()

