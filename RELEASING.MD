Synthtool is released using releasetool. Follow the installation steps [here](https://github.com/googleapis/releasetool).

1. Update releasetool. `python3 -m pip install --upgrade gcp-releasetool`. 
1. Go to the top level directory for `synthtool`.
1. `git fetch --tags`. This ensures you have the most recent tagged release.
1. Run releasetool `releasetool start`. Releasetool creates a release PR.
1. Once the PR is approved and merged, Autorelease will find the PR and finish the release process (tagging and publishing to PyPI).
