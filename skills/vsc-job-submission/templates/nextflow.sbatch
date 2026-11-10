#!/bin/bash -l
# Nextflow driver job.
#
# The sbatch job is ONLY the Nextflow head process — 1 core, small memory, long
# walltime. Real compute is submitted as separate jobs by the slurm executor, so
# do not size this job for the pipeline's work.
#
# ---------------------------------------------------------------------------
# Mindwell, the recommended default. The -profile below must name the sub-profile of
# the cluster this job runs on (mindwell / mindwell_gpu / wice / wice_gpu): each
# one loads its own cluster module, so a mismatch sends every task to the other
# cluster. For wICE, see the variant at the bottom.
# ---------------------------------------------------------------------------
#SBATCH --clusters=mindwell
#SBATCH --partition=dedicated_big_bigmem
#SBATCH --account=lp_big_mindwell_cpu
#SBATCH --job-name=nf_run
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=168:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<your.email@kuleuven.be>

set -euo pipefail

# Work dir on the compute cluster's OWN scratch. Expanded HERE, on the compute
# node, which is the only place $VSC_SCRATCH resolves correctly — the same path
# string is Lustre on wICE and GPFS on Mindwell. Never resolve it on a login node
# and pass the result in.
export NXF_WORK="${VSC_SCRATCH}/work"
mkdir -p "${NXF_WORK}"

# The profile submits every task with this account. The head job's dedicated
# account is banned from the public partitions, so set a public one here.
export SLURM_ACCOUNT=<your-credit-account>

echo "Cluster : ${SLURM_CLUSTER_NAME}"
echo "NXF_WORK: ${NXF_WORK} -> $(readlink -f "${NXF_WORK}")"

# Results may live on project storage; only the work dir must be cluster-local.
# GPFS <your-gpfs-project> because the header above is Mindwell.
OUTDIR=${VSC_PROJECT_GPFS1}/<your-gpfs-project>/path/to/results

# micromamba is a shell function and is absent in batch jobs — use $MAMBA_EXE.
# -c files are applied in order and the LAST one wins, which matters for anything
# the institutional profile already sets (e.g. singularity.cacheDir).
"$MAMBA_EXE" run -n nextflow nextflow run <pipeline> \
    -profile vsc_kul_uhasselt,mindwell,singularity \
    --input samplesheet.csv \
    --outdir "${OUTDIR}" \
    -w "${NXF_WORK}" \
    -c ${VSC_PROJECT_GPFS1}/<your-gpfs-project>/<path/to>/custom_nf_configs/<overrides>.config \
    -resume

echo "Done."

# --- wICE variant ----------------------------------------------------------
# Only for a wICE-specific reason (A100/H100, inputs already on Lustre). Swap to:
#   #SBATCH --clusters=wice
#   #SBATCH --account=lp_big_wice_cpu            # partition stays dedicated_big_bigmem
#   -profile vsc_kul_uhasselt,wice,singularity   # or wice_gpu
# $VSC_SCRATCH then resolves to Lustre automatically, but the project paths do NOT --
# they are plain strings, not per-cluster symlinks. Swap OUTDIR and every -c path from
# ${VSC_PROJECT_GPFS1}/<your-gpfs-project> to ${VSC_PROJECT_LUSTRE1}/<your-lustre-project>, or the wICE
# run writes its results across to GPFS for the whole pipeline. Same for any
# --input, --fasta or params file pointing at project storage.
