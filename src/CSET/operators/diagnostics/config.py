# Copyright 2022 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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