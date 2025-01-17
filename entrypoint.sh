#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

mitmproxy -s /wireguard-rotator.py