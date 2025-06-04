import platform
import subprocess
import json
import logging
from typing import Dict

logger = logging.getLogger("axis.env_detect")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("db/env.log")
fh.setFormatter(logging.Formatter("%(asctime)s | ENV_DETECT | %(levelname)s | %(message)s"))
logger.addHandler(fh)

def detect_os() -> Dict[str, str]:
    """
    Return OS name, version, architecture.
    """
    data = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
    }
    logger.debug(f"Detected OS info: {data}")
    return data

def detect_python() -> Dict[str, str]:
    """
    Return Python version and executable path.
    """
    data = {
        "python_version": platform.python_version(),
        "python_executable": platform.python_executable(),
    }
    logger.debug(f"Detected Python info: {data}")
    return data

def detect_cuda() -> Dict[str, str]:
    """
    Attempt to run 'nvidia-smi --query-gpu=driver_version --format=csv,noheader'
    to detect CUDA driver. If not found, return empty or error message.
    """
    result = {"cuda_driver": None, "cuda_error": None}
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        driver_ver = completed.stdout.strip().split("\n")[0]
        result["cuda_driver"] = driver_ver
    except FileNotFoundError:
        result["cuda_error"] = "nvidia-smi not found"
    except subprocess.CalledProcessError as e:
        result["cuda_error"] = f"Error running nvidia-smi: {e.stderr.strip()}"
    logger.debug(f"Detected CUDA info: {result}")
    return result

def detect_gpu() -> Dict[str, str]:
    """
    Run 'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader'
    to list GPU names and memory. If no GPU, return empty.
    """
    result = {"gpus": []}
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        lines = completed.stdout.strip().split("\n")
        for line in lines:
            name, mem = [x.strip() for x in line.split(",")]
            result["gpus"].append({"name": name, "memory": mem})
    except FileNotFoundError:
        result["gpus"] = []
    except subprocess.CalledProcessError as e:
        result["error"] = f"Error running nvidia-smi: {e.stderr.strip()}"
    logger.debug(f"Detected GPU info: {result}")
    return result

def detect_all() -> Dict[str, Dict]:
    """
    Convenience method to return all environment info.
    """
    env_info = {
        "os": detect_os(),
        "python": detect_python(),
        "cuda": detect_cuda(),
        "gpu": detect_gpu(),
    }
    return env_info
