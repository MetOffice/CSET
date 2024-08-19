#!/bin/bash -l
#SBATCH --qos=high
#SBATCH --mem=15G
#SBATCH --ntasks=2
#SBATCH --time=120

export MPLBACKEND='Agg'
module load scitools

# Run CSET
python $HOME/CSET/lfric_parser.py $1
