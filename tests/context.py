import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', "src")))

import glorp

# declare __all__ so that the import looks used
__all__ = [
    "glorp",
]