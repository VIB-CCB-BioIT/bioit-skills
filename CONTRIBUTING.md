# Adding a skill

Everything goes through a pull request, so every skill gets a second pair of eyes before it is shared.

## Steps

1. **Get access.**
   - Members of the VIB-CCB-BioIT organization: you can create a branch directly in this repo.
   - Everyone else: fork the repo and open the pull request from your fork.
2. **Copy the template.** Copy `skills/_template/` to `skills/<your-skill-name>/`.
   The folder name must be lowercase with hyphens, for example `cell-type-annotation`.
3. **Edit `SKILL.md`.**
   - `name` must equal the folder name.
   - `description` says what the skill does and when to use it. This is what an agent reads to decide whether to load it.
   - `metadata.owner` is your full name (the person to contact).
   - `metadata.status` is `draft` while testing, `stable` once someone other than the author has used it successfully.
   - Fill in the sections: when to use, inputs, steps, outputs, checks, limitations.
4. **Add supporting files** next to `SKILL.md` if needed (small example data, scripts, reference tables). Keep the folder under a few MB, with no patient data and no secrets.
5. **Open a pull request.** Fill in the checklist. An automatic check validates the frontmatter; fix anything it reports.
6. **Review.** A maintainer reads it and may ask for changes. The index in `README.md` and `skills.json` is rebuilt automatically on your pull request.

## Quality bar

- One skill does one task. Split big workflows into several skills.
- Say which tools, packages and reference versions the steps assume.
- Include at least one check the agent can run to confirm the result is sensible.
- State limitations honestly. A skill that says "not tested on spatial data" is more useful than one that implies it works everywhere.
- Never include personal or patient-level data, credentials or unpublished results.

## Changing a skill

Edit its folder and open a pull request. Describe what changed and why. If you change what the skill does in a way that could alter results, say so in the PR so users know to re-check.

## Local check (optional)

```bash
pip install pyyaml
python scripts/build_index.py
```
