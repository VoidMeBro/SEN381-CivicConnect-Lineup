# PED v3.0 — Member 3 Repository and Configuration Evidence

## Section 54: Repository, CI, and Configuration Controls

This section records the repository and configuration controls relevant to the M3 evidence. All four team members confirmed the planned M3 requirements and checks for the local school-project scope. A passing automated check remains evidence for the specific commit it checked.

### 54.1 Repository workflow

Team changes are prepared on a working branch and proposed through a pull request for review before they are merged. The repository's existing GitHub Actions workflow is `.github/workflows/quality.yml`. This section documents that shared workflow rather than adding a second one.

### 54.2 Existing automated checks

The shared workflow runs for pull requests and pushes to `main` and `feat/**`. It uses Python 3.12 and runs from `docs/member1_m2`. Its checks compile the product and tests, run the unittest suite, run the performance smoke scenario, run Bandit, and scan for secrets with Gitleaks. GitHub Actions records the result against the commit it checks. Merge requirements and reviewer approvals are governed by the repository's current settings and the review process; this document does not claim that a specific branch-protection rule is enabled.

### 54.3 Configuration example and secret handling

The root `.env.example` lists the environment variable names read by `docs/member1_m2/product/serve.py`, with development-safe example values and blank secret values. The application reads variables from its process environment; it does not automatically load a `.env` file. The example is therefore a reference for configuring the process, not a promise that copying it to `.env` alone configures the application.

The existing root `.gitignore` excludes local `.env` files, database files, keys, and generated data. The sample `.env.example` remains trackable. Actual passwords, session secrets, and administrator setup tokens must be supplied outside the repository.

### 54.4 Evidence and limitations

The workflow definition is the evidence of which automated checks are configured. The Actions run linked from the relevant pull request is the evidence of the result for a specific commit. The team reviewed the workflow result alongside the application and requirement evidence before approving the local school-project release. The workflow does not enforce a reviewer count by itself; that depends on GitHub repository settings.

## Section 55: Member 3 evidence summary

Member 3's contribution supplies this repository/configuration description, a root-level environment-variable reference, and supporting RTM evidence in `docs/RTM_M3_Member3_CI_Evidence.md`. The project continues to use the repository's existing quality workflow. The team reviewed the integrated M3 requirements and supporting evidence and approved local school-project release readiness on 16 October 2026.
