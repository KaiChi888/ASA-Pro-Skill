# Security policy

## Secrets never belong in this repository

Do not commit, paste into issues, include in cron prompts, or attach to reports:

- Apple Search Ads private keys (`.pem`, `.p8`, `.key`), client credentials, or signed tokens;
- RevenueCat secret API keys;
- GitHub, model-provider, or other API tokens;
- `~/.aads/config.yaml`, `~/.aads/rc-cli.yaml`, `.env`, `auth.json`, customer exports, or filled local approval/state files.

Only placeholders and public examples belong in the skill. Keep real credentials in local mode-`0600` files outside the repository and use least-privilege/read-only access whenever possible.

## Safer installation

`npx` executes a third-party installer with your user permissions. Prefer a reviewed, pinned installer and release; disable installer telemetry and npm lifecycle scripts:

```bash
DO_NOT_TRACK=1 npm_config_ignore_scripts=true \
  npx --yes skills@1.5.20 add \
  'KaiChi888/ASA-Pro-Skill#v1.2.3' --skill asa-pro
```

Do not run an unpinned `npx` command in an environment containing broadly exposed credentials. The reviewed `skills` installer does not execute the Skill's Python scripts during installation, but future unpinned npm releases are outside this repository's control.

## Local permissions

```bash
umask 077
chmod 700 "$HOME/.aads"
chmod 600 "$HOME/.aads/config.yaml" "$HOME/.aads/rc-cli.yaml" /path/to/private-key.pem
```

The bundled scripts write state and research output with mode `0600`, reject output/state symlinks where the operating system supports `O_NOFOLLOW`, redact common secret patterns from CLI error messages, and use a non-blocking process lock for Broad → Exact.

## Automated checks

CI runs Gitleaks against both the checked-out directory and Git history. Before release, also run:

```bash
go run github.com/zricethezav/gitleaks/v8@v8.30.1 dir . --no-banner --redact
go run github.com/zricethezav/gitleaks/v8@v8.30.1 git . --no-banner --redact
```

Always use `--redact` when scanning or sharing reports.

## If a credential is exposed

1. Revoke/rotate it immediately at Apple, RevenueCat, GitHub, or the relevant provider. History rewriting is not a substitute for rotation.
2. Pause affected automation until the replacement credential is installed.
3. Remove the value from the working tree and all Git history/refs.
4. Re-run Gitleaks against the directory and full history.
5. Review access logs and affected Apple Ads mutations or RevenueCat reads.
6. Never paste the leaked value into an issue, commit message, chat, or remediation report; refer to it as `[REDACTED]`.

## Reporting a vulnerability

Report security issues privately to the repository owner. Include affected file/commit and reproduction steps, but never include a live credential value.
