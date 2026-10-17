#!/bin/bash
cd /home/claude/work/tests
for k in "$@"; do WALL=${WALL:-70} python3 t_sprmon.py $k ${FR:-450} > /home/claude/work/mon_$k.log 2>&1; done
echo finished > /home/claude/work/mon_done_$1.txt
