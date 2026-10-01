"""Show which Python interpreter is running this project."""

import sys


print("Python version:", sys.version.split()[0])
print("Python executable:", sys.executable)
print("Using virtual environment:", sys.prefix != sys.base_prefix)
