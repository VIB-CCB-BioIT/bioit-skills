# Partition reference — Mindwell and wICE

Captured **2026-08-13** from `sinfo`, `scontrol show partitions`, and
`sacctmgr show qos` on the live clusters. Partition inventories drift; re-derive
with:

```bash
sinfo -M mindwell,wice -o "%20P %10a %10l %6D %10c %12m %25G"
scontrol show partitions --clusters=mindwell
sacctmgr show qos normal,long,interactive,debug format=Name%20,MaxSubmitJobsPerUser%12,MaxTRESPerUser%30
```

Where the VSC docs and the live cluster disagree, **the live cluster is right**.
Two known doc errors: wICE `hugemem` is billed at 18.52 credits/core-min (docs
say 4.398), and the `dedicated_*` partitions are not documented at all.

## Mindwell

All node types have 192 cores. Login is shared with Genius/wICE
(`login.hpc.kuleuven.be`); Mindwell has no dedicated login nodes.

| Partition | Nodes | Mem/node | GPU | Max walltime | QoS | Def/Max mem per core (MiB) | Credits/core-min | Account required |
|---|---|---|---|---|---|---|---|---|
| `batch_graniterapids` *(default)* | 40 | 768 G | — | 3 d | `normal` | 4000 / 4000 | 2.604 | any credit account |
| `batch_graniterapids_long` | 40 | 768 G | — | 7 d | `long` | 4000 / 4000 | 2.604 | any credit account |
| `bigmem` | 10 | 1536 G | — | 3 d | `normal` | 8000 / 8000 | 3.038 | any credit account |
| `gpu_b200` | 3 | 1536 G | 8× B200 (192 G) | 3 d | `normal` | 8000 / 8000 | 3.038 + **437.50/GPU-min** | any credit account |
| `interactive` | 2 | 768 G | 2× RTX-5000 Ada (32 G) | 16 h | `interactive` | 2000 / 4000 | **0 (free)** | any credit account |
| `dedicated_big_bigmem` | 15 | 1536 G+ | — | 7 d | own | 8000 / 12050 | **0 (free)** | `lp_big_mindwell_cpu` only |
| `dedicated_big_gpu_b200` | 1 | 2313 G | 8× B200 | 7 d | own | 12050 / 12050 | **0 (free)** | `lp_big_mindwell_gpu_b200` only |

CPU: 2× Intel Xeon Platinum 6972P (Granite Rapids, 96 c each) for thin/bigmem/
interactive; 2× AMD EPYC 9655 (Turin) on the GPU nodes. Infiniband NDR, direct
liquid cooled. Local node disk (`$VSC_SCRATCH_NODE` = `/tmp`): 960 GB NVMe, 3840 GB
on bigmem.

Software modules exist only for toolchains **2024a+** (CPU) and **2025a+** (GPU).

`gpu_b200` per-GPU ceiling: **24 cores, 194400 MiB**. Exceeding it produces a
warning.

## wICE

| Partition | Nodes | Cores | Mem/node | GPU | Max walltime | QoS | Def/Max mem per core (MiB) | Credits/core-min | Account required |
|---|---|---|---|---|---|---|---|---|---|
| `batch` *(default)*, `batch_icelake` | 172 | 72 | 256 G | — | 3 d | `normal` | 3400 / 3400 | 2.546 | any |
| `batch_long`, `batch_icelake_long` | 172 | 72 | 256 G | — | 7 d | `long` | 3400 / 3400 | 2.546 | any |
| `batch_sapphirerapids` | 68 | 96 | 256 G | — | 3 d | `normal` | 2500 / 2500 | 3.472 | any |
| `batch_sapphirerapids_long` | 68 | 96 | 256 G | — | 7 d | `long` | 2500 / 2500 | 3.472 | any |
| `bigmem` | 5 | 72 | 2048 G | — | 3 d | `normal` | 28000 / 28000 | 4.398 | any |
| `hugemem` | 1 | 72 | 8 T | — | 3 d | `normal` | 111900 / 111900 | **18.519** | any |
| `gpu`, `gpu_a100` | 4 | 72 | 512 G | 4× A100 SXM4 (80 G) | 3 d | `normal` | 7000 / 7000 | 2.546 + 141.67/GPU-min | any |
| `gpu_h100` | 5 | 64 | 768 G | 4× H100 SXM5 (80 G) | 3 d | `normal` | 11700 / 11700 | 3.472 + **569.44/GPU-min** | any |
| `gpu_a100_debug` | 1 | 64 | 512 G | 1× A100 (no MIG) | 1 h | `debug` | 7500 / 7500 | 2.546 + 141.67 | any |
| `interactive` | 4 | 64 | 512 G | 1× A100 MIG 1g.10gb | 16 h | `interactive` | 2000 / 7500 | **0 (free)** | any |
| `dedicated_big_bigmem` | 16 | 72 | 2048 G | — | 7 d | own | 7000 / 28000 | **0 (free)** | `lp_big_wice_cpu` |
| `dedicated_big_gpu` | 4 | 72 | 1008 G | 4× A100 SXM4 | 7 d | own | 3400 / 14000 | **0 (free)** | `lp_big_wice_gpu` |
| `dedicated_big_gpu_small` | 1 | 72 | 1008 G | 8× A100 MIG 3g.40gb | 7 d | own | 3400 / 14000 | **0 (free)** | `lp_big_wice_gpu` |
| `dedicated_big_gpu_h100` | 3 | 64 | 1523 G | 4× H100 | 7 d | own | 3400 / 21000 | **0 (free)** | `lp_big_wice_gpu_h100` |

Also present but belonging to other groups: `dedicated_cytolab_bigmem`
(`lp_joris_vermeesch`), `dedicated_rega1_gpu` (`l_durable`, 21 d),
`dedicated_rega2_gpu` (`l_cev_division`).

`batch_icelake` is the same node set as `batch`; `gpu` the same as `gpu_a100`.
The H100 and hugemem nodes have **no high-performance interconnect** (ethernet
only) — do not use them for multi-node MPI.

Per-GPU ceilings: `gpu_a100` 18 cores / 126000 MiB; `gpu_h100` 16 / 187200.

## Accounts

`--account` is mandatory and is hard-locked to the partition — the "Account
required" column above is the authority, and the lock table in `SKILL.md` explains
which way it fails. Public partitions take an ordinary credit account (`<your-credit-account>`,
as listed by `sam-balance`); each `dedicated_*` partition takes only its own `lp_big_*`
account, and those accounts are actively denied on the public queues.

`sam-balance` lists the accounts you actually hold and their credits. Two things
it will tell you that the docs will not:

- The nominal balance on the `lp_big_*` accounts (often 1) is not a problem — the
  dedicated partitions bill at `CPU=0`, so those jobs never draw it down.
- `dedicated_big_gpu_h100` needs `lp_big_wice_gpu_h100`; check whether you have an
  association for it before writing a script against that partition.

`lp_mindwell_pilot` has expired and is gone from `sam-balance`, despite still
being advertised in the VSC docs.

## Credit arithmetic

```
CPU-only:  weight_cpu * effective_cores * walltime_minutes
With GPU:  (weight_cpu * cores + weight_gpu * gpus) * walltime_minutes
```

`effective_cores` is what Slurm *allocates*, not what you asked for — memory
over the per-core default and GPU binding both inflate it. `walltime` is the
requested limit, not the elapsed time, for `sam-quote` purposes.

Worked example — 24 h on 2 Mindwell B200 GPUs with 48 cores:
`(3.038 * 48 + 437.5 * 2) * 1440 ≈ 1.47 M credits`. The same job on
`dedicated_big_gpu_b200` costs **0**.

Tools: `sam-quote sbatch <script>` (pre-submission worst case), `sam-balance`,
`sam-statement --account=… --start=… --end=…` (slow; project leaders see all
users), `sam-list-usagerecords` (faster, usage only). Live weights come from
`scontrol show partitions --clusters=<cluster>`.

## Reference links

- Mindwell hardware: https://docs.vscentrum.be/leuven/tier2_hardware/mindwell_hardware.html
- Mindwell quick start: https://docs.vscentrum.be/leuven/mindwell_quick_start.html
- wICE hardware: https://docs.vscentrum.be/leuven/tier2_hardware/wice_hardware.html
- Slurm specifics (per-GPU limits, QoS): https://docs.vscentrum.be/leuven/slurm_specifics.html
- Credits: https://docs.vscentrum.be/leuven/credits.html
- Dedicated nodes: not in the public VSC docs. `scontrol -M <cluster> show partition
  dedicated_big_bigmem` (etc.) is the authority; ask your group's admin for access.
