#!/bin/bash
cd /home/claude/work/tests
WALL=${WALL:-150} python3 emu_atk.py pts $1 $2 "${PARTY:-[1,2,3]}" 1500 > $3 2>&1
