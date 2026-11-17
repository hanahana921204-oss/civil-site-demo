# Streamlit Community Cloud 公開展示部署說明

本文件適用於本專案的獨立展示資料夾 `cloud_demo`。檔案準備完成不代表已公開：目前尚未建立 GitHub repository、未上傳檔案，也未部署公開網址。以下步驟由你登入帳號後操作。

## 1. 本機版與展示版的分隔

|用途|位置|處理方式|
|---|---|---|
|目前已測試成功的本機資料|原專案 `data/site_management.db`|完全保留，不讀取來產生展示資料、不重建、不覆蓋，也不要上傳|
|公開展示程式|`cloud_demo/app.py`、`cloud_demo/database.py`|已複製目前功能並調整展示初始化與提示，後續修改本機版不會自動同步|
|展示種子資料庫|`cloud_demo/data/demo_seed.db`|從程式內的虛構範例重新產生，供公開部署使用|
|展示工作資料庫|`cloud_demo/.runtime_data/demo.db`|首次啟動由種子建立；重新整理保留操作；不提交到 GitHub|

種子內容：5 家示範廠商、4 種材料、8 筆進出貨、4 筆進貨單據、2 筆零用金、3 台機具、2 筆借還紀錄。模板低庫存、未歸還機具與已歸還紀錄可供老師操作檢查。廠商名稱來自固定虛構清單，聯絡人使用「示範窗口」，電話、統編及地址全部留空；借用人與經手人使用示範角色稱呼。沒有複製本機測試時輸入的資料。

## 2. 要上傳哪些檔案

建議建立一個全新的 GitHub repository，只放 `cloud_demo` **裡面的內容**，不是整個原作業資料夾，也不是完整作業 ZIP。

```text
新 GitHub repository 根目錄/
  app.py
  database.py
  demo_runtime.py
  requirements.txt
  README.md
  DEPLOY.md
  DEPLOY_CHECK.md
  run_tests.py
  test-output.txt
  .gitignore
  .streamlit/
    config.toml
  data/
    demo_seed.db
  tests/
    test_demo.py
```

不要上傳原本的 `data/site_management.db`、`.runtime`、`.venv`、`__pycache__`、`.runtime_data`、`delivery`、作業 ZIP、任何 `secrets.toml` 或真實聯絡資料。展示專用 ZIP 只含上述允許的部署檔案，可先解壓縮再選檔上傳；不要把 ZIP 本身當作 Streamlit 程式入口。

## 3. GitHub 網頁上傳（建議第一次使用者採用）

1. 登入 [GitHub](https://github.com/)，右上角「＋」→「New repository」。
2. Repository name 可填 `civil-site-demo`；Description 可填「土木工地管理系統課程公開展示」。
3. 為了讓老師直接查看程式，可選 Public。確認只會放上述虛構資料；若課程要求原始碼不公開，先選 Private，並依 Community Cloud 帳號提供的 repository 權限與分享設定操作。
4. 勾選新增 README，建立 repository，預設分支建議使用 `main`。
5. 進入 repository 的 Code 頁面，選「Add file」→「Upload files」。
6. 先將本專案 `delivery/Streamlit_公開展示版.zip` 解壓到新的資料夾，再將解壓後的檔案與子資料夾拖到上傳區。ZIP 根目錄已放好 app.py，且排除了測試時生成的快取。也可自行從本機 `cloud_demo` 選取上方清單的檔案，但不要選到測試快取。**不要拖整個原作業資料夾，也不要直接上傳 ZIP 本身。**
7. 上傳預覽中確認 `app.py` 直接位於 repository 根目錄，並且有 `data/demo_seed.db`、`.streamlit/config.toml` 與 `.gitignore`。若跳過同名 README，可於 GitHub 刪除預設 README 再上傳展示版 README，或在上傳提交中更新它。
8. 輸入 commit message「準備土木工地教學展示版」，按「Commit changes」。
9. 完成後在 Code 頁面再次檢查檔案位置。`.gitignore` 不會自動阻止網頁手動上傳，也不能移除已追蹤的檔案，因此請確實核對上傳清單。

若拖曳時 GitHub 忽略點開頭的資料夾，可用「Add file」→「Create new file」，在檔名輸入 `.streamlit/config.toml`，貼入本機相同內容並提交；`.gitignore` 同理。`demo_seed.db` 是二進位檔案，須透過 Upload files 上傳，不可複製貼上成文字。

也可用 GitHub Desktop：將**只有展示內容**的新資料夾加入新 repository，檢查 Changes 清單後 Commit，再 Publish repository。不要把原始專案直接整包 Publish。

## 4. Streamlit Community Cloud 部署

1. 開啟 [Streamlit Community Cloud](https://share.streamlit.io/)，登入並依畫面連接 GitHub 帳號，授權存取剛建立的展示 repository。
2. 點「Create app」，選已有程式的部署方式（畫面可能顯示「Yup, I have an app」）。
3. 選你的 repository，例如 `你的帳號/civil-site-demo`。
4. Branch 選 `main`。
5. Main file path 填 `app.py`，大小寫須完全相同。
6. 可選擇 App URL 子網域；實際名稱必須尚未被使用，系統會產生 `https://某個名稱.streamlit.app` 網址。
7. 開啟「Advanced settings」，Python version 選 **3.12**，與本機驗證版本一致。此專案不需要外部帳密，Secrets 保持空白。不要填真實廠商資訊。
8. 儲存設定並點「Deploy」。等待安裝完成，若失敗可在部署紀錄查看原因。
9. 成功後開啟公開網址，確認左側出現「公開教學展示」提示，包含「不保證永久保存」。
10. 檢查 App 的分享／可見性設定，讓老師可透過連結查看；用瀏覽器無痕視窗開啟測試，確認不需要你的登入狀態。若仍需登入，調整該 App 的分享設定，而不是把登入帳密交給老師。

以上是將 `cloud_demo` 的內容上傳到新 repository 根目錄的方式。若你選擇保留外層資料夾，入口須改填 `cloud_demo/app.py`，相應檔案也須全部位於同一 `cloud_demo` 中；requirements.txt 已放在入口同層。不要誤選原作業的根目錄 app.py。

## 5. 部署後給老師前的檢查

- 首頁顯示四種材料、五家合作廠商、模板低庫存。初始「今日進貨」可能為 0，因種子交易日期為資料生成日；這是正常結果，可以新增一筆今天的虛構進貨展示。
- 進貨增加庫存，出貨減少庫存；嘗試超量出貨時應拒絕。
- 依單據查詢廠商、數量、單價與金額；修改對帳狀態不改庫存。
- 零用金初始總額為 300；新增示範支出後統計更新。
- 雷射水平儀借出中、電鑽可借用且有已歸還紀錄、切割機維修中。
- 廠商電話、統編、地址應空白。測試新增時只用「示範」名稱，不輸入真實資料。
- 重新整理頁面，確認本次服務仍存在時的操作保留；不要把這項檢查解讀為跨重建永久保存。

## 6. SQLite 保存限制（必須告知老師）

Community Cloud 的本地檔案儲存**沒有持久化保證**，本展示版不宣稱可以永久保存資料。即使 SQLite 寫入成功，也只代表當下工作環境中的檔案已儲存。

- 所有訪客共用同一份工作資料，不是每人獨立帳戶；別人的新增、修改或刪除可能出現在你的畫面。
- App 重新執行或瀏覽器重新整理不會主動覆蓋已存在的工作資料庫。
- 若平台在重新部署、休眠重建、環境回收等情況移除本機工作檔案，先前操作可能遺失。程式發現工作資料庫不存在時，會重新從虛構種子建立。
- 不保證每次重啟都會重設，也不保證會保留；依平台當次檔案系統狀態而定。
- 網頁操作不會更新 GitHub 的 `demo_seed.db`，CSV 匯出只包含查詢資料，不是完整資料庫備份。
- 本版沒有帳號權限功能，僅供課程公開示範。需要正式工地資料保存時，應選用可持久化的資料庫服務或持久磁碟主機、登入與備份機制；這屬於後續正式版工程。

如果展示資料被其他人改動，可先在 App 管理介面停止服務後由維護者處理**展示工作檔案**，再重新建立環境；單純 Reboot 不保證清除工作檔。想保證取得全新種子展示，可從相同 repository 另建新 App。不要刪除或覆蓋原作業資料庫。

## 7. Linux 相容與套件說明

`app.py`、`database.py`、`demo_runtime.py` 全部使用 Python、Streamlit、SQLite 與 pathlib；不呼叫 Windows API、BAT、PowerShell、桌面軟體或本機絕對路徑。讀取路徑由 `Path(__file__).resolve().parent` 推導，與啟動工作目錄無關；檔名採小寫英文，GitHub 路徑使用 `/`。日期以 Asia/Taipei 計算，避免雲端 UTC 導致「今日」日期不同。

requirements.txt 僅列實際直接使用的第三方套件 Streamlit 與 pandas，固定為已驗證版本。sqlite3、pathlib、threading、zoneinfo 等為 Python 標準函式庫，不需寫進 requirements.txt，也不需要 packages.txt。本地文件製作工具及 Windows 啟動批次檔均未放入展示部署包。

已在目前 Windows 的 Python 3.12 環境進行展示專用隔離測試及程式碼相容性檢查；尚未在實際 Linux Community Cloud 執行部署，最終以部署紀錄與老師開啟網址的驗證為準。

## 8. 常見錯誤

|狀況|檢查方式|
|---|---|
|找不到 app.py|檢查 GitHub 根目錄與 Main file path，區分 app.py 和 cloud_demo/app.py|
|缺少 demo_seed.db|確認 data/demo_seed.db 已透過二進位檔案上傳；檢查大小寫與目錄層級|
|ModuleNotFoundError|確認入口同層存在 requirements.txt、database.py、demo_runtime.py|
|套件版本安裝失敗|先確認 Advanced settings 使用 Python 3.12，再查看 build logs；不要任意加入 Windows 套件|
|資料看似恢復初始值|平台可能重建環境；此展示版不提供永久保存保證|
|看到「資料永久保存於 data/site_management.db」|選到了本機版入口；請改用獨立展示 repository 的 app.py|

## 9. 官方參考（2026-11-17 查核）

- [部署入口、repository、分支、Python 設定](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [requirements.txt 與 Linux 套件依賴](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [檔案組織方式](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
- [本地 SQLite 不保證持久化](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)
