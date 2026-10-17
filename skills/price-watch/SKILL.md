---
name: price-watch
description: 管理 Safari Notify Me 商品價格與補貨監控的條件及本機清單，產生可手動貼上的設定卡，或按需透過 Computer Use 完成 Safari 設定。適用於持續追蹤、修改門檻、列出或停止監控；單次查價不需此 skill。
---

# Safari 價格監控

Safari 負責背景檢查及通知；本 skill 負責準備條件、維護本機清單與核對設定。Python 程式不抓價、不排程，也不會替 Safari 建立或停止監控。

## 選擇操作方式

- **本機操作**：列出、查歷史、產生條件及設定卡不需要 Computer Use。修改本機條件後須明說「待同步 Safari」，不能當成原生已更新。
- **設定卡**：使用者希望減少介面操作、自己設定，或環境沒有 Computer Use 時，用 `handoff` 輸出網址、可貼上的條件、頻率及操作步驟。把所需操作一次交付；完成前保留 draft／needs_attention／stop_pending。
- **代操作**：使用者要求 agent 完成 Safari 新增、修改或停止且有工具時，按需讀 [Safari 操作](references/safari-ui.md)，完成後讀回驗證。沿用已有授權，不每次重問。平時查本機資料不用啟動瀏覽器。

截至 2026-10-18 查閱的官方文件未找到 Notify Me 管理 API；不要把 Shortcuts 的通用 CLI 當成已存在的 Safari 監控 API。未來若有公開介面，先核實能力再使用，不操作 Safari 私有資料庫。

## 本機入口與分享

`skill_dir` 是本檔所在目錄。執行 `python3 <skill_dir>/scripts/watchlist.py list`；寫入及設定卡讀 [本機清單操作](references/registry.md)。Python 3.9+，只需標準函式庫；系統須提供 IANA 時區資料。

資料庫路徑優先序：`--db` → `PRICE_WATCH_DB` → 安裝在 `.agents/skills/price-watch` 時所屬 workspace 的 `runtime/price-watch/watchlist.sqlite3` → Mac 使用者的 `~/Library/Application Support/price-watch/watchlist.sqlite3`（其他系統用使用者 state 目錄）。分享整個 skill 資料夾即可；不要包含 runtime、個人清單或瀏覽器設定。安裝說明見 [README](README.md)。

## 條件與基準

先查清單避免重複。固定型號、規格、賣家、新舊、數量、地區與幣別。SSD 容量、RAM 的單條 64GB／2×32GB 不可混比。目標採 lt（低於）或 lte（不高於）；listed 是一般標價，all_in 才含必要運費與稅費。會員價、回饋、折價券及分期每期金額不當一般標價。

以可用的網頁讀取工具、使用者提供的實際觀察或按需瀏覽器讀取核對商品頁，保存來源與時間。搜尋摘要不能單獨當基準。讀取失敗不當成零元或缺貨，亦不修改購物車查價。

沒有頻率時可明說採每日一次；時區使用使用者或環境已知設定，未知才詢問，不把範例的 Asia/Taipei 當所有人的預設。到期日未指定則留空。

## 狀態與驗證

- add 保存 draft。設定卡不會啟用監控。
- revise 保留舊條件，轉 needs_attention 並清除舊驗證；原生可能仍執行舊條件。編輯同一項目，避免重複建立。
- 只有讀回 Safari 條件／頻率，或使用者明確回報已核對這些內容，才能 record-native active。證據須標明 agent-observed 或 user-confirmed 及實際內容；含糊的「好了」不足以證明條件已正確同步。
- request-stop 後保留 stop_pending；原生刪除及核對成功才記 stopped。本機狀態變更或關閉分頁不代表停止。
- list 是已登記項目的最後已知狀態，不是 Safari 即時全量盤點。顯示驗證時間、證據來源及通知是否送達。
- expiry_due 僅提示到期，沒有背景停止器；不能承諾自動停止。

通知送達與設定完成分開記錄；只有實際通知或使用者確認收到才 record-delivery。不得擅改正式門檻做通知測試。Safari 原生 AI 的精確判斷、準時檢查、去重及完整歷史未由本 skill 保證。通知是查價線索；重新核對頁面再作購買決定，skill 不下單。

使用者要求完全不依賴 Safari／Computer Use 時，說明需要另選可程式化的抓價與排程後端；本版本不能完成該能力，不把設定卡當作無介面自動監控。不另建重複排程或轉送通知到其他服務。
