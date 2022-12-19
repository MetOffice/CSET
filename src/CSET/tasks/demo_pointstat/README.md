# METplus stats

The command generates the stats with METplus.

```bash
./run_metplus.sh
```

## VerPy plotting

This command plots the stats with VerPy.

```bash
cd verpy
python3 plot_met_stats.py --plot_dir ${PWD} --start 2022092103 --end 2022092603 --source /net/home/h02/fryl/NGVER/CSET/test_output/pt_ukv/Output --case_studies True --expids METO_UKV --model_names 'UKV - MET'
```
