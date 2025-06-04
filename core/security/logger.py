import logging
import os

def get_security_logger(name="axis.security"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("db/audit.log")
    fh.setFormatter(logging.Formatter("%(asctime)s | SECURITY | %(levelname)s | %(message)s"))
    if not logger.hasHandlers():
        logger.addHandler(fh)
    return logger 