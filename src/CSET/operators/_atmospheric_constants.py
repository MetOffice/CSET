# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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
"""Constants for the atmosphere."""

# Reference pressure.
P0 = 1000.0  # hPa.

# Specific gas constant for dry air.
RD = 287.0  # J/kg/K.

# Specific gas constant for water vapour.
RV = 461.0  # J/kg/K.

# Specific heat capacity for dry air.
CPD = 1005.7  # J/kg/K.

# Latent heat of vaporization.
LV = 2.501e6  # J/kg/K.

# Reference vapour pressure.
E0 = 6.1078  # hPa.

# Reference temperature.
T0 = 273.15  # K.

# Ratio between mixing ratio of dry and moist air.
EPSILON = 0.622

# Ratio between specific gas constant and specific heat capacity.
KAPPA = RD / CPD
