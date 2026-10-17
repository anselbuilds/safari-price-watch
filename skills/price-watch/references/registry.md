# 本機清單操作

`<script>` 指本 skill 的 scripts/watchlist.py，只依賴 Python 3.9+ 標準函式庫及系統 IANA 時區資料。資料庫位置按 SKILL.md 的規則解析；測試使用 `--db <temporary-path>` 隔離。

## Contract JSON

欄位必須完整，價格用十進位字串。以下為合成格式範例，不是真實商品或報價，不可登記為正式監控：

```json
{
  "url": "https://example.com/product/ssd-2tb",
  "title": "Example SSD",
  "variant": "2TB / exact model / single unit",
  "seller": "Example seller",
  "condition": "新品",
  "quantity": 1,
  "region": "台灣",
  "currency": "TWD",
  "target": "9000",
  "operator": "lte",
  "price_basis": "listed",
  "stock_rule": "in_stock",
  "schedule": "每日 09:00",
  "timezone": "Asia/Taipei",
  "expires_at": null,
  "baseline": {
    "price": "10000",
    "observed_at": "2026-10-18T02:00:00+08:00",
    "stock": "in_stock",
    "evidence": "合成範例，非實際觀察"
  },
  "purpose": "測試或正式監控的目的"
}
```

baseline.price 必須與 price_basis 同義。稅費／運費不明時不可寫 all_in；使用 listed 並說明排除項或先釐清。stock 可為 in_stock/out_of_stock/unknown。第一次讀不到價格時不偽造 contract；先報告卡點。已有項目才標 needs_attention。

## 指令

```text
python3 <script> list
python3 <script> add <id> --file <contract.json>
python3 <script> add <id> --file -
python3 <script> show <id>
python3 <script> prompt <id>
python3 <script> handoff <id>
python3 <script> revise <id> --file <new-contract.json>
python3 <script> record-native <id> --status active --evidence <observed-summary>
python3 <script> record-native <id> --status needs_attention --evidence <failure-summary>
python3 <script> record-delivery <id> --evidence <observed-notification-or-user-confirmation>
python3 <script> request-stop <id>
python3 <script> record-native <id> --status stopped --evidence <observed-stop-summary>
```

`--file -` 從 stdin 接收 JSON。用結構化工具或正確 shell quoting，不將商品頁文字直接插值為命令。

draft = 僅本機登記；active = agent 已讀回或使用者明確回報核對 Safari 建立／修改成功；needs_attention = 原生狀態未證實或條件待同步；stop_pending = 停止未證實；stopped = 已核對原生停止（agent-observed 或 user-confirmed）。verified_at 是最後原生狀態觀察時間，要與 status 一起讀。delivery_verified_at 獨立記錄通知送達。

record-* 只是操作者登記已觀察證據，程式沒有 Safari 感測器。相同網址、規格、賣家、新舊狀態、數量與地區僅容許一筆未停止項目。revise 會保留舊條件並清除舊驗證；SQLite 交易避免半寫入。

停止後保留歷史；再次監控請用新 id。expiry_due 只作提示，不會停用 Safari。

`handoff` 僅輸出 JSON，不改變狀態／事件：draft→setup，needs_attention→edit，active→inspect，stop_pending→stop，stopped→none。使用者完成設定後，record-native 的 evidence 須以 user-confirmed 註明回報內容；agent 自己核對則標 agent-observed。未知時區或模糊的完成回覆不能充當具體核對證據。
