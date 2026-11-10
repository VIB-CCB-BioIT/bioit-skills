# Diagnosing failed VSC jobs

Start here:

```bash
sacct -M wice,mindwell -j <jobid> \
  -o JobID,Cluster,Partition,Account,AllocCPUS,ReqMem,MaxRSS,Elapsed,Timelimit,State,ExitCode
seff <jobid>
```

`State` plus the `.batch` sub-step's `ExitCode` usually names the cause outright.
Note the two clusters have separate job-ID numbering, so always pass `-M`.

## Rejected at submit time

| Message | Cause | Fix |
|---|---|---|
| `Invalid account or account/partition combination specified` | The account↔partition lock. Dedicated partitions accept only their own `lp_big_*` account; public partitions actively deny those accounts. | Match them — see the table in `SKILL.md`. Public ⇒ `<your-credit-account>`; dedicated ⇒ its own account. |
| Same, on an older script | The script uses `--account=lp_mindwell_pilot`, which has expired. | Replace with `<your-credit-account>`. |
| `Invalid partition name specified` | Partition exists on the *other* cluster, or `--clusters` is missing/wrong. `bigmem` exists on both and means different hardware. | Check `--clusters=`; verify with `sinfo -M <cluster>`. |
| `Requested node configuration is not available` | Asked for more cores or memory than any node in that partition has. | Check the partition's real size in `partitions.md`. Mindwell nodes are 192 c; wICE 72 or 96. |
| `Job violates accounting/QOS policy` | Hit a QoS limit: `long` allows 20 queued jobs / 10 nodes, `interactive` 4 jobs / 8 cores / 1 GPU. | Reduce the request, or use a `normal` partition (500 job limit). |
| Job submits but never starts, `(Dependency)` | Waiting on `--dependency=afterok:` for a job that has not finished (or failed). | `squeue -M <cluster> -u $USER`; if the parent failed, the dependent will never run — cancel and resubmit. |
| Job pends with `(AssocGrpBillingMinutes)` | Credit account is empty. | `sam-balance`; use another credit account or a free dedicated/interactive partition. |

## FAILED after a few seconds, with no output file at all

Slurm could not create the `--output` / `--error` file, so it cancelled the batch
step before your script ran. `sacct` shows `FAILED` with ~5 s elapsed, the
`.batch` step `CANCELLED`, and there is no log to read — the log *is* the thing
that failed.

Almost always a path that does not exist on the target cluster. The common cause
is a path traversing `/scratch/leuven`, which is a per-cluster symlink: Lustre on
wICE, GPFS on Mindwell. A directory that exists on one is absent on the other.

Confirmed real case: a directory symlinked into `/scratch/leuven/<group>/<vscid>/`
— e.g. `~/.claude` — so `--output` beneath it works on wICE and fails instantly on
Mindwell.

```bash
# Resolve the path AS THE TARGET CLUSTER SEES IT before blaming the script
srun --clusters=mindwell --partition=interactive --account=<your-credit-account> \
     --time=2:00 --ntasks=1 readlink -f <the path>
```

Fix: point logs at a path that exists on the compute cluster — `$VSC_SCRATCH`
expanded on the node, or an explicit `/gpfs1/scratch/...` for Mindwell — and
`mkdir -p` the directory before submitting.

## OUT_OF_MEMORY

The job was killed for exceeding its memory allocation. `seff` reports peak RSS
against what was requested.

The trap: on public partitions `DefMemPerCPU == MaxMemPerCPU`, so `--mem` /
`--mem-per-cpu` above that ceiling does **not** give the task more memory per
core — it allocates extra cores instead, and you are billed for them. If a task
genuinely needs more memory per core, you need a different partition, not a
bigger number.

Options, in order of preference:

1. Move to a partition with a higher per-core ceiling: Mindwell `bigmem`
   (8000 M/core, 1536 G/node), wICE `bigmem` (28000 M), `hugemem` (111900 M),
   or `dedicated_big_bigmem` (which *does* allow raising `--mem-per-cpu`).
2. Raise `--cpus-per-task` so the total allocation grows.
3. For Nextflow, override the specific process rather than the whole pipeline —
   the recommended pattern is a small extra `-c` config with
   `withName: 'THE_PROCESS' { memory = 1500.GB * task.attempt }`.

Worked example of the trap: a `batch_sapphirerapids_long` job asking for 50 cores
and 120 G gets exactly 2500 M/core × 50 = 122 G — sitting on the ceiling with no
headroom, so it dies `OUT_OF_MEMORY` on the first spike.

## TIMEOUT

Walltime exhausted; partial output is whatever had been flushed.

- 3 days is the maximum on the default partitions. For longer, use
  `batch_graniterapids_long` (Mindwell) or `batch_long` /
  `batch_sapphirerapids_long` (wICE), or a `dedicated_*` partition — all 7 days.
- **7 days is the ceiling everywhere**, and it is hit in practice — a job dying at
  exactly `7-00:00:2x` on `dedicated_big_bigmem` is the wall, not a fluke. There is
  no longer partition, so the answer is checkpointing or splitting the work, not a
  bigger `--time`.
- Nextflow head jobs should have a long `--time` (168 h is a sensible default)
  since they only orchestrate; it is the *tasks* that need realistic limits.
- `-resume` works if the work directory survived. Confirm the work dir is not on
  purge-subject scratch that has since been cleaned (30-day purge).

## Job runs but the tool is "not found"

Almost always the batch environment, not the software.

- Missing `-l` in the shebang. `#!/bin/bash` alone does not source `~/.bashrc`, so
  `$PATH`, the cluster module, and all `NXF_*` variables are absent. Use
  `#!/bin/bash -l`.
- `micromamba: command not found` — it is a shell function, absent in batch jobs.
  Use `$MAMBA_EXE run -n <env> …` or an absolute path into
  `$VSC_DATA/software/micromamba/envs/<env>/bin/`.
- `--export=VAR=…` without `ALL` exports only what is listed; everything else is
  gone. Use absolute paths for binaries and containers in such scripts.
- On Mindwell, modules exist only for toolchains 2024a+ (CPU) / 2025a+ (GPU). An
  older toolchain that works on wICE may simply not be there.

## Job is inexplicably slow, or gets cancelled without warning

Suspect filesystem locality first. Compute on one cluster doing heavy I/O against
the other cluster's filesystem is both slow and against policy — VSC states such
jobs *"can be cancelled by the system administrators without prior notice."*

Check what the job is actually reading and writing: a Mindwell job must use GPFS
(`/gpfs1/...`), a wICE job Lustre (`/lustre1/...`). The `$VSC_SCRATCH` path string
is identical on both clusters but resolves differently per node, so this is easy
to get wrong invisibly. See "Filesystem must match the cluster" in `SKILL.md`.

Other causes: millions of small files on a parallel filesystem (metadata-bound —
VSC advises against it), or a container being re-pulled every task because the
cache directory points at the wrong filesystem.

## GPU job oddities

- **`sacct` shows more cores than requested** — expected. `GresEnforceBind=Yes`
  rounds the allocation up to whole per-GPU shares (16 cores + 2 GPUs ⇒ 42).
- **Warning about cores/memory per GPU** — over the ceiling (Mindwell `gpu_b200`
  24 cores / 194400 MiB per GPU). Reduce, or request another GPU.
- **CUDA not visible in a container** — missing `--nv` on
  `singularity run|exec`.
- Unexpectedly large credit spend: a B200 is 437.5 credits/GPU-minute and an H100
  569.4. Use `dedicated_big_gpu_b200` (free) when the 7-day limit fits, and
  `sam-quote sbatch <script>` before submitting anything long.

## Useful one-liners

```bash
# Why is my job pending?
squeue -M mindwell -u $USER -o "%.18i %.20P %.8T %.10M %.20R"

# Full spec of a live job, including the resolved work dir and log paths
scontrol -M mindwell show job <jobid>

# Attach a shell to a running job to look around
srun -M mindwell --jobid=<jobid> --overlap --pty bash -l

# What did I run recently, and how did it end?
sacct -M wice,mindwell -u $USER -S now-14days \
  -o JobID,Cluster,Partition,Account,AllocCPUS,ReqMem,Elapsed,State --parsable2
```
