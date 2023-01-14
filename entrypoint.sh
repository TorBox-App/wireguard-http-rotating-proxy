#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

/usr/bin/mitmproxy -s /wireguard-rotator.py