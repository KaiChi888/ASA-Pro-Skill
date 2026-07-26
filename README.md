# ASA Pro Skill

[English](#english) · [繁體中文](#繁體中文)

A reusable Agent Skill for Apple Search Ads Advanced: country-by-country Broad → Exact, New Users targeting, RevenueCat revenue attribution, and disciplined CPT cost control.

## English

### Install

```bash
npx skills add KaiChi888/ASA-Pro-Skill
```

Install non-interactively for all supported agents:

```bash
npx skills add KaiChi888/ASA-Pro-Skill --all
```

List available skills first:

```bash
npx skills add KaiChi888/ASA-Pro-Skill --list
```

The skill at `skills/asa-pro/SKILL.md` exposes `asa-pro` to agents supported by the [skills CLI](https://github.com/vercel-labs/skills).

### Operating logic

- One Apple Search Ads campaign per country.
- Two ad groups: `Broad Discovery` and `Exact Match`.
- Search Match off, Search Results placement, manual CPT.
- Every ad group targets New Users by excluding existing app downloaders.
- Broad search terms that generate downloads become research candidates, not automatic Exact keywords.
- Before promotion, inspect that keyword's country-specific App Store search results and competitors with the included research tool. Only a current evidence-backed `related` verdict can proceed.
- After approval, Exact is created first; then the term becomes an Exact negative in Broad so traffic routes safely.
- Revenue-proven Exact winners can be split into dedicated campaigns.
- Once daily, the skill ranks possible dedicated-campaign candidates and shows them to the user for `approve`, `hold`, or `reject`; it never splits automatically.
- Keywords start around USD 1–2, then bids are reduced gradually toward efficient avgCPT.
- Deterministic three-hour harvesting plus daily reasoning-based bid review.
- CI validation plus safety/troubleshooting ladders for zero exposure, broken attribution, and partial mutations.
- Apple Ads operations via [`aads`](https://github.com/SaadBelfqih/apple-ads-cli).
- Revenue analysis via [`rc`](https://github.com/SaadBelfqih/rc-cli).

### Zero to running ads

1. Install Go 1.25+.
2. Install `aads`; run `aads configure`.
3. Install `rc`; run `rc configure`.
4. Enable RevenueCat Apple Ads Services and send AdServices attribution from the iOS app.
5. Load `asa-pro` and perform the setup inventory in dry-run mode.
6. Approve target countries and daily budgets.
7. Create one campaign per country with Broad and Exact ad groups.
8. Verify New Users targeting and RUNNING status.
9. Seed localized keywords and use `app_store_relevance.py` to review candidate terms against the top storefront competitors.
10. Save `related`/`ambiguous`/`irrelevant` evidence outside the repo, then test `broad_to_exact.py --dry-run --relevance-file <path>`.
11. Enable three-hour harvesting and daily Exact bid review after two clean dry runs.

See [`skills/asa-pro/SKILL.md`](skills/asa-pro/SKILL.md) and [`skills/asa-pro/references/setup.md`](skills/asa-pro/references/setup.md).

### Mandatory competitor relevance gate

```bash
python3 skills/asa-pro/scripts/app_store_relevance.py \
  --keyword "photo cleaner" --app-id 1234567890 --country US --limit 10
```

The tool queries the country-specific iTunes Lookup/Search APIs and returns the advertised app, top result apps, genres, descriptions, ratings, links, and comparison signals. An agent or human must inspect dominant user intent and record `related`, `ambiguous`, or `irrelevant`; the heuristic suggestion never auto-approves. `broad_to_exact.py --apply` now refuses to run without a current approval file, and only `related` terms can be mutated. See [`competitor-relevance.md`](skills/asa-pro/references/competitor-relevance.md).

ASA Pro also includes the machine's URL/browser research workflow: Google/Bing/DuckDuckGo or agent web search when useful, country-specific iTunes Search/Lookup URLs, direct App Store product pages, `aads apps search`, and Sensor Tower public overview URLs. If a search engine returns CAPTCHA/Cloudflare, it switches to direct sources instead of trying to bypass the block. Source URL, storefront, retrieval date, and visible evidence must be recorded; snippets alone cannot approve relevance.

The preferred visual keyword check is Apple's own iPhone App Store search URL. Replace `us` with the campaign country and URL-encode the keyword:

```text
https://apps.apple.com/us/iphone/search?term=keyword
```

Inspect Apple's ranked top 5–10 apps on this page before approving Broad → Exact. The included research script also returns this URL as `app_store_search_url`.

### Daily dedicated-campaign decision queue

Once per day, ASA Pro reviews Exact keywords using 30–60-day Apple Ads and RevenueCat evidence plus 3/7/14-day trends. It displays only actionable `scale independently` or `isolate for cost control` candidates, including spend, installs, CPI, paid customers, revenue/ROAS basis, attribution coverage, proposed campaign/bid, budget redistribution versus expansion, migration plan, and rollback. The user chooses `approve`, `hold`, or `reject` per immutable candidate ID. No campaign is split, no budget is moved, and no source keyword is paused without explicit approval. See [`daily-dedicated-campaign-review.md`](skills/asa-pro/references/daily-dedicated-campaign-review.md).

### CLI installation

```bash
mkdir -p "$HOME/tools" "$HOME/.local/bin"
export GOBIN="$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

git clone https://github.com/SaadBelfqih/apple-ads-cli.git "$HOME/tools/apple-ads-cli"
make -C "$HOME/tools/apple-ads-cli" install

git clone https://github.com/SaadBelfqih/rc-cli.git "$HOME/tools/rc-cli"
make -C "$HOME/tools/rc-cli" install

aads version
rc version
```

> Both CLIs are unofficial/alpha tooling. Pin reviewed commits in production and verify every write with a fresh read.

### Security

Never commit Apple private keys, private account IDs, RevenueCat secret keys, customer exports, or local CLI configs. This repository contains placeholders only.

---

## 繁體中文

### 安裝 Skill

```bash
npx skills add KaiChi888/ASA-Pro-Skill
```

非互動安裝到所有支援的 Agent：

```bash
npx skills add KaiChi888/ASA-Pro-Skill --all
```

安裝前先列出 Skill：

```bash
npx skills add KaiChi888/ASA-Pro-Skill --list
```

根目錄下 `skills/asa-pro/SKILL.md` 會被辨識為 `asa-pro` Skill，可供 [skills CLI](https://github.com/vercel-labs/skills) 支援的 Agent 使用。

### 核心廣告邏輯

- 每個國家建立一個 Apple Search Ads Campaign。
- 每個 Campaign 有 `Broad Discovery` 與 `Exact Match` 兩個 Ad Group。
- 關閉 Search Match，只投 Search Results，採手動 CPT。
- 所有廣告群組都設定為 **New Users**，排除已下載 App 的用戶。
- Broad 搜尋詞產生下載後只會成為「待調研候選」，不會自動提升為 Exact。
- 提升前必須查該國 App Store 搜尋結果與競品；只有具證據且仍有效的 `related` 判定才能繼續。
- 核准後先確認 Exact 建立成功，再於 Broad 加入同詞 Exact Negative，安全導流到 Exact。
- 有收入、付費訂閱與良好 ROAS 的 Exact 關鍵字，可拆成獨立 Campaign。
- 每天一次審查可能需要獨立 Campaign 的候選詞，顯示給使用者選擇 `approve`、`hold` 或 `reject`，不會自動拆分。
- 新關鍵字先用約 **US$1–2** 取得曝光，再依 avgCPT、下載與收入逐步降價。
- 每三小時執行 deterministic Broad → Exact；每天一次由 Agent 綜合 3/7 日資料與 RevenueCat 審查 Exact 出價。
- 內建 CI 驗證、安全護欄，以及零曝光、歸因中斷、部分寫入失敗的排查流程。
- Apple Ads 操作用 [`aads`](https://github.com/SaadBelfqih/apple-ads-cli)。
- RevenueCat 收入歸因用 [`rc`](https://github.com/SaadBelfqih/rc-cli)。

### 從零開始搭建

1. 安裝 Go 1.25 以上。
2. 安裝 `aads`，執行 `aads configure`。
3. 安裝 `rc`，執行 `rc configure`。
4. 在 RevenueCat 啟用 Apple Ads Services，並由 iOS App 傳送 AdServices 歸因。
5. 載入 `asa-pro`，先以 dry-run 盤點帳戶。
6. 由使用者確認國家與每日預算。
7. 每國建立 Campaign、Broad 與 Exact 群組。
8. 驗證 New Users targeting 與 RUNNING 狀態。
9. 加入在地化關鍵字，以 `app_store_relevance.py` 對待提升詞查詢該國前幾名競品。
10. 將 `related`／`ambiguous`／`irrelevant` 與證據存於 Repo 外，再測試 `broad_to_exact.py --dry-run --relevance-file <path>`。
11. 連續兩次 dry-run 正確後，再啟用每三小時採集與每日出價審查。

完整流程請看 [`skills/asa-pro/SKILL.md`](skills/asa-pro/SKILL.md) 與 [`skills/asa-pro/references/setup.md`](skills/asa-pro/references/setup.md)。

### 強制競品相關性 Gate

```bash
python3 skills/asa-pro/scripts/app_store_relevance.py \
  --keyword "photo cleaner" --app-id 1234567890 --country US --limit 10
```

工具會查詢指定國家的 iTunes Lookup／Search API，輸出被投放 App、搜尋結果前幾名 App、類別、描述、評分、連結與比對訊號。Agent 或人工必須依主要使用者意圖判斷 `related`、`ambiguous` 或 `irrelevant`；工具的 heuristic 建議不會自動核准。現在 `broad_to_exact.py --apply` 沒有有效審查檔就會拒絕寫入，而且只有 `related` 能建立 Exact 與 Broad Negative。詳見 [`competitor-relevance.md`](skills/asa-pro/references/competitor-relevance.md)。

ASA Pro 也已納入這台設備的網址／Browser 競品研究流程：需要時使用 Google、Bing、DuckDuckGo 或 Agent 網頁搜尋，搭配指定國家的 iTunes Search／Lookup URL、App Store 商品頁、`aads apps search` 與 Sensor Tower 公開 Overview URL。遇到 CAPTCHA／Cloudflare 時不嘗試繞過，直接改用 API 與直接網址。審查要保存來源 URL、Storefront、取得日期與實際可見證據；只有搜尋摘要不能核准相關性。

關鍵字的首選視覺檢查方式是 Apple 自己的 iPhone App Store 搜尋網址。將 `us` 換成 Campaign 國家，並將關鍵字 URL encode：

```text
https://apps.apple.com/us/iphone/search?term=keyword
```

核准 Broad → Exact 前，必須檢查這個頁面由 Apple 排出的前 5–10 個 App。競品查詢腳本也會在 `app_store_search_url` 欄位回傳此網址。

### 每日獨立 Campaign 決策清單

ASA Pro 每天一次以 30–60 日 Apple Ads／RevenueCat 證據，加上最近 3／7／14 日趨勢，審查所有 Exact 關鍵字。例行報告只顯示可執行的 `scale independently` 或 `isolate for cost control` 候選，包含花費、下載、CPI、付費客戶、收入／ROAS 口徑、歸因覆蓋率、建議 Campaign／出價、預算是重新分配或擴張、遷移與回滾方案。使用者依不可變 Candidate ID 選擇 `approve`、`hold` 或 `reject`。沒有明確核准前，不建立 Campaign、不移動預算，也不暫停來源關鍵字。詳見 [`daily-dedicated-campaign-review.md`](skills/asa-pro/references/daily-dedicated-campaign-review.md)。

### CLI 安裝

```bash
mkdir -p "$HOME/tools" "$HOME/.local/bin"
export GOBIN="$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

git clone https://github.com/SaadBelfqih/apple-ads-cli.git "$HOME/tools/apple-ads-cli"
make -C "$HOME/tools/apple-ads-cli" install

git clone https://github.com/SaadBelfqih/rc-cli.git "$HOME/tools/rc-cli"
make -C "$HOME/tools/rc-cli" install

aads version
rc version
```

> 兩套 CLI 都是非官方／早期版本工具。正式環境建議固定已審查的 commit；所有寫入完成後都要重新讀取驗證。

### 安全提醒

不要提交 Apple 私鑰、私有帳戶 ID、RevenueCat Secret Key、客戶資料或本機 CLI 設定。本 Repo 只含 placeholder。

## License

MIT — see [`LICENSE`](LICENSE).
