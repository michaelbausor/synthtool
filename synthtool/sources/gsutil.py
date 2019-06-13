# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pathlib
import re
import shutil
import subprocess
from typing import Dict, Tuple

from synthtool import _tracked_paths
from synthtool import cache
from synthtool import metadata
from synthtool import shell


def copy_dir_from_gcs(
    url: str,
    dest: pathlib.Path = None,
    parallel: bool = True,
) -> pathlib.Path:
    if dest is None:
        dest = cache.get_cache_dir()

    cmd = ['gsutil']

    if parallel:
        cmd.append('-m')

    cmd.extend(['cp', '-r', url, '.'])

    shell.run(cmd, cwd=str(dest))

    # TODO: add to synthtool metadata

    return dest / pathlib.Path(url).stem


def copy_file_from_gcs(
    url: str
    dest: pathlib.Path = None
) -> str:
    if dest is None:
        dest = cache.get_cache_dir()

    shell.run(['gsutil', 'cp', url, dest], cwd=str(dest))

    return dest / pathlib.Path(url).stem


def get_file_content_from_gcs(
    url: str
    dest: pathlib.Path = None
) -> str:
    file_dest = copy_file_from_gcs(url, dest=dest)
    with open(file_dest, 'r') as f:
        return f.read().strip()
