# M3 Supporting RTM Evidence — Repository and Configuration

This document provides supporting evidence rows for team review and transfer into the maintained project RTM. It does not replace the authoritative RTM or claim that CI alone proves requirement acceptance.

## Evidence references

- Shared workflow: `.github/workflows/quality.yml`
- Configuration reference: `.env.example`
- Runtime environment-variable handling: `docs/member1_m2/product/serve.py`
- Secret and local-file exclusions: root `.gitignore`
- CI result: the GitHub Actions checks attached to the relevant pull request commit

## Supporting evidence rows

| Control / requirement area | Verification criterion | Evidence in repository | Status and boundary |
|---|---|---|---|
| Build and regression checks | Compile the product and tests and run the unittest suite for a pull request commit. | `.github/workflows/quality.yml`; linked GitHub Actions run | Configured in the shared workflow. Each run applies only to its checked commit. |
| Performance smoke check | Run the repository's performance smoke scenario. | `.github/workflows/quality.yml`; `docs/member1_m2/product/performance_smoke.py` | Configured as a smoke scenario; does not establish production-scale capacity. |
| Static and secret scanning | Run Bandit and Gitleaks on the checked repository revision. | `.github/workflows/quality.yml`; linked GitHub Actions run | Configured. These tools have defined detection limits and do not prove the absence of every vulnerability or secret. |
| Configuration documentation | Document the environment variables consumed by the application without committing credentials. | `.env.example`; `docs/member1_m2/product/serve.py`; root `.gitignore` | Reference file is present at the repository root. The application reads process environment variables and does not automatically load `.env`. |
| Repository review process | Propose changes through a pull request and review them before merge. | Pull request history and repository settings | The PR process is used. Any required approval count or merge gate must be confirmed in the current GitHub settings. |

## Limits

These rows describe configured checks and file-level evidence. All four team members reviewed the integrated M3 requirements and evidence and approved local school-project readiness on 16 October 2026. The Actions run applies to the specific commit it checked; hosted production readiness is outside the approved scope.
