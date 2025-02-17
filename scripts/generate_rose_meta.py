#! /usr/bin/env python3
# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Generates the rose-meta.conf file from a template.

To use, simply execute this script and it will regenerate the rose-meta.conf
from its template.

$ ./scripts/generate_rose_meta.py
"""

from pathlib import Path

import jinja2

rose_meta_folder = Path(__file__).parent.parent / "cset-workflow/meta/"
source = rose_meta_folder / "rose-meta.conf.jinja2"
destination = rose_meta_folder / "rose-meta.conf"

env = jinja2.Environment(autoescape=False, lstrip_blocks=True, trim_blocks=True)
template = env.from_string(source.read_text())
destination.write_text(template.render())
