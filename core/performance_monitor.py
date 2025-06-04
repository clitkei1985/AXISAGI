import threading
import time
import psutil
import GPUtil
import json
import logging

logger = logging.getLogger("axis.performance_monitor")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("db/performance.log")
fh.setFormatter(logging.Formatter("%(asctime)s | PERFORMANCE | %(levelname)s | %(message)s"))
logger.addHandler(fh)

class PerformanceMonitor:
    """
    Sample CPU, RAM, and GPU usage every N seconds in a background thread,
    write to db/performance.log, and keep the last snapshot in memory for fast queries.
    """

    _instance = None
    _monitor_thread: threading.Thread = None
    _stop_event = threading.Event()
    _interval = 30  # seconds
    _latest_snapshot = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def start_monitoring(cls, interval: int = 30):
        """
        Start the background thread if not already running.
        """
        inst = cls()
        if cls._monitor_thread and cls._monitor_thread.is_alive():
            return
        cls._interval = interval
        cls._stop_event.clear()
        cls._monitor_thread = threading.Thread(target=cls._monitor_loop, daemon=True)
        cls._monitor_thread.start()
        logger.info(f"Performance monitoring started (interval={interval}s).")

    @classmethod
    def stop_monitoring(cls):
        """
        Signal the thread to stop gracefully.
        """
        cls._stop_event.set()
        if cls._monitor_thread:
            cls._monitor_thread.join()
            logger.info("Performance monitoring stopped.")

    @classmethod
    def _monitor_loop(cls):
        while not cls._stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                virtual_mem = psutil.virtual_memory()._asdict()
                gpu_data = []
                try:
                    for gpu in GPUtil.getGPUs():
                        gpu_data.append({
                            "id": gpu.id,
                            "name": gpu.name,
                            "load": gpu.load,
                            "memoryUtil": gpu.memoryUtil,
                            "memoryTotal": gpu.memoryTotal,
                            "memoryFree": gpu.memoryFree,
                            "memoryUsed": gpu.memoryUsed,
                        })
                except Exception:
                    # No GPU or GPUtil not installed/configured; ignore
                    gpu_data = []

                snapshot = {
                    "cpu_percent": cpu_percent,
                    "virtual_memory": virtual_mem,
                    "gpus": gpu_data
                }
                cls._latest_snapshot = snapshot
                logger.debug(json.dumps(snapshot))
            except Exception as e:
                logger.exception(f"Error in performance monitor loop: {e}")

            # Wait (interval - the 1s already spent by cpu_percent)
            remaining = cls._interval - 1
            if remaining > 0:
                time.sleep(remaining)

    @classmethod
    def get_current_metrics(cls) -> dict:
        """
        Return the most recent snapshot of CPU/Memory/GPU usage.
        """
        return cls._latest_snapshot or {}
