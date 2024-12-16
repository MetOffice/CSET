# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""
Age of air operator.

The age of air diagnostic provides a qualtitative view of how old air is within
the domain, by calculating a back trajectory at each grid point at each lead time
to determine when air entered through the lateral boundary. This is useful for
diagnosing how quickly air ventilates the domain, depending on its size and the
prevailing meteorology.

The diagnostic uses the u, v and w components of wind, along with geopotential height to
perform the back trajectory. Data is first regridded to 0.5 degrees.

Note: the code here does not consider sub-grid transport, and only uses the postprocessed
velocity fields and geopotential height. Its applicability is for large-scale flow O(1000 km),
and not small scale flow where mixing is likely to play a larger role.
"""
