import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix for Windows console Unicode
import locale

locale.setlocale(locale.LC_ALL, "C")
