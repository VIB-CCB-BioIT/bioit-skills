# BioIT & AI Skills

A shared library of agent skills for bioinformatics & AI work at VIB-CCB BioIT. A skill is a folder with a `SKILL.md` file that tells an AI agent how to do one task well, for example annotating cell types or reviewing a pathway analysis.

- **Use a skill:** open its folder, read `SKILL.md`, and copy the folder into your agent's skills directory.
- **Add a skill:** see [CONTRIBUTING.md](CONTRIBUTING.md). It takes a copy of the template and a pull request.
- **Machine-readable list:** [`skills.json`](skills.json).

> The index below is **generated** from the `SKILL.md` files. Do not edit between the markers.

<!-- SKILLS:START -->
**3 skills**

| Skill | What it does | Owner | Status | Tags |
|---|---|---|---|---|
| [powerpoint-vib](skills/powerpoint-vib) | Use whenever a PowerPoint presentation, slide deck, or .pptx file needs to be created or generated — for talks, project updates, meeting slides, posters-as-slides, or any "make me a deck/slides about X" request. VIB-CCB has a mandatory house style, so ALWAYS build new decks from the bundled VIB-CCB template rather than a blank python-pptx presentation, even if the user doesn't mention a template, branding, or VIB by name. Also use it when an existing VIB deck needs reworking because its figures are too small or unreadable, or its slides carry too much text — the skill's figure-first layout rules and audit script apply. Do not use this for editing arbitrary existing .pptx files that aren't meant to carry VIB branding. | Luuk Harbers | draft | presentations, pptx, vib-branding |
| [vsc-job-submission](skills/vsc-job-submission) | Use when writing, submitting, or debugging batch jobs on the KU Leuven VSC clusters (Mindwell, wICE, Genius) — sbatch scripts, choosing a cluster/partition/account, requesting GPUs, memory or walltime, interactive sessions, monitoring the queue, or diagnosing a job that failed, was killed, timed out, or was rejected. Also the reference for what the clusters contain: which partitions exist, and per partition the node count, cores, GPU model and count (B200, A100, H100), memory, maximum walltime, per-GPU core and memory ceiling, and credit cost. Answers both action requests ("run this on the cluster", "how many cores should I ask for", "why did my job die") and bare factual ones ("what is the max number of GPUs on a Mindwell partition", "which partition has H100s", "how long can a job run") — even if Slurm is never mentioned. Encodes the Mindwell-first default and the account/partition lock that VSC documents nowhere. | Luuk Harbers | draft | hpc, vsc, slurm, kuleuven |
| [vsc-remote-dev](skills/vsc-remote-dev) | Use when connecting to the KU Leuven VSC for interactive work — setting up or debugging a VS Code tunnel, `code tunnel` on a compute node, screen/tmux sessions on a login node, `ssh login` and SSH config, Open OnDemand, or loading software with Lmod modules. Applies to "I can't connect", "VS Code won't attach", "my session died overnight", "which module do I load", "where did my screen go", and to any request to set up a development environment on the cluster. Encodes the recommended code-tunnel workflow, which replaces the older Remote-SSH approach. | Luuk Harbers | draft | hpc, vsc, vscode, remote-dev, kuleuven |
<!-- SKILLS:END -->
