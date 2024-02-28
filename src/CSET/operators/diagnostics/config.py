import numpy as np

# Cell statistics config

long_name = "1-hourly mean precipitation rate"
short_name = "1hr_mean_precip"
thresholds = [0.5]
n_proc = 1
observations = ["GPM", "UK_radar_2km", "Darwin_radar_rain_2.5km"]
x_log = True
y_log = True
time_grouping = ["forecast_period"]
y_axis = "frequency"