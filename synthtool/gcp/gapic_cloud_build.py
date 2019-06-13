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
from pathlib import Path
from typing import Optional

from synthtool import _tracked_paths
from synthtool import log
from synthtool import metadata
from synthtool.gcp import artman
from synthtool.sources import gsutil

#GOOGLEAPIS_URL: str = git.make_repo_clone_url("googleapis/googleapis")
#GOOGLEAPIS_PRIVATE_URL: str = git.make_repo_clone_url("googleapis/googleapis-private")
#LOCAL_GOOGLEAPIS: Optional[str] = os.environ.get("SYNTHTOOL_GOOGLEAPIS")

CLOUD_BUILD_PROJECT: str = 'vkit-pipeline'
CLOUD_BUILD_BUCKET_URI: str = f'gs://{CLOUD_BUILD_PROJECT}-cloud-build-artifacts/github_googleapis_googleapis'
CLOUD_BUILD_LATEST_SHA_FILE: str = 'cloud_build_latest'

CLOUD_BUILD_BUCKET_URI_OVERRIDE: Optional[str] = os.environ.get("SYNTHTOOL_CLOUD_BUILD_URI")


class GAPICCloudBuild:
    def __init__(self):
        self._googleapis = None
        self._googleapis_private = None
        self._artman = artman.Artman()

    def php_library(self, service: str, version: str, **kwargs) -> Path:
        return self._download_gapic_code(service, version, "php", **kwargs)

    def java_library(self, service: str, version: str, **kwargs) -> Path:
        return self._download_gapic_code(service, version, "java", **kwargs)

    def _download_gapic_code(
        self,
        service,
        version,
        language,
        gapic_dir=None,
        googleapis_sha=None,
        private=False,
        include_protos=False,
        generator_args=None,
    ):
        # map the language to the artman argument and subdir of genfiles
        LANGUAGE_DIRECTORY_NAME= {
            "go": (f"gapi-cloud-{service}-{version}-go", "go"),
            "java": (f"google-cloud-{service}-{version}-java", "java"),
            "php": (f"google-cloud-{service}-{version}-php", "php"),
        }

        if language not in LANGUAGE_DIRECTORY_NAME:
            raise ValueError("provided language unsupported")

        language_directory_name, gen_language = LANGUAGE_DIRECTORY_NAME[language]

        if CLOUD_BUILD_BUCKET_URI_OVERRIDE:
            gcs_uri = CLOUD_BUILD_BUCKET_URI_OVERRIDE
        else:
            gcs_uri = CLOUD_BUILD_BUCKET_URI

        # Get googleapis SHA
        if googleapis_sha is None:
            googleapis_sha = self._get_latest_googleapis_sha(gcs_uri)

        # Download the GAPIC directory
        if gapic_dir is None:
            gapic_dir = Path('gapic-cloud-build') / language_directory_name

        gapic_dir_gs_uri = f'{gcs_uri}/{googleapis_sha}/{gapic_dir}'

        log.debug(f"Running gsutil to fetch gapic directory: {gapic_dir_gs_uri}.")
        genfiles = gsutil.copy_dir_from_gcs(gapic_dir_gs_uri)

        if not genfiles.exists():
            raise FileNotFoundError(
                f"Unable to find files from gsutil: {genfiles}."
            )

        log.success(f"Downloaded code into {genfiles}.")

        # Get the *.protos files and put them in a protos dir in the output
        if include_protos:
            import shutil

            source_dir = googleapis / service_path.parent / version
            proto_files = source_dir.glob("**/*.proto")
            # By default, put the protos at the root in a folder named 'protos'.
            # Specific languages can be cased here to put them in a more language
            # appropriate place.
            proto_output_path = genfiles / "protos"
            if language == "python":
                # place protos alongsize the *_pb2.py files
                proto_output_path = genfiles / f"google/cloud/{service}_{version}/proto"
            os.makedirs(proto_output_path, exist_ok=True)

            for i in proto_files:
                log.debug(f"Copy: {i} to {proto_output_path / i.name}")
                shutil.copyfile(i, proto_output_path / i.name)
            log.success(f"Placed proto files into {proto_output_path}.")

        metadata.add_client_destination(
            source=gapic_dir_gs_uri,
            api_name=service,
            api_version=version,
            language=language,
            generator="gapic",
        )

        _tracked_paths.add(genfiles)
        return genfiles

    def _get_latest_googleapis_sha(self, gcs_uri):
          return gsutil.get_file_content_from_gcs(f'{gcs_uri}/{CLOUD_BUILD_LATEST_SHA_FILE}')
