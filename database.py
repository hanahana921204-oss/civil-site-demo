"""SQLite 永久資料、關聯與庫存完整性。"""
from pathlib import Path
import sqlite3
from datetime import date
import math
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / '.runtime_data' / 'demo.db'
TABLES = {
 'vendors': ['name','trade','contact','phone','tax_id','address','rating','active'],
 'materials': ['name','unit','min_stock'],
 'materials_log': ['material_id','vendor_id','date','direction','quantity','unit_price','note'],
 'purchase_documents': ['log_id','document_no','payment_status','reconciliation_status'],
 'petty_cash': ['date','item','amount','handler','note'],
 'equipment': ['code','name','category','maintenance'],
 'equipment_loans': ['equipment_id','borrower','loan_date','due_date','return_date'],
}

@contextmanager
def connect(path=None):
    p = Path(path or DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        with con:
            yield con
    finally:
        con.close()

def init_db(path=None, seed=True):
    with connect(path) as c:
        c.executescript('''
CREATE TABLE IF NOT EXISTS vendors(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(length(trim(name))>0), trade TEXT NOT NULL CHECK(trade IN ('水電','泥作','鋼構','材料供應','其他')), contact TEXT NOT NULL, phone TEXT NOT NULL, tax_id TEXT NOT NULL, address TEXT NOT NULL, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)));
CREATE TABLE IF NOT EXISTS materials(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE CHECK(length(trim(name))>0), unit TEXT NOT NULL CHECK(length(trim(unit))>0), min_stock REAL NOT NULL CHECK(min_stock>=0));
CREATE TABLE IF NOT EXISTS materials_log(id INTEGER PRIMARY KEY, material_id INTEGER NOT NULL REFERENCES materials(id) ON DELETE RESTRICT, vendor_id INTEGER REFERENCES vendors(id) ON DELETE RESTRICT, date TEXT NOT NULL, direction TEXT NOT NULL CHECK(direction IN ('進貨','出貨')), quantity REAL NOT NULL CHECK(quantity>0), unit_price REAL NOT NULL CHECK(unit_price>=0), note TEXT NOT NULL DEFAULT '', CHECK(direction!='進貨' OR vendor_id IS NOT NULL));
CREATE TABLE IF NOT EXISTS purchase_documents(id INTEGER PRIMARY KEY, log_id INTEGER NOT NULL UNIQUE REFERENCES materials_log(id) ON DELETE CASCADE, document_no TEXT NOT NULL UNIQUE CHECK(length(trim(document_no))>0), payment_status TEXT NOT NULL CHECK(payment_status IN ('未請款','已請款','已付款')), reconciliation_status TEXT NOT NULL CHECK(reconciliation_status IN ('未對帳','已對帳','有差異')));
CREATE TABLE IF NOT EXISTS petty_cash(id INTEGER PRIMARY KEY, date TEXT NOT NULL, item TEXT NOT NULL CHECK(length(trim(item))>0), amount REAL NOT NULL CHECK(amount>0), handler TEXT NOT NULL CHECK(length(trim(handler))>0), note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS equipment(id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE CHECK(length(trim(code))>0), name TEXT NOT NULL CHECK(length(trim(name))>0), category TEXT NOT NULL, maintenance INTEGER NOT NULL DEFAULT 0 CHECK(maintenance IN (0,1)));
CREATE TABLE IF NOT EXISTS equipment_loans(id INTEGER PRIMARY KEY, equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON DELETE RESTRICT, borrower TEXT NOT NULL CHECK(length(trim(borrower))>0), loan_date TEXT NOT NULL, due_date TEXT NOT NULL CHECK(due_date>=loan_date), return_date TEXT CHECK(return_date IS NULL OR return_date>=loan_date));
CREATE UNIQUE INDEX IF NOT EXISTS one_open_loan ON equipment_loans(equipment_id) WHERE return_date IS NULL;
CREATE TRIGGER IF NOT EXISTS stock_insert AFTER INSERT ON materials_log BEGIN SELECT CASE WHEN (SELECT COALESCE(SUM(CASE direction WHEN '進貨' THEN quantity ELSE -quantity END),0) FROM materials_log WHERE material_id=NEW.material_id)<-0.0000001 THEN RAISE(ABORT,'庫存不足，無法出貨') END; END;
CREATE TRIGGER IF NOT EXISTS stock_update AFTER UPDATE ON materials_log BEGIN SELECT CASE WHEN EXISTS(SELECT material_id FROM materials_log WHERE material_id IN (OLD.material_id,NEW.material_id) GROUP BY material_id HAVING SUM(CASE direction WHEN '進貨' THEN quantity ELSE -quantity END)<-0.0000001) THEN RAISE(ABORT,'修改後庫存不足') END; END;
CREATE TRIGGER IF NOT EXISTS stock_delete AFTER DELETE ON materials_log BEGIN SELECT CASE WHEN (SELECT COALESCE(SUM(CASE direction WHEN '進貨' THEN quantity ELSE -quantity END),0) FROM materials_log WHERE material_id=OLD.material_id)<-0.0000001 THEN RAISE(ABORT,'刪除後庫存不足') END; END;
CREATE TRIGGER IF NOT EXISTS loan_insert BEFORE INSERT ON equipment_loans WHEN NEW.return_date IS NULL BEGIN SELECT CASE WHEN (SELECT maintenance FROM equipment WHERE id=NEW.equipment_id)=1 THEN RAISE(ABORT,'機具維修中') END; END;
CREATE TRIGGER IF NOT EXISTS loan_update BEFORE UPDATE ON equipment_loans WHEN NEW.return_date IS NULL BEGIN SELECT CASE WHEN (SELECT maintenance FROM equipment WHERE id=NEW.equipment_id)=1 THEN RAISE(ABORT,'機具維修中') END; END;
CREATE TRIGGER IF NOT EXISTS maintenance_update BEFORE UPDATE ON equipment WHEN NEW.maintenance=1 BEGIN SELECT CASE WHEN EXISTS(SELECT 1 FROM equipment_loans WHERE equipment_id=NEW.id AND return_date IS NULL) THEN RAISE(ABORT,'借出中機具不可設為維修') END; END;
''')
    if seed:
        with connect(path) as c:
            if not c.execute('SELECT 1 FROM vendors').fetchone():
                today = date.today().isoformat()
                for i,(name,trade) in enumerate([('示範大地建材','材料供應'),('示範安心水電','水電'),('示範宏達泥作','泥作'),('示範力強鋼構','鋼構'),('示範聯合工程','其他')],1):
                    c.execute('INSERT INTO vendors VALUES(?,?,?,?,?,?,?,?,?)',(i,name,trade,'示範聯絡人','','', '示範地址，非真實廠商',4,1))
                for i,(name,unit,minimum,qty) in enumerate([('水泥','包',30,100),('鋼筋','噸',5,20),('砂石','立方公尺',10,50),('模板','片',20,25)],1):
                    c.execute('INSERT INTO materials VALUES(?,?,?,?)',(i,name,unit,minimum))
                    cur=c.execute("INSERT INTO materials_log(material_id,vendor_id,date,direction,quantity,unit_price,note) VALUES(?,1,?,'進貨',?,100,'示範資料')",(i,today,qty))
                    c.execute("INSERT INTO purchase_documents(log_id,document_no,payment_status,reconciliation_status) VALUES(?,?,'未請款','未對帳')",(cur.lastrowid,f'DEMO-{i:03}'))
                    c.execute("INSERT INTO materials_log(material_id,date,direction,quantity,unit_price,note) VALUES(?,?,'出貨',10,100,'示範領料')",(i,today))
                c.execute("INSERT INTO petty_cash(date,item,amount,handler,note) VALUES(?,'文具',250,'示範管理員','示範資料')",(today,))
                c.executemany('INSERT INTO equipment(code,name,category,maintenance) VALUES(?,?,?,?)',[('EQ001','雷射水平儀','測量',0),('EQ002','電鑽','電動工具',0),('EQ003','切割機','電動工具',1)])

def query(sql, params=(), path=None):
    with connect(path) as c:
        return [dict(r) for r in c.execute(sql,params).fetchall()]

def validate(table, values):
    if table not in TABLES or set(values)!=set(TABLES[table]):
        raise ValueError('資料欄位不完整')
    for key,v in values.items():
        if key in ('date','loan_date','due_date','return_date') and v is not None:
            date.fromisoformat(str(v))
        if isinstance(v,float) and not math.isfinite(v):
            raise ValueError('數字必須是有限值')
    if table=='vendors' and values['tax_id'] and (len(values['tax_id'])!=8 or not values['tax_id'].isdigit()):
        raise ValueError('統編須為八位數字或留空')

def save(table, values, record_id=None, path=None, document=None):
    validate(table,values)
    with connect(path) as c:
        c.execute('BEGIN IMMEDIATE')
        if table=='materials' and record_id:
            old=c.execute('SELECT unit FROM materials WHERE id=?',(record_id,)).fetchone()
            if old and old['unit']!=values['unit'] and c.execute('SELECT 1 FROM materials_log WHERE material_id=?',(record_id,)).fetchone():
                raise ValueError('已有交易的材料不可變更單位，請另建材料')
        if table=='purchase_documents':
            log=c.execute("SELECT 1 FROM materials_log WHERE id=? AND direction='進貨'",(values['log_id'],)).fetchone()
            if not log: raise ValueError('單據只能關聯進貨交易')
        if table=='materials_log' and values['vendor_id'] is not None:
            vendor=c.execute('SELECT active FROM vendors WHERE id=?',(values['vendor_id'],)).fetchone()
            old=c.execute('SELECT vendor_id FROM materials_log WHERE id=?',(record_id,)).fetchone() if record_id else None
            if not vendor or (not vendor['active'] and (not old or old['vendor_id']!=values['vendor_id'])):
                raise ValueError('請選擇啟用中的廠商')
        if record_id is None:
            cols=','.join(values)
            record_id=c.execute(f"INSERT INTO {table}({cols}) VALUES({','.join('?' for _ in values)})",tuple(values.values())).lastrowid
        else:
            if not c.execute(f'SELECT 1 FROM {table} WHERE id=?',(record_id,)).fetchone():
                raise ValueError('資料已不存在，請重新整理')
            c.execute(f"UPDATE {table} SET {','.join(k+'=?' for k in values)} WHERE id=?",(*values.values(),record_id))
        if table=='materials_log':
            if values['direction']=='進貨':
                if document is None: raise ValueError('進貨必須填寫單據')
                c.execute('INSERT INTO purchase_documents(log_id,document_no,payment_status,reconciliation_status) VALUES(?,?,?,?) ON CONFLICT(log_id) DO UPDATE SET document_no=excluded.document_no,payment_status=excluded.payment_status,reconciliation_status=excluded.reconciliation_status',(record_id,document['document_no'],document['payment_status'],document['reconciliation_status']))
            else: c.execute('DELETE FROM purchase_documents WHERE log_id=?',(record_id,))
        return record_id

def delete(table, record_id, path=None):
    if table not in TABLES: raise ValueError('未知資料表')
    with connect(path) as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute(f'DELETE FROM {table} WHERE id=?',(record_id,))

def stocks(path=None):
    return query("SELECT m.*,COALESCE(SUM(CASE l.direction WHEN '進貨' THEN l.quantity ELSE -l.quantity END),0) AS stock FROM materials m LEFT JOIN materials_log l ON l.material_id=m.id GROUP BY m.id",path=path)

def equipment_status(path=None):
    return query("SELECT e.*,CASE WHEN e.maintenance=1 THEN '維修中' WHEN EXISTS(SELECT 1 FROM equipment_loans l WHERE l.equipment_id=e.id AND l.return_date IS NULL) THEN '借出中' ELSE '可借用' END AS status FROM equipment e",path=path)

if __name__=='__main__':
    init_db()
    print(f'資料庫已建立：{DB_PATH}')
