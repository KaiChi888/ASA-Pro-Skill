# Setup: Apple Ads + RevenueCat

## 1. Prerequisites

- Apple Search Ads Advanced account.
- API user with minimum roles for intended reads/writes.
- RevenueCat project and v2 read-only secret.
- Go 1.25+ and Git.
- iOS app using RevenueCat and AdServices attribution.

## 2. Install CLIs

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

Pin reviewed commits in production.

## 3. Configure Apple Ads

In Apple Search Ads > Settings > API, create an API user, generate/upload an EC P-256 key pair, and collect Client ID, Team ID, Key ID, Organization ID, and private key PEM path.

```bash
aads configure
aads acls me
aads acls list
aads apps search --query "YOUR APP"
aads campaigns list --all -o table
```

The config is `~/.aads/config.yaml`. Keep it and the PEM out of Git; restrict file permissions.

```bash
umask 077
chmod 700 "$HOME/.aads"
chmod 600 "$HOME/.aads/config.yaml" /path/to/apple-ads-private-key.pem
```

Never pass private-key contents, Apple client secrets, or API tokens on command lines, in cron prompts, or in copied debug output. Configure them interactively or in local mode-0600 files only.

## 4. Configure RevenueCat

Create a RevenueCat v2 secret with read-only access to charts/metrics, customers/attributes, apps, subscriptions, and purchases.

```bash
rc configure
rc projects list -o table
rc apps list -o table
rc metrics overview -o table
```

The default config is `~/.aads/rc-cli.yaml`. For multiple projects, use separate mode-0600 configs and switch explicitly; never commit them. Do not run or share config-display commands unless you have verified that the CLI redacts secrets.

```bash
chmod 600 "$HOME/.aads/rc-cli.yaml"
```

## 5. Verify ASA attribution—not merely revenue

RevenueCat can show revenue with zero Apple Ads keyword attribution. Before ROAS decisions:

1. Enable RevenueCat Apple Ads Services/Advanced integration with read-only Apple Ads access.
2. Ensure the iOS app collects and forwards Apple's AdServices attribution token promptly after install.
3. Start small:

```bash
rc keyword-revenue --limit 100 -o json
rc campaign-roi --limit 100 -o json
```

If no ASA rows appear, label coverage **unverified** and do not claim keyword/campaign ROAS. Large customer scans can take minutes.

## 6. Inventory before writes

```bash
aads campaigns list --all -o json
aads adgroups find-all --all -o json
```

Record organization, app/`adamId`, country/currency, IDs/status/reasons, budget, Search Match, New Users targeting, all active/paused keywords and negatives, and recent 3/7/30-day spend/install/CPI/avgCPT. Do not mutate until scope, countries, budget, and currency are explicit.

## 7. Configure the competitor relevance gate

Copy `templates/relevance-approvals.json` to a private local path such as `~/.aads/asa-pro-relevance.json`. For each Broad performance candidate, run `scripts/app_store_relevance.py` with the campaign country and Adam ID, inspect the top App Store competitors, and record `related`, `ambiguous`, or `irrelevant` with evidence. Never store private account IDs or review files in this repository. `broad_to_exact.py --apply` requires the local file and accepts only a current country/app-matched `related` review.
