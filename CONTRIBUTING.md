# Contributing Guide

## Branch and Review Expectations

1. Create feature branches from `master`.
2. Open pull requests with clear scope and test evidence.
3. Keep commits focused and reversible.
4. Require code owner review for protected paths.

## Local Validation Checklist

Run before opening a pull request:

```bash
make lint
make test
make phase7-latency
```

If your change touches SLA monitoring or compliance exports, also run:

```bash
make phase7-reprocess
```

## Required Pull Request Content

Include:
- summary of behavioral impact,
- test/validation output,
- rollback approach for risky changes,
- documentation updates where applicable.

## Security and Secrets

- Never commit credentials or personal tokens.
- Use environment variables and local secret files excluded by `.gitignore`.
- Report vulnerabilities through the security policy process in `SECURITY.md`.
