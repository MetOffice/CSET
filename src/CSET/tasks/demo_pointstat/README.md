# METplus Pointstat

You need to make a copy of the `user_system_local.conf.example` file with the
`.example` extension removed, and fill in the configuration options to suite
your local environment. Similarly the `run_metplus.sh.example` file also needs
its extension removed and the contained variables replaced.

Once these steps are done the stats can be generated with METplus.

```bash
./run_metplus.sh
```

## VerPy plotting

This command plots the stats with VerPy.

```bash
cd verpy
python3 plot_met_stats.py --plot_dir ${PWD} --start 2022092103 --end 2022092603 --source /path/to/output/test_output/pt_ukv/Output --case_studies True --expids METO_UKV --model_names 'UKV - MET'
```
