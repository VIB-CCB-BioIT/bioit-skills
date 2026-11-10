# Maintainer notes

Reviewer: Masoomeh Rahimpour (`@mrahimpour`), set in `.github/CODEOWNERS`. Every pull request requests their review automatically.

To make the review mandatory, protect `main` (Repo → Settings → Rules → Rulesets):
- Require a pull request before merging, with 1 approval.
- Require the status check **Validate skills / build**.
- Let the GitHub Actions bot bypass the rule, so the automatic index commit can be pushed.

Also set Settings → Actions → General → Workflow permissions → **Read and write**.

When more reviewers join, change `.github/CODEOWNERS` to a team handle.
