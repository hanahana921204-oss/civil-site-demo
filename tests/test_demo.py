import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from contextlib import closing
from streamlit.testing.v1 import AppTest
import database as db
from demo_runtime import prepare_demo, SEED_PATH, local_today

ROOT=Path(__file__).resolve().parents[1]

class DemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_path=db.DB_PATH
        self.seed_hash=hashlib.sha256(SEED_PATH.read_bytes()).hexdigest()
        self.env=patch.dict(os.environ,{'SITE_DEMO_RUNTIME_DIR':self.tmp.name})
        self.env.start()
    def tearDown(self):
        db.DB_PATH=self.old_path
        self.env.stop()
        self.assertEqual(hashlib.sha256(SEED_PATH.read_bytes()).hexdigest(),self.seed_hash)
        self.tmp.cleanup()
    def test_01_seed_schema_and_privacy(self):
        with closing(sqlite3.connect(SEED_PATH.as_uri()+'?mode=ro',uri=True)) as c:
            for table in db.TABLES:
                self.assertGreater(c.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM vendors').fetchone()[0],5)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM vendors WHERE phone!='' OR tax_id!='' OR address!='' OR name NOT LIKE '示範%' OR contact!='示範窗口'").fetchone()[0],0)
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_02_runtime_isolation_and_no_reset(self):
        target=prepare_demo(db)
        self.assertEqual(target,Path(self.tmp.name)/'demo.db')
        ident=db.save('petty_cash',dict(date=local_today().isoformat(),item='示範測試',amount=10,handler='示範管理員',note=''))
        prepare_demo(db)
        self.assertEqual(db.query('SELECT amount FROM petty_cash WHERE id=?',(ident,))[0]['amount'],10)
        self.assertNotEqual(target,SEED_PATH)
    def test_03_inventory_and_loans(self):
        prepare_demo(db)
        before=db.stocks()[0]['stock']
        values=dict(material_id=1,vendor_id=1,date=local_today().isoformat(),direction='進貨',quantity=10,unit_price=100,note='示範測試')
        ident=db.save('materials_log',values,document=dict(document_no='CLOUD-TEST-001',payment_status='未請款',reconciliation_status='未對帳'))
        self.assertEqual(db.stocks()[0]['stock'],before+10)
        db.delete('materials_log',ident)
        self.assertEqual(db.stocks()[0]['stock'],before)
        values.update(direction='出貨',vendor_id=None,quantity=99999)
        with self.assertRaises(sqlite3.IntegrityError): db.save('materials_log',values)
        self.assertEqual(db.equipment_status()[0]['status'],'借出中')
        with self.assertRaises(sqlite3.IntegrityError):
            db.save('equipment_loans',dict(equipment_id=1,borrower='示範借用人',loan_date=local_today().isoformat(),due_date=local_today().isoformat(),return_date=None))
    def test_04_all_pages_and_submit(self):
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
        self.assertEqual(len(app.exception),0)
        for page in app.sidebar.radio[0].options:
            app.sidebar.radio[0].set_value(page).run()
            self.assertEqual(len(app.exception),0,page)
        app.sidebar.radio[0].set_value('零用金').run()
        next(x for x in app.text_input if x.label=='項目').set_value('示範介面測試')
        next(x for x in app.text_input if x.label=='經手人').set_value('示範管理員')
        next(x for x in app.number_input if x.label=='金額').set_value(60)
        next(x for x in app.button if x.label=='儲存資料').click().run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(len(app.error),0)
        self.assertEqual(db.query('SELECT SUM(amount) total FROM petty_cash')[0]['total'],360)
        self.assertTrue(any('不保證永久保存' in x.value for x in app.sidebar.warning))
    def test_05_cross_platform_sources(self):
        for filename in ('app.py','database.py','demo_runtime.py'):
            text=(ROOT/filename).read_text(encoding='utf-8')
            compile(text,filename,'exec')
            for forbidden in ('C:\\','win32','ctypes','os.startfile','subprocess','site_management.db'):
                self.assertNotIn(forbidden,text)

if __name__=='__main__': unittest.main(verbosity=2)
