cd /home/claude/work/tests
cat q53.txt | xargs -P 2 -I{} sh -c 'n=$(echo "{}" | tr " " "_"); python3 t_contract53.py {} > logs53/c53_$n.log 2>&1; echo "{} -> $?" >> logs53/q53_status.txt'
echo ALLDONE >> logs53/q53_status.txt
