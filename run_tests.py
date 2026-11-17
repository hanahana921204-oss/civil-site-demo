"""執行展示專用隔離測試；不連線本機正式資料庫。"""
from pathlib import Path
import os
import sys
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
with (ROOT/'test-output.txt').open('w',encoding='utf-8') as output:
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
print((ROOT/'test-output.txt').read_text(encoding='utf-8'))
sys.exit(0 if result.wasSuccessful() else 1)
