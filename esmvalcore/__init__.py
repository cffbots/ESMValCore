"""ESMValTool core package."""
import logging
import os

from ._version import __version__
from .config import CFG

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    '__version__',
    'cmor',
    'CFG',
    'preprocessor',
]


def get_script_root():
    """Return the location of the ESMValTool installation."""
    return os.path.abspath(os.path.dirname(__file__))
