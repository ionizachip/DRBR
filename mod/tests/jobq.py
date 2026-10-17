import subprocess,sys,os,time
from concurrent.futures import ThreadPoolExecutor
jobs=[l.rstrip('\n').split('|') for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
# line: key|points|party|log|ENV=VAL,ENV=VAL
def run(j):
    key,pts,party,log,envs=(j+[''])[:5]
    env=dict(os.environ); env['KH_MERGED']='/home/claude/work/build_frozen3/merged/'
    env.setdefault('WALL','150')
    for kv in envs.split(','):
        if '=' in kv:
            a,b=kv.split('=',1); env[a]=b
    with open(log,'w') as f:
        subprocess.run(['python3','emu_atk.py','pts',key,pts,party,'2000'],stdout=f,stderr=subprocess.STDOUT,env=env,cwd='/home/claude/work/tests')
with ThreadPoolExecutor(int(sys.argv[2])) as ex: list(ex.map(run,jobs))
print('queue done')
