# python
# Compatibility wrapper: prefer CPython's logging, fall back to MicroPython's ulogging.
try:
    import logging
except ImportError:
    import ulogging as logging # MicroPython

# Ensure basicConfig exists (no-op on MicroPython)
if not hasattr(logging, "basicConfig"):
    def basicConfig(level=logging.INFO, format=None):
        try:
            root = logging.getLogger()
            root.setLevel(level)
        except Exception:
            pass
    logging.basicConfig = basicConfig

def get_logger(name="app", level=logging.INFO):
    """Return a logger configured to a sensible default level on both platforms."""
    logger = logging.getLogger(name)
    try:
        logger.setLevel(level)
    except Exception:
        pass
    return logger

# Example usage:
# from logging_compat import get_logger, logging
#logging.basicConfig(level=logging.INFO)
#logger = get_logger("gcode")
#logger.info("startup")
