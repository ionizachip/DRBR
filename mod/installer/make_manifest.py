#!/usr/bin/env python3
"""Generate KNIGHT_HUB_MANIFEST.txt for the Knight Hub installer.

Usage:
  make_manifest.py VANILLA PATCHED PATCH -o KNIGHT_HUB_MANIFEST.txt [options]

PATCH is either
  * a joined .xdelta file  -> it is split into parts of <= --part-size bytes
                              (default 29000000) written to --parts-out (default: folder of -o)
                              as <xdelta name>.part0, .part1, ...
  * a directory holding <name>.part0 .part1 ... (already split) -> used as is.

Unless --no-verify is given, the joined patch is applied to VANILLA with xdelta3 and the result
must hash to PATCHED (so a manifest is never written for a patch that does not work).

Options:
  --mod-version V        mod version string (default: dev)
  --mod-name N           default: Knight Hub
  --xdelta-name N        name of the joined patch (default: name of the .xdelta, or derived)
  --part-size BYTES      default 29000000
  --parts-out DIR        where to write the parts when splitting
  --xdelta3-exe PATH     record the SHA256 of the xdelta3.exe that ships beside the installer
  --music-dir DIR        folder (the 'mus' layout) to hash optional music from
  --music REL            optional music file, relative to the mus folder, '/' separators
                         (repeatable; default with --music-dir: the four standard files and build 47's seven songs)
  --xdelta3 PATH         xdelta3 used for verification (default: xdelta3 from PATH)
  --steam-file PATH      a Knight Fights Online Steam file that ships beside the installer (kf_steam.dll,
                         steam_api64.dll, steam_appid.txt): recorded as steam=<name>|<sha256> (repeatable)
  --no-verify            skip applying the patch
"""
import argparse, hashlib, os, re, subprocess, sys, tempfile

DEFAULT_MUSIC = ["knightmare_knight.ogg", "thorn_knight.ogg",
                 "its_nothing_but_garbage_noise.ogg", "superchargedknight/cleaver.ogg",
                 # build 47: the new fight songs (knight_hub_music.zip)
                 "kh_void_star.ogg", "kh_lv_crusher.ogg", "kh_true_hero.ogg", "kh_neotech_online.ogg",
                 "kh_storyshift_black.ogg", "kh_anywhere_you_go.ogg", "kh_ever_ascending.ogg",
                 # build 48: twelve more (knight_hub_music2.zip)
                 "kh_lost_dream.ogg", "kh_forget_me_not.ogg", "kh_hell_hammer.ogg", "kh_in_my_way.ogg", "kh_till_the_end.ogg", "kh_megalo_vania.ogg", "kh_megalo_strike_back.ogg", "kh_red_crimson_death.ogg", "kh_wrong_enemy.ogg", "kh_n1ght_of_n1ghtcore.ogg", "kh_that_feeling.ogg", "kh_identity_crisis.ogg",
                 # build 50: the Claude Music Handoff's 20 new songs (knight_hub_music3.zip / knight_hub_music4.zip)
                 "kh_blood.ogg", "kh_close_to_inevitability.ogg", "kh_dusttale_sonata.ogg", "kh_fraight_fest.ogg", "kh_heir_of_grief.ogg", "kh_megalovania_itsaleccio.ogg", "kh_neo_chaos.ogg", "kh_penumbra_phantasm.ogg", "kh_petal_dance.ogg", "kh_white_cell.ogg", "kh_chrysalis.ogg", "kh_deep_waters.ogg", "kh_hell_for_frandle.ogg", "kh_ice_shock.ogg", "kh_megalovania_sunhatgirl.ogg", "kh_our_flower_power.ogg", "kh_risen_up.ogg", "kh_venari.ogg", "kh_vs_susie_neo.ogg", "kh_wheel_of_misfortune.ogg"]

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vanilla"); ap.add_argument("patched"); ap.add_argument("patch")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--mod-version", default="dev")
    ap.add_argument("--mod-name", default="Knight Hub")
    ap.add_argument("--xdelta-name")
    ap.add_argument("--part-size", type=int, default=29000000)
    ap.add_argument("--parts-out")
    ap.add_argument("--xdelta3-exe")
    ap.add_argument("--music-dir")
    ap.add_argument("--music", action="append", default=[])
    ap.add_argument("--xdelta3", default="xdelta3")
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--steam-file", action="append", default=[])
    a = ap.parse_args()

    out_dir = os.path.dirname(os.path.abspath(a.output))
    parts = []   # (name, path)
    if os.path.isdir(a.patch):
        found = {}
        prefixes = set()
        for fn in os.listdir(a.patch):
            m = re.fullmatch(r"(.+)\.part(\d+)", fn)
            if m:
                prefixes.add(m.group(1)); found[int(m.group(2))] = fn
        if len(prefixes) != 1:
            sys.exit("expected exactly one <name>.partN family in %s, found %s" % (a.patch, sorted(prefixes)))
        xname = a.xdelta_name or prefixes.pop()
        if sorted(found) != list(range(len(found))):
            sys.exit("part numbers are not contiguous from 0: %s" % sorted(found))
        for i in range(len(found)):
            parts.append((found[i], os.path.join(a.patch, found[i])))
        # parts must be named <xname>.partN for the installer's naming convention (not required, just informative)
    else:
        xname = a.xdelta_name or os.path.basename(a.patch)
        pdir = a.parts_out or out_dir
        os.makedirs(pdir, exist_ok=True)
        i = 0
        with open(a.patch, "rb") as f:
            while True:
                buf = f.read(a.part_size)
                if not buf:
                    break
                name = "%s.part%d" % (xname, i)
                p = os.path.join(pdir, name)
                with open(p, "wb") as o:
                    o.write(buf)
                parts.append((name, p)); i += 1
        if not parts:
            sys.exit("patch file is empty")
    for name, p in parts:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
            sys.exit("part name not allowed by the installer: " + name)
        if os.path.getsize(p) > a.part_size:
            sys.exit("part larger than --part-size: " + name)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", xname):
        sys.exit("xdelta name not allowed by the installer: " + xname)

    # join (hash + optional file for verification)
    jh = hashlib.sha256(); jsize = 0
    joined_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xdelta")
    try:
        for name, p in parts:
            with open(p, "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    jh.update(b); joined_tmp.write(b); jsize += len(b)
        joined_tmp.close()
        van_sha = sha256_file(a.vanilla); pat_sha = sha256_file(a.patched)
        if not a.no_verify:
            outp = joined_tmp.name + ".out"
            r = subprocess.run([a.xdelta3, "-d", "-f", "-s", a.vanilla, joined_tmp.name, outp],
                               capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit("verification failed: xdelta3 exit %d: %s" % (r.returncode, r.stderr))
            ok = sha256_file(outp) == pat_sha
            os.remove(outp)
            if not ok:
                sys.exit("verification failed: patch applied to VANILLA does not give PATCHED")
            print("verified: patch applied to vanilla == patched")
    finally:
        if os.path.exists(joined_tmp.name):
            os.remove(joined_tmp.name)

    L = []
    L.append("# Knight Hub installer manifest - generated by make_manifest.py. Do not edit by hand.")
    L.append("schema=1")
    L.append("mod_name=" + a.mod_name)
    L.append("mod_version=" + a.mod_version)
    L.append("vanilla_size=%d" % os.path.getsize(a.vanilla))
    L.append("vanilla_sha256=" + van_sha)
    L.append("patched_size=%d" % os.path.getsize(a.patched))
    L.append("patched_sha256=" + pat_sha)
    L.append("xdelta_name=" + xname)
    L.append("xdelta_size=%d" % jsize)
    L.append("xdelta_sha256=" + jh.hexdigest())
    L.append("part_count=%d" % len(parts))
    for i, (name, p) in enumerate(parts):
        L.append("part.%d=%s|%d|%s" % (i, name, os.path.getsize(p), sha256_file(p)))
    if a.xdelta3_exe:
        L.append("xdelta3_exe_sha256=" + sha256_file(a.xdelta3_exe))
    music = a.music or (DEFAULT_MUSIC if a.music_dir else [])
    for rel in music:
        if rel.startswith("/") or ".." in rel.split("/") or "\\" in rel:
            sys.exit("bad music path: " + rel)
        sha = ""
        if a.music_dir:
            mp = os.path.join(a.music_dir, *rel.split("/"))
            if os.path.isfile(mp):
                sha = sha256_file(mp)
            else:
                print("warning: music file not found for hashing: " + mp, file=sys.stderr)
        L.append("music=" + rel + ("|" + sha if sha else ""))
    for sp in a.steam_file:
        nm = os.path.basename(sp)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", nm):
            sys.exit("steam file name not allowed by the installer: " + nm)
        L.append("steam=" + nm + "|" + sha256_file(sp))
    with open(a.output, "w", newline="\r\n", encoding="ascii") as f:
        f.write("\n".join(L) + "\n")
    print("wrote %s: %d part(s), xdelta %d bytes" % (a.output, len(parts), jsize))

if __name__ == "__main__":
    main()
