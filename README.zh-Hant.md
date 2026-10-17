# Safari 價格監控

[English](README.md)

準備監控條件、維護本機清單，並產生 Safari Notify Me 設定卡。Safari 負責背景檢查與通知；Python 程式只記錄條件、核對證據及歷史，不抓價、不排程、不發通知，也不直接操作 Safari。

**Experimental v0.1.0 prerelease。** Ansel 署名與維護，採 [MIT](LICENSE)。

[下載 v0.1.0](https://github.com/anselbuilds/safari-price-watch/archive/refs/tags/v0.1.0.zip) · [版本說明](https://github.com/anselbuilds/safari-price-watch/releases/tag/v0.1.0) · [安裝與實際使用](#安裝與實際使用)

## 環境

Python 3.9+、SQLite 與系統 IANA 時區資料，僅用標準函式庫。本次以 macOS arm64 的 Python 3.9.6 驗證。實際監控另需提供 Notify Me 的 Mac／Safari、可用的 Apple Intelligence 與 Safari 系統通知；功能依裝置、地區及語言而異。參考 [Apple Notify Me 文件](https://support.apple.com/en-in/guide/safari/ak35p2kk9h5r/mac)。本機 list／show／prompt／handoff 不需要 Safari 或 Computer Use。

## 首次使用，不安裝也可試

在解壓後的 repo 根目錄執行：

```sh
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 add demo-ssd --file skills/price-watch/examples/demo-contract.json
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 handoff demo-ssd
python3 skills/price-watch/scripts/watchlist.py --db runtime/demo/watchlist.sqlite3 show demo-ssd
```

預期仍是 draft，設定卡 action 為 setup、native_action_performed 為 false。重跑同一 id 的 add 會失敗，不覆蓋舊資料。此例是 example.com 合成商品，不要拿去建立 Safari 正式監控。list／show 等指令首次使用也會初始化資料庫。

可請 agent：「讀取 skills/price-watch/SKILL.md，解釋 demo 的設定卡，不操作 Safari、不記 active。」

## 安裝與實際使用

將完整 skills/price-watch 資料夾複製至 agent 支援的 skill 目錄。Codex 專案位置為 .agents/skills/price-watch；個人位置依 [現行文件](https://learn.chatgpt.com/docs/build-skills) 可用 ~/.agents/skills/price-watch，既有環境可能使用 ~/.codex/skills/price-watch，依宿主設定。先保留既有版本，避免覆蓋；最終應直接找到 price-watch/SKILL.md。本版尚未驗證宿主技能選單的自動探索。

全域／個人安裝請明確設定 PRICE_WATCH_DB，或於子指令前加 --db，將資料放在 skill 資料夾外。程式把 .agents/skills 視為專案布局，因此以該位置作個人安裝時也應明定 DB。其他安裝布局使用使用者 state 目錄。詳細格式見 [本機清單操作](skills/price-watch/references/registry.md)。

以 $price-watch 或宿主的技能選單呼叫：

> 替這個商品網址準備監控，固定型號與賣家，一般標價不高於 USD 80、有貨，每日 UTC 09:00。先讀商品頁取得基準，讀不到不要編造。只產生設定卡，由我在 Safari 設定。

設定後重新打開 Safari Edit 核對條件、頻率與時間，agent 親見或使用者明確回報已核對後，才記 active。模糊的「好了」不能當核對證據。修改時先 revise 本機，再編輯原有原生監控；停止時先 request-stop，實際刪除並核對後才記 stopped。

| 狀態 | 意義 |
| --- | --- |
| draft | 僅本機登記 |
| needs_attention | 條件待同步或原生未確認，可能仍執行舊設定 |
| active | 曾核對原生設定，不代表已收到通知 |
| stop_pending | 尚未確認原生停止 |
| stopped | 已核對原生移除，保留歷史 |

通知送達另行記錄。expiry_due 只提示到期，不自動停止。list 不是 Safari 即時全量盤點。不要為測試擅改真實監控門檻。

## 驗收與限制

執行 `python3 -m unittest discover -s tests -v` 重跑合成測試。測試不連網、不碰 Safari 或正式清單，臨時資料放在此 checkout 下。詳見 [VALIDATION.md](VALIDATION.md)。實際通知送達仍未驗證；沒有無介面管理 API、獨立抓價／排程／通知後端。本版不保證 Safari 判價準確性、準時或去重。

資料庫以明文保存網址、條件與證據，分享前排除 runtime、個人清單與瀏覽器資料。agent 讀取內容可能交由模型服務處理；不能因 SQLite 在本機就宣稱完全離線。回報請用合成資料，見 [SECURITY.md](SECURITY.md)。
