# in case you see strange errors about lru etc. on a mac with M1 chip, try this

pip uninstall pycryptodome
pip install pycryptodome --no-cache-dir --verbose

pip3 uninstall lru-dict
arch -arm64 pip install lru-dict --no-cache

pip3 uninstall pyethash
arch -arm64 pip install pyethash --no-cache
