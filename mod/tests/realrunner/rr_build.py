"""DRBR real-runner tests (1.0.4): a PRIVATE test build of the game - the merged code given plus the autotest hook
(kat_hook.gml: a practice match, the attacks forced, a log and screenshots) - built with the release's own build script.
The hook is never in a release: it goes into a copy of the code in a sandbox, and the build is written next to it.
Usage: python3 rr_build.py <merged dir> <out.win> [sandbox dir]"""
import os, sys, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def patch(sbx):
    m = os.path.join(sbx, 'merged')
    p = os.path.join(m, 'gml_GlobalScript_knight_core.gml')
    t = open(p, encoding='utf8').read()
    a = 'function kbr_now()\n{\n    var _M = kbr_match();\n    if (is_undefined(_M) || !_M.go)\n        return -999999;\n'
    assert t.count(a) == 1, 'kbr_now'
    # the match clock in game frames (the test build may run slower than real time under software rendering)
    t = t.replace(a, a + '    if (variable_global_exists("kat") && is_struct(global.kat))\n        return global.kat.fgo;\n')
    b = 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st)\n{\n'
    assert t.count(b) == 1, 'kbr_tl_pick_attack'
    t = t.replace(b, b + '    if (variable_global_exists("kat") && is_struct(global.kat))\n        return global.kat.seq[_k mod array_length(global.kat.seq)];\n')
    t = t.rstrip('\n') + '\n' + open(os.path.join(HERE, 'kat_hook.gml'), encoding='utf8').read()
    open(p, 'w', encoding='utf8').write(t)
    q = os.path.join(m, 'gml_Object_obj_gamecontroller_Step_1.gml')
    s = open(q, encoding='utf8').read()
    assert s.startswith('kdr_frame();\n'), 'gamecontroller begin step'
    open(q, 'w', encoding='utf8').write(s.replace('kdr_frame();\n', 'kdr_frame();\nkat_tick();\n', 1))


def main():
    merged, out = sys.argv[1], sys.argv[2]
    sbx = sys.argv[3] if len(sys.argv) > 3 else out + '.sbx'
    if os.path.exists(sbx):
        shutil.rmtree(sbx)
    os.makedirs(sbx)
    shutil.copytree(merged, os.path.join(sbx, 'merged'))
    shutil.copy('/home/claude/work/build/assets.json', os.path.join(sbx, 'assets.json'))
    patch(sbx)
    env = dict(os.environ, DOTNET_ROOT='/home/claude/dotnet', PATH=os.environ['PATH'] + ':/home/claude/dotnet', BUILD_DIR=sbx,
               MODS_DIR='/home/claude/work/out', KNIGHTS_JSON='/home/claude/scripts/knights.json', STAGE='all')
    with open(os.path.join(sbx, 'build.log'), 'w') as lg:
        r = subprocess.run(['/home/claude/utmt_cli/UndertaleModCli', 'load', '/mnt/user-data/uploads/data.win', '-s', '/home/claude/scripts/build.csx',
                            '-o', out, '-f'], env=env, stdout=lg, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd='/home/claude/work')
    ok = r.returncode == 0 and os.path.exists(out)
    print('test build %s: %s (%s)' % (out, 'ok' if ok else 'FAILED', os.path.join(sbx, 'build.log')))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
