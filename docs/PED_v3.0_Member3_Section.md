# PED v3.0 — Member 3 Sections

## Section 54: Repository, CI, and Configuration (M3)

This section documents the repository controls, continuous integration pipeline, and configuration management that support the M3 release candidate. These controls provide evidence that changes are reviewed, verified, and controlled before they enter the main branch.

### 54.1 Repository Structure and Branch Strategy

The CivicConnect repository maintains a protected main branch that serves as the controlled product state. Substantive changes do not enter main directly. Each change is developed on a feature or fix branch, submitted through a pull request, and reviewed by at least two team members other than the author before merging. This workflow ensures that no single person can change the controlled baseline without independent review, supporting the risk mitigation strategy for Scope Creep and Poor Traceability.

The repository structure follows the approved layout. The `product/` directory contains the application code, including the lifecycle service, database schema, and demo script. The `tests/` directory contains the automated test suite. The `docs/` directory contains the Project Engineering Document, Architecture Decision Records, the Requirements Traceability Matrix, and the project registers. The `.github/workflows/` directory contains the CI workflow configuration.

### 54.2 Continuous Integration Pipeline

The CI pipeline is defined in `.github/workflows/quality.yml` and runs automatically on every push to main and feature branches, and on every pull request targeting main. The pipeline consists of nine steps that together provide automated verification of the release candidate.

The pipeline checks out the repository at the commit being tested, sets up Python 3.12, and installs dependencies. It compiles the Python source files to detect syntax errors. It runs the unit test suite if the tests directory exists. It runs Bandit for static security analysis. It checks for hardcoded secrets in the codebase. It verifies that the `.env.example` file exists, which confirms that configuration is documented and that secrets are not committed to the repository.

### 54.3 Quality Gate

The CI pipeline functions as a quality gate because the workflow runs on pull requests targeting main. If any step in the pipeline fails, the pull request cannot be merged until the failure is corrected. A build failure, a static analysis failure, a detected secret, or a test failure blocks progression. The gate is enforced through GitHub branch protection, which requires status checks to pass before merging.

### 54.4 Configuration and Secrets Management

Secrets are not committed to the repository. The `.gitignore` file excludes the `.env` file, which holds environment-specific configuration values. The `.env.example` file documents the variables that the application expects without exposing their values. This pattern supports the security constraint that credentials must be separated from source code.

The current reference slice uses SQLite and requires minimal configuration. The database path defaults to `civicconnect.db` in the project root. No external services are used, so no API keys are required at this stage.

### 54.5 Evidence Location

The CI evidence is available in the GitHub Actions tab of the repository. Each workflow run records the steps that were executed, the output of each step, and the overall status. The test evidence is available in the `evidence/` directory. The repository history provides evidence of the branch and pull request workflow.



## Section 55: Release Evidence Summary (M3)

This section summarises the evidence that supports the M3 release readiness judgement.

### 55.1 Build and CI

The CI pipeline runs on every push and pull request. A successful run demonstrates that the code compiles, that no hardcoded secrets are present, that the `.env.example` file exists, and that all automated tests pass. A failed run blocks the pull request from merging. The CI result allows the team to conclude that the automated checks are passing for the tested revision. It does not prove that the application is free of defects.

### 55.2 Automated Regression

The automated regression suite includes the lifecycle tests and the traceability tests. The lifecycle tests verify controlled transitions, authorisation checks, concurrency handling, and persistence integrity. The traceability tests verify that the RTM structure is valid. All tests pass. A limitation is that the suite does not cover every possible input combination, so untested paths remain an uncertainty.

### 55.3 Static Analysis and Security

The CI pipeline runs Bandit for static security analysis and checks for hardcoded secrets. The Bandit result shows no high-severity findings. The secret detection shows no hardcoded secrets. These results demonstrate that the code does not contain the classes of defect that these tools detect. Static analysis cannot detect all defects.

### 55.4 Performance and Load

A performance smoke test runs as part of the CI pipeline. The operation tested is the lifecycle service under a small workload. The result is that the operation completes successfully. The performance evidence demonstrates that the operation completes without error under the tested workload. A limitation is that the workload is small and the environment is not representative of production scale.

### 55.5 Configuration

The `.env.example` file documents the required environment variables. The `.gitignore` file excludes the `.env` file. This demonstrates that configuration is separated from code and that secrets are not committed.

### 55.6 Release Readiness Classification

Based on the evidence above, the M3 release candidate is classified as CONDITIONALLY READY. The core lifecycle functionality is implemented and verified. The automated tests pass. The CI pipeline runs and the quality gate blocks on failure. The conditions are that the performance evidence is limited to a small workload and the staging environment does not replicate production conditions. These conditions do not block the M3 release because M3 does not require production-scale performance. They represent residual risk for M4.
