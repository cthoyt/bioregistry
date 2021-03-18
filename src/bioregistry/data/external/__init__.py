# -*- coding: utf-8 -*-

"""External resources."""

import os
from pathlib import Path

__all__ = [
    'ONTOBEE_PATH',
]

HERE = Path(os.path.abspath(os.path.dirname(__file__)))
ONTOBEE_PATH = HERE / 'ontobee.json'
