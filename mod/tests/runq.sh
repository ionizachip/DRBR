#!/bin/bash
# usage: runq.sh KEY "pts" PARTY LOGFILE [env...]
cd /home/claude/work/tests
KH_MERGED=/home/claude/work/build_frozen3/merged/ WALL=${WALL:-150} python3 emu_atk.py pts $1 $2 "$3" 1500 > $4 2>&1
