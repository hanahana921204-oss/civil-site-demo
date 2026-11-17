from datetime import date
import sqlite3
import pandas as pd
import streamlit as st
import database as db
from demo_runtime import prepare_demo, local_today

prepare_demo(db)

st.set_page_config(page_title='土木工地管理系統',page_icon='🏗️',layout='wide')
db.init_db(seed=False)
st.markdown('''<style>.stApp{background:#f5f5f7;color:#1d1d1f} .block-container{max-width:1250px;padding-top:2rem} div[data-testid="stMetric"]{background:white;border-radius:18px;padding:20px} .stButton>button[kind="primary"],.stFormSubmitButton>button{background:#007aff;color:white;border:0;border-radius:10px} [data-testid="stSidebar"]{background:#fff} h1{letter-spacing:-1px} </style>''',unsafe_allow_html=True)
st.title('土木工地管理系統')
st.caption('日常行政 · 材料進出貨 · 協力廠商')
page=st.sidebar.radio('功能選單',['首頁 Dashboard','材料基本資料','材料進出貨','協力廠商名錄','進貨單據查詢','零用金','機具管理','機具借還'])
st.sidebar.warning('公開教學展示：請勿輸入真實電話、統編、姓名或地址。所有訪客共用資料，操作會互相影響；SQLite 寫入不保證永久保存。')
if 'flash' in st.session_state: st.success(st.session_state.pop('flash'))

def frame(rows):
    labels={'id':'編號','name':'名稱','trade':'工種','contact':'聯絡人','phone':'電話','tax_id':'統編','address':'地址','rating':'配合評價','active':'啟用','unit':'單位','min_stock':'警戒庫存','stock':'目前庫存','date':'日期','direction':'類型','quantity':'數量','unit_price':'單價','note':'備註','material_id':'材料編號','vendor_id':'廠商編號','document_no':'單據編號','payment_status':'請款狀態','reconciliation_status':'對帳狀態','total':'總金額','vendor':'供貨廠商','material':'材料','item':'項目','amount':'金額','handler':'經手人','code':'機具編號','category':'類別','maintenance':'維修中','status':'狀態','equipment_id':'機具資料編號','borrower':'借用人','loan_date':'借出日期','due_date':'預計歸還日','return_date':'實際歸還日','log_id':'交易編號','equipment_name':'機具名稱'}
    return pd.DataFrame(rows).rename(columns=labels)

def show(rows,key='table'):
    df=frame(rows)
    st.dataframe(df,width='stretch',hide_index=True)
    st.download_button('匯出目前查詢 CSV',df.to_csv(index=False).encode('utf-8-sig'),file_name='工地查詢.csv',mime='text/csv',key=key)

def editor(table,rows,fields,extra=None):
    options={0:'＋ 新增資料',**{r['id']:f"#{r['id']} · {r.get('name',r.get('document_no',r.get('item',r.get('date',r.get('borrower',r.get('code','資料'))))))}" for r in rows}}
    selected=st.selectbox('選擇新增或要修改的紀錄',list(options),format_func=options.get,key=table+'pick')
    old=next((r for r in rows if r['id']==selected),{})
    with st.form(table+str(selected)):
        values={}
        for key,label,kind,choices in fields:
            val=old.get(key)
            if kind=='text': values[key]=st.text_input(label,value=val or '') .strip()
            elif kind=='number': values[key]=st.number_input(label,min_value=0.0,value=float(val or 0),step=1.0)
            elif kind=='date': values[key]=st.date_input(label,value=date.fromisoformat(val) if val else local_today()).isoformat()
            elif kind=='optional_date':
                returned=st.checkbox('已歸還',value=bool(val))
                d=st.date_input(label,value=date.fromisoformat(val) if val else local_today())
                values[key]=d.isoformat() if returned else None
            elif kind=='bool': values[key]=int(st.checkbox(label,value=bool(val) if val is not None else key=='active'))
            else:
                opts=choices
                if not opts: st.warning(f'請先建立{label}'); return
                keys=list(opts) if isinstance(opts,dict) else opts
                values[key]=st.selectbox(label,keys,index=keys.index(val) if val in keys else 0,format_func=(lambda x,mapping=opts:mapping[x]) if isinstance(opts,dict) else str)
        doc=extra(old) if extra else None
        submitted=st.form_submit_button('儲存資料',type='primary')
    if submitted:
        try:
            db.save(table,values,selected or None,document=doc)
            st.session_state.flash='資料已儲存'; st.rerun()
        except (ValueError,sqlite3.Error) as e: st.error(f'無法儲存：{e}')
    if selected:
        confirm=st.checkbox('確認永久刪除此筆資料',key=table+'confirm')
        if st.button('刪除紀錄',disabled=not confirm,key=table+'delete'):
            try:
                db.delete(table,selected); st.session_state.flash='資料已刪除'; st.rerun()
            except sqlite3.Error as e: st.error(f'無法刪除：{e}。已有關聯的廠商請取消「啟用」，有交易的材料與借用紀錄的機具須保留。')

def text(k,l): return (k,l,'text',None)
def num(k,l): return (k,l,'number',None)
def dt(k,l): return (k,l,'date',None)
def sel(k,l,opts): return (k,l,'select',opts)
def flag(k,l): return (k,l,'bool',None)
vendors=db.query('SELECT * FROM vendors ORDER BY id')
materials=db.query('SELECT * FROM materials ORDER BY id')
vmap={v['id']:v['name']+('（停用）' if not v['active'] else '') for v in vendors}
mmap={m['id']:m['name']+' / '+m['unit'] for m in materials}

if page=='首頁 Dashboard':
    stocks=db.stocks(); low=[r for r in stocks if r['stock']<r['min_stock']]
    today=db.query("SELECT COUNT(*) n,COALESCE(SUM(quantity*unit_price),0) total FROM materials_log WHERE direction='進貨' AND date=?",(local_today().isoformat(),))[0]
    cash=db.query('SELECT COALESCE(SUM(amount),0) total FROM petty_cash')[0]['total']
    a,b,c,d,e=st.columns(5)
    a.metric('材料種類',len(stocks)); b.metric('今日進貨筆數',today['n']); c.metric('低庫存材料',len(low)); d.metric('合作廠商',sum(v['active'] for v in vendors)); e.metric('零用金累計支出',f"${cash:,.0f}")
    st.caption(f"今日進貨總金額：${today['total']:,.2f}（不同單位不合併加總數量）")
    if low: st.error('低庫存警示：'+'、'.join(f"{r['name']} {r['stock']:g}{r['unit']}（警戒 {r['min_stock']:g}）" for r in low))
    else: st.success('所有材料庫存充足')
    st.subheader('目前庫存'); show(stocks,'stocks')
    st.subheader('最近進出貨紀錄'); show(db.query('SELECT l.*,m.name material,m.unit,v.name vendor FROM materials_log l JOIN materials m ON m.id=l.material_id LEFT JOIN vendors v ON v.id=l.vendor_id ORDER BY l.date DESC,l.id DESC LIMIT 10'))
    monthly=db.query("SELECT substr(date,1,7) 月份,SUM(amount) 支出 FROM petty_cash GROUP BY substr(date,1,7) ORDER BY 月份")
    if monthly: st.bar_chart(pd.DataFrame(monthly).set_index('月份'))
elif page=='材料基本資料':
    q=st.text_input('搜尋材料名稱'); show([r for r in db.stocks() if q.casefold() in r['name'].casefold()])
    st.caption('低於警戒庫存顯示紅色警示。歷史數量均以材料單位記錄，已有交易請勿變更單位意義。')
    editor('materials',materials,[text('name','材料名稱'),text('unit','單位'),num('min_stock','警戒庫存')])
elif page=='協力廠商名錄':
    q=st.text_input('搜尋名稱、工種、聯絡人或電話'); show([v for v in vendors if q.casefold() in str(v).casefold()])
    editor('vendors',vendors,[text('name','廠商名稱'),sel('trade','工種',['水電','泥作','鋼構','材料供應','其他']),text('contact','聯絡人'),text('phone','電話'),text('tax_id','統編（八位數字或留空）'),text('address','地址'),sel('rating','配合評價',[1,2,3,4,5]),flag('active','啟用')])
elif page=='材料進出貨':
    q=st.text_input('搜尋材料、廠商、日期或備註')
    rows=db.query('SELECT l.*,m.name material,m.unit,v.name vendor FROM materials_log l JOIN materials m ON m.id=l.material_id LEFT JOIN vendors v ON v.id=l.vendor_id ORDER BY l.date DESC,l.id DESC')
    show([r for r in rows if q.casefold() in str(r).casefold()])
    st.info('數量須大於 0。出貨不得超過目前庫存；修改或刪除進貨也會檢查庫存。出貨可不指定廠商。')
    def document(old):
        current=db.query('SELECT * FROM purchase_documents WHERE log_id=?',(old.get('id',-1),))
        d=current[0] if current else {}
        st.caption('以下單據欄位僅在類型為「進貨」時使用，進貨單據編號必填且不可重複。')
        return {'document_no':st.text_input('單據編號',value=d.get('document_no','')).strip(),'payment_status':st.selectbox('請款狀態',['未請款','已請款','已付款'],index=['未請款','已請款','已付款'].index(d.get('payment_status','未請款'))),'reconciliation_status':st.selectbox('對帳狀態',['未對帳','已對帳','有差異'],index=['未對帳','已對帳','有差異'].index(d.get('reconciliation_status','未對帳')))}
    editor('materials_log',rows,[sel('material_id','材料與單位',mmap),sel('vendor_id','供貨廠商',{None:'無（僅出貨適用）',**vmap}),dt('date','日期'),sel('direction','類型',['進貨','出貨']),num('quantity','數量'),num('unit_price','單價'),text('note','備註')],document)
elif page=='進貨單據查詢':
    v=st.selectbox('篩選廠商',[None,*vmap],format_func=lambda x:'全部' if x is None else vmap[x])
    m=st.selectbox('篩選材料',[None,*mmap],format_func=lambda x:'全部' if x is None else mmap[x])
    start=st.date_input('起始日期',date(2000,1,1)); end=st.date_input('結束日期',local_today()); no=st.text_input('單據編號關鍵字')
    rows=db.query('SELECT p.*,l.date,l.material_id,l.vendor_id,m.name material,m.unit,v.name vendor,l.quantity,l.unit_price,l.quantity*l.unit_price total FROM purchase_documents p JOIN materials_log l ON l.id=p.log_id JOIN materials m ON m.id=l.material_id JOIN vendors v ON v.id=l.vendor_id WHERE l.date BETWEEN ? AND ? ORDER BY l.date DESC,l.id DESC',(start.isoformat(),end.isoformat()))
    rows=[r for r in rows if (v is None or r['vendor_id']==v) and (m is None or r['material_id']==m) and no.casefold() in r['document_no'].casefold()]
    show(rows); st.metric('查詢進貨總金額',f"${sum(r['total'] for r in rows):,.2f}")
    if rows:
        picked=st.selectbox('選取單據查看明細',[r['id'] for r in rows],format_func=lambda x:next(r['document_no'] for r in rows if r['id']==x))
        r=next(r for r in rows if r['id']==picked)
        st.write(f"供貨廠商：{r['vendor']} ｜ 材料：{r['material']} ｜ 數量：{r['quantity']:g} {r['unit']} ｜ 單價：{r['unit_price']:g} ｜ 總金額：{r['total']:,.2f}")
        st.caption('單據狀態獨立儲存，不變動材料數量。新增或刪除單據請至材料進出貨，與進貨交易一併處理。')
        with st.form('document_status'):
            docno=st.text_input('單據編號',r['document_no'])
            payment=st.selectbox('請款狀態',['未請款','已請款','已付款'],index=['未請款','已請款','已付款'].index(r['payment_status']))
            reconciliation=st.selectbox('對帳狀態',['未對帳','已對帳','有差異'],index=['未對帳','已對帳','有差異'].index(r['reconciliation_status']))
            submit=st.form_submit_button('儲存單據狀態')
        if submit:
            try:
                db.save('purchase_documents',dict(log_id=r['log_id'],document_no=docno.strip(),payment_status=payment,reconciliation_status=reconciliation),r['id'])
                st.session_state.flash='單據已更新，庫存不變'; st.rerun()
            except (ValueError,sqlite3.Error) as e: st.error(str(e))
elif page=='零用金':
    q=st.text_input('搜尋日期、項目或經手人'); rows=db.query('SELECT * FROM petty_cash ORDER BY date DESC,id DESC'); filtered=[r for r in rows if q.casefold() in str(r).casefold()]
    st.metric('查詢支出合計',f"${sum(r['amount'] for r in filtered):,.2f}"); show(filtered)
    editor('petty_cash',rows,[dt('date','日期'),text('item','項目'),num('amount','金額'),text('handler','經手人'),text('note','備註')])
elif page=='機具管理':
    rows=db.equipment_status(); q=st.text_input('搜尋機具'); show([r for r in rows if q.casefold() in str(r).casefold()])
    editor('equipment',rows,[text('code','機具編號'),text('name','名稱'),text('category','類別'),flag('maintenance','維修中')])
else:
    eq=db.query('SELECT * FROM equipment'); rows=db.query("SELECT l.*,e.name equipment_name,CASE WHEN l.return_date IS NULL THEN '借出中' ELSE '已歸還' END status FROM equipment_loans l JOIN equipment e ON e.id=l.equipment_id ORDER BY l.id DESC")
    q=st.text_input('搜尋機具、借用人、日期或狀態'); show([r for r in rows if q.casefold() in str(r).casefold()])
    st.caption('選取借用紀錄後勾選「已歸還」並填入實際日期，即完成歸還。未歸還或維修中機具不可再借出。')
    editor('equipment_loans',rows,[sel('equipment_id','機具',{e['id']:e['code']+' '+e['name'] for e in eq}),text('borrower','借用人'),dt('loan_date','借出日期'),dt('due_date','預計歸還日'),('return_date','實際歸還日','optional_date',None)])
