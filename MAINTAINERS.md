# Maintainer notes (one-time setup)

How contributions are controlled on GitHub:

1. **Create a team** in the organization, for example `bioit-skills-maintainers`
   (Org → Teams → New team). Add the people who review skills.
2. **Give access.**
   - Repo → Settings → Collaborators and teams: give `bioit-skills-maintainers` **Maintain** or **Write**.
   - Other org members: **Write** (they can create branches and open pull requests) or **Read** (they fork).
3. **Protect `main`** (Repo → Settings → Rules → Rulesets, or Branches → Add rule):
   - Require a pull request before merging, with 1 approval.
   - Require the status check **Validate skills / build**.
   - Allow the GitHub Actions bot to push the automatic index commit (bypass list), or the rebuild step will be blocked.
4. **CODEOWNERS** (`.github/CODEOWNERS`) currently lists `@mrahimpour`, so every pull request requests their review automatically. Once the maintainers team exists, change it to `* @VIB-CCB-BioIT/bioit-skills-maintainers`. To make that review mandatory, enable **Require review from Code Owners** in the branch rule.
5. **Optional: Teams.** Subscribe the channel to the repo (`@GitHub subscribe VIB-CCB-BioIT/bioit-skills pulls releases`) so new skills are announced.
6. **Workflow permissions:** Settings → Actions → General → Workflow permissions → Read and write.
