#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec bash "$root/components/h3/scripts/check-upstream.sh" "$@"
