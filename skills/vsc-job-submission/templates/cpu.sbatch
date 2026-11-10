#!/bin/bash -l
# CPU batch job — Mindwell. The `-l` is required: without it ~/.bashrc never
# runs and $PATH, the cluster module and $MAMBA_EXE are all missing.
#
# Public partition => a real credit account (<your-credit-account>, e.g. lp_mylab).
# For the free dedicated nodes (if sam-balance shows you have access) instead, use:
#   --partition=dedicated_big_bigmem --account=lp_big_mindwell_cpu
# The two sets are mutually exclusive and enforced by Slurm.
#SBATCH --clusters=mindwell
#SBATCH --partition=batch_graniterapids
#SBATCH --account=<your-credit-account>
#SBATCH --job-name=my_job
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
# 4000M is the per-core ceiling on batch_graniterapids. Asking for more does NOT
# give the task more memory — it allocates (and bills) extra cores. Need more
# per core? Use bigmem (8000M) or dedicated_big_bigmem (12050M).
#SBATCH --mem-per-cpu=4000M
#SBATCH --time=24:00:00
# Logs on the SAME cluster's scratch. $VSC_SCRATCH resolves per node: GPFS here,
# Lustre on wICE. Do not hardcode /scratch/leuven/... for a Mindwell job.
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<your.email@kuleuven.be>

set -euo pipefail

# Per-job scratch on the local cluster's filesystem, cleaned up at the end.
workdir="${VSC_SCRATCH}/${SLURM_JOB_NAME}/${SLURM_JOB_ID}"
mkdir -p "${workdir}"
trap 'rm -rf "${workdir}"' EXIT

echo "Job ${SLURM_JOB_ID} on $(hostname), cluster ${SLURM_CLUSTER_NAME}"
echo "Work dir: ${workdir} -> $(readlink -f "${workdir}")"

# --- stage inputs in -------------------------------------------------------
# Use cp, not mv or `rsync -a`: those preserve the original atime, and scratch
# files not ACCESSED for 30 days are deleted automatically.
# GPFS project storage, matching the Mindwell header above. On wICE this would be
# ${VSC_PROJECT_LUSTRE1}/<your-lustre-project> instead -- project paths do NOT resolve per
# cluster the way $VSC_SCRATCH does, so they have to be swapped by hand.
INPUT_DIR=${VSC_PROJECT_GPFS1}/<your-gpfs-project>/path/to/input
cp -r "${INPUT_DIR}"/. "${workdir}/"

cd "${workdir}"

# --- do the work -----------------------------------------------------------
# micromamba is a shell function and does not exist in batch jobs; use $MAMBA_EXE
# or an absolute path into the env.
"$MAMBA_EXE" run -n <env> <command> --threads "${SLURM_CPUS_PER_TASK}"

# --- copy results out ------------------------------------------------------
RESULTS_DIR=${VSC_PROJECT_GPFS1}/<your-gpfs-project>/path/to/results
mkdir -p "${RESULTS_DIR}"
rsync -a --include='*/' --include='*.out' --exclude='*' "${workdir}/" "${RESULTS_DIR}/"

echo "Done."
