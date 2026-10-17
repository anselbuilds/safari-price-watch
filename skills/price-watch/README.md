# price-watch：可分享的 Safari 價格監控 skill

將 `price-watch` 資料夾放入接收者專案的 `.agents/skills/`，或個人 `~/.codex/skills/`。保留整個資料夾結構；在支援該技能目錄的 agent 中載入。其他 agent 可直接讀 `SKILL.md`，但技能探索與工具名稱依宿主而異。

需求：Python 3.9+ 及 IANA 時區資料。Safari 執行監控另需支援 Notify Me 的 macOS／Safari、Apple Intelligence 和系統通知；本機清單工具本身不需 Safari、Computer Use、API key 或 Python 第三方套件。

## 使用

- `$price-watch 準備這個商品的降價監控，產生設定卡，我自己貼到 Safari。`
- `$price-watch 列出監控及最後核對時間。`
- `$price-watch 把目標價改成 8000，產生待同步的設定卡。`
- `$price-watch 幫我在 Safari 完成設定並核對。`（需宿主提供 Computer Use）

操作本機程式：

```sh
python3 scripts/watchlist.py list
python3 scripts/watchlist.py handoff <watch-id>
```

新增資料的 JSON 格式和完整命令見 `references/registry.md`。價格與時間的例子是合成資料，不能直接當正式監控。

`handoff` 輸出 JSON 設定卡，可由 agent 整理成網址、條件及操作步驟。設定卡不會操作 Safari；使用者完成後回報已核對的條件與頻率，agent 才記錄 user-confirmed 狀態。停止也要在 Safari 實際移除。

專案安裝的清單位於專案 `runtime/price-watch/`；全域安裝在 Mac 使用者 `~/Library/Application Support/price-watch/`。可用 `PRICE_WATCH_DB` 或 `--db` 指定位置。升級 skill 不必搬動清單。

此包只含 skill、程式及文件，不含作者的商品監控、帳戶資料或瀏覽器設定。現行版本沒有 Safari 無介面管理 API 整合、獨立抓價服務或通知後端。公開分享程式不會分享或啟用接收者的 Safari 監控。

個人安裝在 ~/.agents/skills/price-watch 時請明定 PRICE_WATCH_DB 或 --db；程式把 .agents/skills 視為專案布局。CLI 初次查詢也會初始化 DB。完整雙語安裝與合成示例見發布 repo 根目錄 README。

Experimental v0.1.0，Ansel 署名與維護，採 [MIT](LICENSE)。完整[安裝及首次使用](https://github.com/anselbuilds/safari-price-watch/tree/v0.1.0#install-and-use)。一般問題用 [Issues](https://github.com/anselbuilds/safari-price-watch/issues)，敏感漏洞用[私密回報](https://github.com/anselbuilds/safari-price-watch/security/advisories/new)，不承諾回覆時限。
