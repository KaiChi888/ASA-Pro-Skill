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

The root `SKILL.md` exposes the `asa-pro` skill to agents supported by the [skills CLI](https://github.com/vercel-labs/skills).

### Operating logic

- One Apple Search Ads campaign per country.
- Two ad groups: `Broad Discovery` and `Exact Match`.
- Search Match off, Search Results placement, manual CPT.
- Every ad group targets New Users by excluding existing app downloaders.
- Broad search terms that generate downloads are promoted to Exact.
- Exact is created first; then the term becomes an Exact negative in Broad so traffic routes safely.
- Revenue-proven Exact winners can be split into dedicated campaigns.
- Keywords start around USD 1–2, then bids are reduced gradually toward efficient avgCPT.
- Deterministic three-hour harvesting plus daily reasoning-based bid review.
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
9. Seed localized keywords and test `scripts/broad_to_exact.py --dry-run`.
10. Enable three-hour harvesting and daily Exact bid review after two clean dry runs.

See [`SKILL.md`](SKILL.md) and [`references/setup.md`](references/setup.md).

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

根目錄的 `SKILL.md` 會被辨識為 `asa-pro` Skill，可供 [skills CLI](https://github.com/vercel-labs/skills) 支援的 Agent 使用。

### 核心廣告邏輯

- 每個國家建立一個 Apple Search Ads Campaign。
- 每個 Campaign 有 `Broad Discovery` 與 `Exact Match` 兩個 Ad Group。
- 關閉 Search Match，只投 Search Results，採手動 CPT。
- 所有廣告群組都設定為 **New Users**，排除已下載 App 的用戶。
- Broad 搜尋詞產生下載後，提升為 Exact 關鍵字。
- 先確認 Exact 建立成功，再於 Broad 加入同詞 Exact Negative，安全導流到 Exact。
- 有收入、付費訂閱與良好 ROAS 的 Exact 關鍵字，可拆成獨立 Campaign。
- 新關鍵字先用約 **US$1–2** 取得曝光，再依 avgCPT、下載與收入逐步降價。
- 每三小時執行 deterministic Broad → Exact；每天一次由 Agent 綜合 3/7 日資料與 RevenueCat 審查 Exact 出價。
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
9. 加入在地化關鍵字，測試 `scripts/broad_to_exact.py --dry-run`。
10. 連續兩次 dry-run 正確後，再啟用每三小時採集與每日出價審查。

完整流程請看 [`SKILL.md`](SKILL.md) 與 [`references/setup.md`](references/setup.md)。

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
