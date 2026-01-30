from pathlib import Path
import sys

python_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(python_dir))
