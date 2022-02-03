from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).absolute().parent / 'proto'))

from .daeh5 import Daeh5  # noqa

__all__ = ('Daeh5',)
