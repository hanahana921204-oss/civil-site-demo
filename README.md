# 土木工地管理系統｜公開教學展示版

本資料夾為可獨立上傳 GitHub 的 Streamlit Community Cloud 展示專案。完整步驟見 `DEPLOY.md`。

- 入口：`app.py`
- Python：3.12
- 套件：`requirements.txt`（Streamlit、pandas）
- 虛構種子資料：`data/demo_seed.db`
- 工作資料庫：`.runtime_data/demo.db`（首次啟動自動建立，不應上傳 GitHub）
- 繁體中文介面、材料進出貨、廠商、單據、零用金、機具借還及 Dashboard。

所有示範人名皆為角色代稱，五家廠商皆為虛構名稱；電話、統編、地址留空。所有訪客共用同一份展示工作資料，操作可能互相影響。請勿輸入真實個資；**Community Cloud 的 SQLite 本地寫入不保證永久保存**，重建環境後可能回復種子資料，操作不會自動回存 GitHub。

本機預覽（先建立虛擬環境並安裝套件）：

```text
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

隔離測試：`python run_tests.py`。測試只使用暫存工作資料庫，不會修改種子或本機作業資料。
