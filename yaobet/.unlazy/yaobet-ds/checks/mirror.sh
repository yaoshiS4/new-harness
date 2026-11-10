#!/usr/bin/env bash
# genplan.py mirrors: for every pins.txt check row, the new key literal of the changed
# check line(s) appears in the new-side range of the genplan.py hunk that mirrors it.
# Prints MIRROR OK n/n.
LEAF=mirror; PORT=0
. "$(dirname "${BASH_SOURCE[0]}")/ds.sh"

need mirror-inputs "$DS_DIR/pins.txt" .unlazy/yaobet-rebuild/genplan.py || finish
helper mirror
n=$((N_OK + N_FAIL))
if [ "$N_FAIL" -eq 0 ] && [ "$N_OK" -gt 0 ]; then echo "MIRROR OK $N_OK/$n"; exit 0; fi
echo "MIRROR FAILED $N_FAIL/$n"; exit 1
