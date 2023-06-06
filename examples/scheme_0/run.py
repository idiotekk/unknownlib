import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "../../lib"))
from unknownlib.scheme.main import main

if __name__ == "__main__":
    main()