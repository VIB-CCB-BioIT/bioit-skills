---
name: vsc-remote-dev
description: >-
  Use when connecting to the KU Leuven VSC for interactive work — setting up or debugging a VS
  Code tunnel, `code tunnel` on a compute node, screen/tmux sessions on a login node, `ssh login`
  and SSH config, Open OnDemand, or loading software with Lmod modules. Applies to "I can't
  connect", "VS Code won't attach", "my session died overnight", "which module do I load", "where
  did my screen go", and to any request to set up a development environment on the cluster.
  Encodes the recommended code-tunnel workflow, which replaces the older Remote-SSH approach.
metadata:
  owner: Luuk Harbers
  status: draft
  tags: [hpc, vsc, vscode, remote-dev, kuleuven]
---

# Interactive development on the VSC

Job submission is covered by `vsc-job-submission`. This skill is about getting a
working editor and shell on a compute node, and about finding software once you
are there.

## When to use

Setting up or debugging interactive work on the KU Leuven VSC: VS Code tunnels,
screen/tmux on a login node, Open OnDemand, Lmod modules, and R/Python editor
integration over a tunnel. Not for batch jobs (use `vsc-job-submission`).

Replace `<your-credit-account>` below with your group's credit account (see
`sam-balance`). The `interactive` partition is free, but `--account` is still
mandatory.

## Recommended workflow: code tunnel

`screen` on the **login node** → `srun` **inside** it → `code tunnel` on the
**compute node** → connect local VS Code to the tunnel. Remote-SSH into compute
nodes is deprecated: it needs every node prefix listed in the user's local SSH
config and offers no way to move the VS Code server off the small `$VSC_HOME`.

```bash
ssh login
hostname -f                     # note the login node; screen is per-node
screen -S tunnel

srun --clusters=mindwell --partition=interactive --account=<your-credit-account> \
     --ntasks=1 --cpus-per-task=8 --mem=32G --time=16:00:00 --pty bash -l

CODE=$(ls -d /apps/leuven/common/software/code-cli/*/code | tail -1)
"$CODE" tunnel --accept-server-license-terms \
        --name "vsc-${USER}-mindwell" \
        --server-data-dir "${VSC_DATA}/.vscode-server" \
        --extensions-dir  "${VSC_DATA}/.vscode-server/extensions"

# first run: complete the device-code login before detaching
# detach: Ctrl-a d     (NOT `exit`, NOT Ctrl-a k)
```

Then locally: Command Palette → "Remote Tunnels: Connect to Tunnel". Requires
the `ms-vscode.remote-server` extension.


## Non-obvious failure modes

Diagnose in roughly this order — the first two cover most reports.

**`$VSC_HOME` fills up.** Without `--server-data-dir`/`--extensions-dir` the VS
Code server and every extension unpack into `~/.vscode-server`. `$VSC_HOME` is
about 7 GB and holds dotfiles. Symptom: the tunnel starts but VS Code never
finishes connecting, or connects and drops. Check
`du -sh ~/.vscode-server ~/.vscode-cli`, delete, restart with the flags.

**Tunnel name collisions.** A name is one registration per account. The same
`--name` used on two clusters means the second silently steals it and the first
stops working. Always suffix the cluster: `vsc-<vscid>-<cluster>`. Recover with
`code tunnel unregister`.

**Version-pinned paths.** `/apps/leuven/common/software/code-cli/<version>/code`
— the version directory changes. Never write the literal version; glob and take
the last. A user reporting `code: command not found` after months of working
setup has almost certainly pinned it.

**Login-node stickiness.** `screen -ls` only lists sessions on the current login
node. Several sit behind the `login` alias and the individual names
(`tier2-p-login-N`) do not resolve publicly, so a specific one cannot be
targeted. An empty `screen -ls` usually means a different login node, not a dead
job — check `squeue --me` before concluding anything died.

**The 16 h interactive cap.** `interactive` maxes at 16:00:00 on both wICE and
Mindwell, so tunnels do not survive overnight. This is expected. Do not suggest
parking a tunnel on `batch` for days to avoid it: it bills credits while idle and
misuses the partition.

**Maintenance masquerading as user error.** "Requested node configuration is not
available" for an otherwise valid request usually means nodes are `down`,
`drain`, `maint` or `reserved`. Check before debugging the command:

```bash
sinfo -M wice -p interactive -N -o "%N %T %C %m"
```

## Recovery commands

Run on the compute node, with `$CODE` resolved as above:

```bash
"$CODE" tunnel status        # is one running here
"$CODE" tunnel kill          # stop it
"$CODE" tunnel restart
"$CODE" tunnel unregister    # release this machine's name
"$CODE" tunnel prune         # drop servers no longer running
"$CODE" tunnel rename <new>
```

## screen and tmux

```bash
screen -S tunnel      # create        tmux new -s tunnel
screen -ls            # list          tmux ls
screen -r tunnel      # reattach      tmux attach -t tunnel
# detach: Ctrl-a d                    # detach: Ctrl-b d
```

Both are at `/usr/bin`. `exit` and `Ctrl-a k` destroy the session and everything
in it; only detaching preserves the job.

## Open OnDemand

The portal offers a VS Code Tunnel under Interactive Apps that performs the same
setup with no ssh, screen or srun, using the same `vsc-<VSC-id>-<cluster>`
naming. Suggest it when someone wants a session quickly and default resources
suffice; prefer the manual route when cluster, account or resources matter, or
when the setup should be scripted.

<https://docs.vscentrum.be/compute/portal/ondemand/vscode-tunnel.html>

## Lmod modules

Nothing is loaded by default.

```bash
module spider samtools          # search, incl. extensions inside toolchains
module av                       # everything (long)
module load SAMtools/1.21-GCC-13.3.0
module list
module purge
```

Points that actually matter:

- **Load modules inside the job script**, not only in the interactive shell, or
  the job will not find them.
- Requires a login shell — `#!/bin/bash -l`. Without it `module` is undefined.
- `cluster/*` modules retarget Slurm commands, e.g. `cluster/wice/batch`. Usually
  unnecessary: `--clusters=` on `sbatch`/`srun` works from any login node and is
  less surprising. Note that loading one *changes the current shell's* cluster
  and can be a source of confusion when a user reports that `squeue` "lost" jobs.
- Availability differs per cluster architecture. A module on Genius may not
  exist on Mindwell.
- Prefer a module over building from source; prefer micromamba over both when
  version control matters.

## Editor integration

R needs `languageserver` and `httpgd` installed in R, `radian` as the terminal,
and exactly two extensions (`REditorSupport.r`, `RDebugger.r-debugger`) — more
than that and they conflict. `Cannot determine R HOME` is fixed by reconnecting
or by setting `R_HOME` in `terminal.integrated.env.linux`.

Extensions install per-host. An extension that appears missing over the tunnel is
usually installed locally but not on the remote.

## Reference

- <https://docs.vscentrum.be/compute/portal/ondemand/vscode-tunnel.html> — OnDemand tunnel
- <https://docs.vscentrum.be/access/access_methods.html> — first login, keys, MFA
- <https://code.visualstudio.com/docs/remote/tunnels>

## Checks

- `"$CODE" tunnel status` on the compute node reports a running tunnel with the
  expected `vsc-<vscid>-<cluster>` name.
- `squeue -M mindwell,wice --me` shows the interactive job that hosts it.
- `du -sh ~/.vscode-server ~/.vscode-cli` is small (or the dirs do not exist),
  confirming the server lives under `$VSC_DATA`.
- After detaching, `screen -ls` (on the same login node) still lists the session.

## Limitations

- The `code-cli` install path and the 16 h `interactive` cap are as observed in
  2026; re-check `/apps/leuven/common/software/code-cli/` and
  `scontrol -M mindwell show partition interactive` if something changes.
- Assumes an `ssh login` alias already set up in your local SSH config
  (see the VSC access docs above).
- Tested on Mindwell and wICE; not on Genius.
