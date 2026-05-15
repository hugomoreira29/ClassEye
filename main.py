import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ui"))

from app import launch

if __name__ == "__main__":
    launch()
