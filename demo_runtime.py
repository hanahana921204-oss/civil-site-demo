"""由虛構種子建立展示專用工作資料庫，與本機作業資料隔離。"""
from pathlib import Path
from contextlib import closing
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import sqlite3
import tempfile
import threading

ROOT=Path(__file__).resolve().parent
SEED_PATH=ROOT/'data'/'demo_seed.db'
_LOCK=threading.Lock()

def local_today():
    return datetime.now(ZoneInfo('Asia/Taipei')).date()

def prepare_demo(database, runtime_dir=None):
    directory=Path(runtime_dir or os.environ.get('SITE_DEMO_RUNTIME_DIR') or ROOT/'.runtime_data').resolve()
    target=directory/'demo.db'
    database.DB_PATH=target
    with _LOCK:
        if target.exists():
            return target
        if not SEED_PATH.is_file():
            raise FileNotFoundError('缺少 data/demo_seed.db，請確認 GitHub 已上傳展示種子資料庫。')
        directory.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory,suffix='.db',delete=False) as f:
            temporary=Path(f.name)
        try:
            with closing(sqlite3.connect(SEED_PATH.as_uri()+'?mode=ro',uri=True)) as src:
                with closing(sqlite3.connect(temporary)) as dst:
                    src.backup(dst)
            # 同目錄原子完成首次初始化；重新整理不會重設既有資料。
            os.replace(temporary,target)
        finally:
            if temporary.exists(): temporary.unlink()
    return target
