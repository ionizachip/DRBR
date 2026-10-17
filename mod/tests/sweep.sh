#!/bin/bash
# usage: sweep.sh KEY NAMES(comma) PARTY OUT [WALL]
cd /home/claude/work/tests
WALL=${5:-200} python3 emu_atk.py names $1 $2 "$3" 1500 > $4 2>&1
