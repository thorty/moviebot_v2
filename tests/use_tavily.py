import sys
import os

# Füge das Parent-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.tools import internet_search_tavily


# Test die Funktion
result = internet_search_tavily.invoke({"query": "beste Fantasy Serien 2024"})
print(result)