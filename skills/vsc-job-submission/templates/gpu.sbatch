#!/bin/bash -l
# GPU batch job — Mindwell (B200).
#
# This uses the dedicated GPU node, which is FREE (billing weight 0)
# and allows 7-day walltimes. It accepts ONLY lp_big_mindwell_gpu_b200, and that
# account is banned from the public partitions.
#
# For the public GPU queue instead (3-day limit, and expensive — 437.5 credits
# per GPU-minute, so a 24h 2-GPU job is ~1.3M credits):
#   --partition=gpu_b200 --account=<your-credit-account>
#SBATCH --clusters=mindwell
#SBATCH --partition=dedicated_big_gpu_b200
#SBATCH --account=lp_big_mindwell_gpu_b200
#SBATCH --job-name=my_gpu_job
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=2
# Stay within the per-GPU ceiling: 24 cores and 194400 MiB per B200. Slurm binds
# CPUs to GPUs (GresEnforceBind=Yes), so the allocation is rounded up to whole
# per-GPU shares — sacct reporting more cores than requested is normal.
#SBATCH --cpus-per-task=24
#SBATCH --mem-per-cpu=12050M
#SBATCH --time=32:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<your.email@kuleuven.be>

set -euo pipefail

workdir="${VSC_SCRATCH}/${SLURM_JOB_NAME}/${SLURM_JOB_ID}"
mkdir -p "${workdir}"

nvidia-smi
echo "Allocated GPUs: ${CUDA_VISIBLE_DEVICES:-none}"

# Containerised GPU work: --nv passes the driver through. Bind every path the
# tool must read that is not already auto-mounted.
# The shared software/ tree exists on both project directories. Take the container
# from the one matching the cluster -- a Mindwell job loading its .sif from Lustre
# reads the whole image across the cluster boundary before it starts.
SIF=${VSC_PROJECT_GPFS1}/<your-gpfs-project>/software/singularity/<image>.sif

singularity exec --nv \
    -B "${workdir}" \
    -B "${VSC_PROJECT_GPFS1}/<your-gpfs-project>" \
    "${SIF}" \
    <command> --device cuda:all

echo "Done."
