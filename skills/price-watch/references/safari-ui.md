# Safari 原生操作（按需讀取）

前置條件：支援 Notify Me 的 Safari／macOS、可用的 Apple Intelligence 及 Safari 系統通知。功能依版本、裝置、語言與地區而異；不要為了本 skill 自動改變系統語言或接受新條款。

使用環境提供的 Computer Use 工具，例如 `cua_repl`，先讀當前工具文件。沒有工具時交付 handoff 設定卡，不假裝已執行。

1. 在 Safari 開啟已核對的商品網址。新項目用 Page Menu → Notify Me；已有項目用監控橫幅 Edit。
2. 貼上 prompt／handoff 條件。頻率透過 Edit 設定；核對 Mac 當前時區與約定時區，必要時換算，不更改系統時區。
3. 若明示缺 Safari 系統通知，依使用者的通知要求及當前工具權限規則處理；不要順帶開放網站推播或其他 app 通知。
4. 儲存後重新打開 Edit，核對網址、規格、門檻、頻率與時間，才記 active。不能確認時記 needs_attention 並指出具體卡點。
5. 停止使用原項目 Edit → Delete，依環境適用的確認規則操作；驗證該監控已移除才記 stopped。不要清除 Safari 個人資料。

實機經驗：Page Menu popover 可能未出現在差異 AX 樹，查看完整 AX 樹找 NotifyMeWhenButton。解析中 Done 可能變成 Next，勿連續點擊忙碌按鈕。長句停滯時可保留語義改寫較短條件，再依畫面回報處理前置條件；有針對性的重試仍失敗就交付設定卡與卡點。

## 已查證的介面範圍（2026-10-18）

- [Apple Notify Me 文件](https://support.apple.com/en-in/guide/safari/ak35p2kk9h5r/mac)：說明 Page Menu、條件欄和 Edit 頻率設定。
- [Apple Shortcuts CLI 文件](https://support.apple.com/en-gb/guide/shortcuts-mac/apd455c82f02/mac)：可執行既有捷徑，不代表可直接新增／修改 Safari Notify Me。
- 本次檢查 Safari 27.0.1 的公開 scripting dictionary，未見 Notify Me 管理命令。這是有限範圍查證，不是宣稱所有版本皆無 API。
