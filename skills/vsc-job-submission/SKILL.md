---
name: vsc-job-submission
description: >-
  Use when writing, submitting, or debugging batch jobs on the KU Leuven VSC clusters (Mindwell,
  wICE, Genius) — sbatch scripts, choosing a cluster/partition/account, requesting GPUs, memory or
  walltime, interactive sessions, monitoring the queue, or diagnosing a job that failed, was
  killed, timed out, or was rejected. Also the reference for what the clusters contain: which
  partitions exist, and per partition the node count, cores, GPU model and count (B200, A100,
  H100), memory, maximum walltime, per-GPU core and memory ceiling, and credit cost. Answers both
  action requests ("run this on the cluster", "how many cores should I ask for", "why did my job
  die") and bare factual ones ("what is the max number of GPUs on a Mindwell partition", "which
  partition has H100s", "how long can a job run") — even if Slurm is never mentioned. Encodes the
  Mindwell-first default and the account/partition lock that VSC documents nowhere.
metadata:
  owner: Luuk Harbers
  status: draft
  tags: [hpc, vsc, slurm, kuleuven]
---

# Submitting jobs on the VSC (Mindwell / wICE)

This skill covers Slurm on the KU Leuven Tier-2 clusters. Picking the wrong
filesystem for the cluster is the most common way these jobs fail, and admins
enforce it, so read "Filesystem must match the cluster" below.

## When to use

Writing, submitting, sizing or debugging any Slurm job on Mindwell, wICE or
Genius, and answering factual questions about their partitions, GPUs, walltimes
and credit costs. Not for pipeline/profile design (Nextflow is covered only as
far as cluster and storage go) and not for interactive editor setup (see
`vsc-remote-dev`).

## Placeholders — fill these in for your group

| Placeholder | Meaning | Example (one VIB-CCB lab) |
|---|---|---|
| `<your-credit-account>` | Your group's normal credit account, from `sam-balance` | `lp_mylab` |
| `<your-gpfs-project>` | Your project directory on GPFS (Mindwell), under `$VSC_PROJECT_GPFS1` | `prj_000NN` |
| `<your-lustre-project>` | Your project directory on Lustre (wICE/Genius), under `$VSC_PROJECT_LUSTRE1` | `stg_000NN` |

The `lp_big_*` dedicated accounts and `dedicated_big_*` partitions below are
named as they exist on the clusters; whether *you* can use them depends on
`sam-balance`.

## Filesystem must match the cluster

- **Mindwell → GPFS** (`$VSC_SCRATCH_GPFS1`, `$VSC_PROJECT_GPFS1`).
  **wICE and Genius → Lustre** (`$VSC_SCRATCH_LUSTRE1`, `$VSC_PROJECT_LUSTRE1`).
  Both filesystems are visible from both clusters, so a mismatch does not error;
  it runs slowly and may get the job cancelled.
- **`$VSC_SCRATCH` is the same string on both clusters** and resolves through a
  node-local symlink. It is correct only when it expands *on the compute node*
  (inside the job script). Expanded in a login shell — e.g. inside `--wrap="…"`
  typed on a wICE login node — it silently gives a Mindwell job the Lustre path.
  When in doubt, write `$VSC_SCRATCH_GPFS1` / `$VSC_SCRATCH_LUSTRE1` explicitly.
- **Project paths do not follow the cluster.** Moving a job between clusters
  means editing its project paths by hand.
- **Scratch is purged** of files not accessed for 30 days. Nothing durable lives
  there. Stage data in with `cp` (not `mv`/`rsync -a`, which keep the old atime).
- Never write data to `$VSC_HOME` (small quota, dotfiles only).

## Default to Mindwell

**Large jobs, and anything generating many intermediate files (Nextflow/nf-core
especially), go to Mindwell with work directories on GPFS scratch.** Do not put
work directories on project storage unless it genuinely cannot be avoided.

A Mindwell job should read and write GPFS project storage (`<your-gpfs-project>`)
too, not just GPFS scratch. Unlike `$VSC_SCRATCH`, a project path is a plain string
and does not follow the cluster — moving a job to Mindwell means editing its input,
output and config paths by hand.

Legitimate reasons to use wICE instead:

- The job needs an A100 or H100 specifically (Mindwell GPUs are B200).
- It depends on a wICE-only dedicated partition (`dedicated_big_gpu_h100`).
- It is small and its inputs are already on Lustre (`<your-lustre-project>`),
  where staging in would cost more than the job saves.

Both clusters are reachable from any login node; `-M/--clusters` selects the
target, so you never need to hop hosts to submit.

## Prefer the dedicated nodes for short jobs

```bash
sam-balance   # does this account hold lp_big_mindwell_cpu / lp_big_mindwell_gpu_b200?
```

**If that check finds the association and the job fits in roughly a day, submit
it to a dedicated Mindwell partition first.** Those partitions bill at
`CPU=0` — the job is free — and far fewer users contend for them, so a short job
normally starts sooner there than the same job in the public queue. Access is not
universal: each dedicated partition sets `AllowAccounts=<its own account>` and
nothing else, so a submitter without the association falls straight through to
step 2.

Order of preference, cluster and partition together:

1. **Mindwell dedicated** — `dedicated_big_bigmem` for CPU and large-memory
   work, `dedicated_big_gpu_b200` for GPU work.
2. **Mindwell public** — `batch_graniterapids`, `bigmem` or `gpu_b200` on an
   ordinary credit account.
3. **wICE** — only for one of the reasons listed above.

One day is where the queue-wait advantage is worth taking, not a ceiling: the
dedicated partitions allow 7 d, so a longer job may still use them. Which account
goes with which partition is in "Account and partition are hard-locked together"
below; node counts and walltimes are in `references/partitions.md`.

## Pick a partition

Mindwell (all nodes 192 cores):

| Need | Partition | GPU/node | Mem/node | Walltime |
|---|---|---|---|---|
| Normal CPU work | `batch_graniterapids` *(default)* | — | 768 G | 3 d |
| CPU work over 3 days | `batch_graniterapids_long` | — | 768 G | 7 d |
| More than ~750 G RAM | `bigmem` | — | 1536 G | 3 d |
| GPU | `gpu_b200` | 8× B200 (192 G) | 1536 G | 3 d |
| Testing, shells, data transfers | `interactive` | 2× RTX-5000 Ada (32 G) | 768 G | 16 h |
| Dedicated CPU/bigmem nodes | `dedicated_big_bigmem` | — | 1536 G+ | 7 d |
| Dedicated GPU node | `dedicated_big_gpu_b200` | 8× B200 | 2313 G | 7 d |

**8 GPUs per node is the Mindwell ceiling** — no partition has more. `gpu_b200`
additionally caps each GPU at 24 cores and 194400 MiB; asking for more produces
a warning.

wICE equivalents: `batch` / `batch_long` (72 c, 256 G), `batch_sapphirerapids{,_long}`
(96 c), `bigmem` (2 T), `hugemem` (8 T), `gpu_a100` (4× A100 80 G), `gpu_h100`
(4× H100 80 G), `interactive` (1× A100 MIG), `dedicated_big_bigmem`,
`dedicated_big_gpu` and `dedicated_big_gpu_h100` (4× A100 / 4× H100),
`dedicated_big_gpu_small` (8× A100 MIG). wICE tops out at **4 full GPUs per
node**.

Full specs, node counts, billing weights and per-GPU limits:
`references/partitions.md` (captured 2026-08-13).

## Account and partition are hard-locked together

This is enforced by Slurm and documented nowhere. Getting it backwards is an
immediate rejection, not a slow queue.

| Partition | Account to use |
|---|---|
| Mindwell `dedicated_big_bigmem` | `lp_big_mindwell_cpu` |
| Mindwell `dedicated_big_gpu_b200` | `lp_big_mindwell_gpu_b200` |
| wICE `dedicated_big_bigmem` | `lp_big_wice_cpu` |
| wICE `dedicated_big_gpu`, `dedicated_big_gpu_small` | `lp_big_wice_gpu` |
| **Any public partition, either cluster** | `<your-credit-account>` |

The dedicated partitions set `AllowAccounts=<their own account>` and nothing
else. Every public partition sets `DenyQos=…,lp_big_mindwell_cpu,lp_big_mindwell_gpu_b200,lp_big_wice_cpu,lp_big_wice_gpu`
— so the dedicated accounts are actively **banned** from the public queues. The
two sets never mix.

`--account` is mandatory. Two things that look like problems but are not:

- **`sam-balance` shows `Available = 1`** for the `lp_big_*` accounts. Harmless —
  every dedicated partition has `TRESBillingWeights=CPU=0`, so those jobs cost
  nothing and the balance is never drawn down.
- **`interactive` is also free** on both clusters (weight 0).

**`lp_mindwell_pilot` is dead.** The VSC docs still advertise it as a free pilot
account, but it is no longer in `sam-balance`. Any older script using it will be
rejected — swap it for `<your-credit-account>`.

Check before submitting: `sam-balance`, and `sam-quote sbatch <script>` for a
worst-case cost estimate (it assumes the job runs to its full time limit).

## The canonical job script

```bash
#!/bin/bash -l
#SBATCH --clusters=mindwell
#SBATCH --partition=batch_graniterapids
#SBATCH --account=<your-credit-account>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=4000M
#SBATCH --time=24:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<your.email@kuleuven.be>
```

Notes on this header:

- **`#!/bin/bash -l` is required in practice.** Without `-l`, `~/.bashrc` never
  runs and the cluster module is never loaded, so `$PATH`, `micromamba`, and the
  `NXF_*` variables are all missing. This is the root cause of most "works
  interactively, fails in the job" reports.
- Put log paths on the **same cluster's** scratch (see "Filesystem must match the
  cluster"). Prefer
  `$VSC_SCRATCH`-relative or job-relative paths over a hardcoded
  `/scratch/leuven/<group>/<vscid>/logs/`, which resolves to Lustre when it is
  written out in full and is therefore wrong for a Mindwell job.
- `--cluster=` (singular) and `--gres=gpu:N` appear in many older
  scripts. Both are valid Slurm and work fine — no need to "fix" them. New
  scripts should use the documented `--clusters=` and `--gpus-per-node=`.

Templates: `templates/cpu.sbatch`, `templates/gpu.sbatch`,
`templates/nextflow.sbatch`.

## Memory: the expensive mistake

On every public partition `DefMemPerCPU == MaxMemPerCPU`. You cannot get more
memory per core — asking for it **silently allocates more cores**, and you are
billed for all of them.

`--mem-per-cpu=8G` on `batch_sapphirerapids` (2500 MiB/core) costs
`ceil(8*1024/2500) = 4` cores for every task you asked for. Requesting a node's
full memory blocks and bills the entire node.

Per-core ceilings: Mindwell `batch_graniterapids` 4000 M, `bigmem`/`gpu_b200`
8000 M; wICE `batch` 3400 M, `batch_sapphirerapids` 2500 M, `bigmem` 28000 M,
`hugemem` 111900 M. The dedicated partitions are the exception and do allow
raising it (Mindwell `dedicated_big_bigmem` up to 12050 M).

If you need lots of memory on few cores, that is what `bigmem` / `hugemem` /
`dedicated_big_bigmem` are for.

## GPUs

```bash
#SBATCH --partition=gpu_b200
#SBATCH --account=<your-credit-account>
#SBATCH --gpus-per-node=2
#SBATCH --cpus-per-task=24
```

- Respect the per-GPU ceiling or Slurm warns and may resize: Mindwell `gpu_b200`
  24 cores + 194400 MiB per GPU; wICE `gpu_h100` 16 + 187200; `gpu_a100` 18 + 126000.
- `GresEnforceBind=Yes`, so the CPU allocation is rounded up to a whole number of
  per-GPU shares. A job asking for 16 cores with 2 GPUs is allocated 42. `sacct`
  showing more cores than you requested is expected.
- GPUs are the expensive resource: a B200 bills 437.5 credits/GPU-minute, an H100
  569.4. A 24 h 2-GPU `gpu_b200` job costs roughly 1.3 M credits — and nothing at
  all on `dedicated_big_gpu_b200`. See "Prefer the dedicated nodes for short
  jobs" above.
- In containers: `singularity run --nv …` (or `exec`), with explicit `-B` binds
  for any staging paths the tool must read.

## Environment inside jobs

By default `sbatch` uses `--export=ALL`, so exported variables from the submitting
shell **do** reach the job (verified: `$MAMBA_EXE` arrives intact). What does not
survive is anything that is not an exported variable — shell functions, aliases,
and whatever `~/.bashrc` would have set up had it run.

- Use `#!/bin/bash -l` (above). Without it `~/.bashrc` never runs, so no cluster
  module is loaded. If your `~/.bashrc` only loads toolchains (e.g. `foss/2025a`)
  in interactive shells, `module load` what you need explicitly in the job.
- **`micromamba` is a shell function, so it does not exist in batch jobs** even
  though `$MAMBA_EXE` is set. Use the absolute binary, `$MAMBA_EXE`, or a direct
  path into the env:
  ```bash
  "$MAMBA_EXE" run -n nextflow nextflow run …
  $VSC_DATA/software/micromamba/envs/<env>/bin/<tool>
  ```
- **`--export=VAR=…` replaces the default `ALL`**, so it exports *only* what you
  list and everything else disappears. Scripts that use `--export`
  this way should therefore hardcode absolute paths for the binaries and containers they
  need; keep doing that, or write `--export=ALL,VAR=…` to add rather than replace.
- The `vsc_kul_uhasselt` Nextflow profile reads `$SLURM_ACCOUNT` as the account
  for every task it submits. Export it (`export SLURM_ACCOUNT=<your-credit-account>`, commonly
  done from `~/.bashrc`) and remember to change it when you change cluster.

## Whole-node jobs

There is no `--exclusive` recipe in the KU Leuven docs. Request every core:
`--nodes=1 --ntasks-per-node=192` on Mindwell, `72` on wICE IceLake, `96` on
Sapphire Rapids.

## Interactive sessions

```bash
srun --clusters=mindwell --partition=interactive --account=<your-credit-account> \
     --ntasks=1 --time=01:00:00 --pty bash -l
```

Capped at 8 cores, 1 GPU, 16 h — and free. Add `--gpus-per-node=1 --x11` for a
GPU/graphical session. Open OnDemand also supports Mindwell. For anything large,
use a batch job instead; interactive allocations idle.

## Monitoring

The two clusters have **separate job-ID spaces**, so `-M` is effectively
mandatory on every query.

```bash
squeue -M wice,mindwell -u $USER          # queue on both
sacct  -M wice,mindwell -S now-7days \
       -o JobID,Cluster,Partition,Account,AllocCPUS,ReqMem,Elapsed,State
seff <jobid>                              # efficiency after the fact
scontrol -M mindwell show job <jobid>     # full spec of a live job
srun -M mindwell --jobid=<id> --overlap --pty bash -l   # shell into a running job
```

Concurrency limits (QoS follows the partition name — `*_long`→`long`,
`interactive`→`interactive`, else `normal`): `normal` 500 queued jobs per user;
`long` 20 jobs and 10 nodes; `interactive` 4 jobs, 8 cores, 1 GPU, 1 node. The
dedicated QoS set no limits. Re-check with:

```bash
sacctmgr show qos normal,long,interactive format=Name%20,MaxSubmitJobsPerUser%12,MaxTRESPerUser%30
```

When a job dies, see `references/troubleshooting.md`.

## Nextflow

Enough to get the storage and cluster parts right; this skill does not cover
pipeline or profile design.

- Submit the Nextflow **head process** as a small job (1 core, 8–16 G, long
  walltime) and let the `slurm` executor spawn the real work. That is the recommended
  pattern and `templates/nextflow.sbatch` follows it.
- Set the work directory on the compute cluster's own scratch, inside the job
  script: `export NXF_WORK="${VSC_SCRATCH}/work"`, or `-w "${VSC_SCRATCH}/work"`
  (correct there because it expands on the node — see "Filesystem must match the
  cluster"). Results can go to the project directory on the same cluster's
  filesystem — `<your-gpfs-project>` for a Mindwell run, `<your-lustre-project>`
  for a wICE one.
- **Pick the cluster sub-profile explicitly**: `-profile vsc_kul_uhasselt,mindwell`
  (or `mindwell_gpu`) on Mindwell, `vsc_kul_uhasselt,wice` (or `wice_gpu`) on
  wICE. Each loads its own `cluster/<name>/<queue>` module and sets its own
  `resourceLimits`, so a `wice` sub-profile inside a Mindwell job emits
  `--clusters=wice` for every task. The `mindwell` profiles landed in
  nf-core/configs on 2026-08-18; on a first run, confirm the tasks appear in
  `squeue -M mindwell`. To list the sub-profiles that exist:
  ```bash
  curl -s https://raw.githubusercontent.com/nf-core/configs/master/conf/vsc_kul_uhasselt.config \
    | grep -nE '^    [a-z_]+ \{'
  ```

## Checks

- `sam-balance` lists the account you put in `--account`, and the account matches
  the partition per the lock table above.
- `sam-quote sbatch <script>` gives a cost you expect (worst case: full walltime).
- After submission, the job appears in `squeue -M <cluster> -u $USER` on the
  cluster you intended; for Nextflow, the child tasks appear there too.
- Every path in the script (work dir, logs, inputs, outputs) is on the filesystem
  that matches the cluster: `/gpfs1/…` for Mindwell, `/lustre1/…` for wICE.
- Afterwards, `seff <jobid>` shows CPU and memory efficiency that justify the
  request; shrink the next request if not.

## Limitations

- Partition specs, billing weights, QoS limits and account names are a snapshot
  (`references/partitions.md`, captured 2026-08-13). Re-check with `sinfo`,
  `scontrol show partition`, `sacctmgr show qos` and `sam-balance` before relying
  on a number.
- Written and tested from one VIB-CCB lab's accounts; access to the `dedicated_big_*`
  partitions is not universal.
- Assumes `micromamba` under `$VSC_DATA/software/micromamba` and the
  `vsc_kul_uhasselt` nf-core profile; adapt if your setup differs.
- Genius is mentioned only in passing; nothing here was tested on it.
