// DRBR core tests - the same code the Windows programs run, on .NET (here: Linux). Real inputs: the real vanilla Chapter 3
// data.win, the real release payload (the real game patch), the provided starting save, a real signing key.
// Env: DRBR_TEST_VANILLA (vanilla data.win), DRBR_TEST_PAYLOAD (payload dir), DRBR_TEST_KEY (private key .pem),
//      DRBR_TEST_WORK (scratch dir), DRBR_TEST_RELEASES (the test releases served over HTTP: make_test_releases.py) + DRBR_TEST_HTTP (its URL)
// Usage: drbr-tests [group ...]   groups: basics signature manifest save game install repair failures interrupt update join uninstall
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

namespace Drbr
{
    static class Tests
    {
        static int pass, fail;
        static readonly List<string> Fails = new List<string>();
        static string Work, Vanilla, PayloadDir, Key;

        static void Ok(bool c, string what)
        {
            if (c) { pass++; Console.WriteLine("ok   " + what); }
            else { fail++; Fails.Add(what); Console.WriteLine("FAIL " + what); }
        }

        static string Throws(Action a)
        {
            try { a(); return null; }
            catch (Exception e) { return (e is DrbrException ? ((DrbrException)e).Code + ": " : e.GetType().Name + ": ") + e.Message; }
        }

        static int Main(string[] args)
        {
            Work = Env("DRBR_TEST_WORK", Path.Combine(Path.GetTempPath(), "drbr-tests"));
            Vanilla = Env("DRBR_TEST_VANILLA", "/mnt/user-data/uploads/data.win");
            PayloadDir = Env("DRBR_TEST_PAYLOAD", null);
            Key = Env("DRBR_TEST_KEY", null);
            Directory.CreateDirectory(Work);
            Log.Open(Path.Combine(Work, "logs"), "DRBR tests");
            HashSet<string> want = new HashSet<string>(args);
            Action<string, Action> G = (n, f) =>
            {
                if (want.Count > 0 && !want.Contains(n)) return;
                Console.WriteLine("== " + n);
                try { f(); } catch (Exception e) { Ok(false, n + " crashed: " + e); }
            };
            G("basics", Basics);
            G("signature", SignatureTests);
            G("manifest", ManifestTests);
            G("save", SaveTests);
            G("game", GameTests);
            G("install", InstallTests);
            G("repair", RepairTests);
            G("failures", FailureTests);
            G("interrupt", InterruptTests);
            G("update", UpdateTests);
            G("join", JoinTests);
            G("uninstall", UninstallTests);
            // not in the default run: a real release on the internet (DRBR_TEST_LIVE_URL), read the launcher's way
            if (want.Contains("live")) { Console.WriteLine("== live"); try { LiveTests(); } catch (Exception e) { Ok(false, "live crashed: " + e); } }
            Console.WriteLine("drbr core tests: " + (pass + fail) + " checks, " + fail + " failed");
            foreach (string f in Fails) Console.WriteLine("FAILED: " + f);
            return fail == 0 ? 0 : 1;
        }

        static string Env(string k, string d) { string v = Environment.GetEnvironmentVariable(k); return string.IsNullOrEmpty(v) ? d : v; }

        // the test releases' versions (make_test_releases.py): the payload's own version with n added to its last number
        // (DRBR 1.0.1: they were fixed 1.0.1-1.0.5, so testing a 1.0.1 payload, its "updates" were not newer than it)
        static string TestVer(int n)
        {
            string b = Json.ParseObject(File.ReadAllText(Path.Combine(PayloadDir, "payload.json"))).Str("version", "1.0.0");
            string[] parts = b.Split('.');
            parts[parts.Length - 1] = (int.Parse(parts[parts.Length - 1], CultureInfo.InvariantCulture) + n).ToString(CultureInfo.InvariantCulture);
            return string.Join(".", parts);
        }

        // ------------------------------------------------------------------------------------------------ helpers
        static string Sh(string cmd)
        {
            string o;
            int rc = Proc.Run("/bin/sh", "-c \"" + cmd.Replace("\"", "\\\"") + "\"", Work, out o);
            if (rc != 0) throw new Exception("command failed (" + rc + "): " + cmd + "\n" + o);
            return o;
        }

        static void Link(string src, string dst)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            if (File.Exists(dst)) File.Delete(dst);
            Sh("ln '" + src + "' '" + dst + "' 2>/dev/null || cp '" + src + "' '" + dst + "'");
        }

        static Dictionary<string, string> Snapshot(string dir)
        {
            Dictionary<string, string> d = new Dictionary<string, string>();
            if (!Directory.Exists(dir)) return d;
            foreach (string f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories)) d[Fs.Rel(dir, f)] = new FileInfo(f).Length + ":" + Hash.Sha256File(f);
            return d;
        }

        static bool SameSnap(Dictionary<string, string> a, Dictionary<string, string> b, out string diff)
        {
            List<string> d = new List<string>();
            foreach (var kv in a) { string v; if (!b.TryGetValue(kv.Key, out v)) d.Add("-" + kv.Key); else if (v != kv.Value) d.Add("~" + kv.Key); }
            foreach (var k in b.Keys) if (!a.ContainsKey(k)) d.Add("+" + k);
            diff = string.Join(" ", d.Take(12));
            return d.Count == 0;
        }

        /// <summary>A Steam-like DELTARUNE folder: the real vanilla data.win (hard link), a stand-in DELTARUNE.exe, Chapter 3's
        /// kind of files (sounds, language, videos, options), the music folder, and the leftovers of the old in-place Knight
        /// Hub that DRBR must never copy.</summary>
        static string FakeGame(string name, bool knightHubInPlace = false)
        {
            string g = Path.Combine(Work, name);
            if (Directory.Exists(g)) Fs.DeleteDir(g);
            string ch = Path.Combine(g, "chapter3_windows");
            Directory.CreateDirectory(Path.Combine(ch, "lang"));
            Directory.CreateDirectory(Path.Combine(ch, "vid"));
            Directory.CreateDirectory(Path.Combine(g, "mus", "superchargedknight"));
            File.WriteAllText(Path.Combine(g, "DELTARUNE.exe"), "stand-in runner");
            File.WriteAllText(Path.Combine(g, "options.ini"), "[Windows]\r\nSleepMargin=30\r\nUsex64=True\r\n");
            File.WriteAllText(Path.Combine(ch, "options.ini"), "[Windows]\r\nSleepMargin=30\r\nUsex64=True\r\n[Easing_and_Tweening]\r\n");
            File.WriteAllBytes(Path.Combine(ch, "audiogroup1.dat"), Encoding.ASCII.GetBytes(new string('a', 5000)));
            File.WriteAllBytes(Path.Combine(ch, "snd_icespell.ogg"), Encoding.ASCII.GetBytes("OggS sound"));
            File.WriteAllBytes(Path.Combine(ch, "AUDIO_INTRONOISE.ogg"), Encoding.ASCII.GetBytes("OggS intro"));
            File.WriteAllText(Path.Combine(ch, "lang", "lang_ja.json"), "{\"x\":1}");
            File.WriteAllBytes(Path.Combine(ch, "vid", "tennaIntroF1_compressed_28.mp4"), new byte[3000]);
            File.WriteAllBytes(Path.Combine(g, "mus", "knight.ogg"), Encoding.ASCII.GetBytes("OggS knight"));
            File.WriteAllBytes(Path.Combine(g, "mus", "joker.ogg"), Encoding.ASCII.GetBytes("OggS joker"));
            File.WriteAllBytes(Path.Combine(g, "mus", "superchargedknight", "other.ogg"), Encoding.ASCII.GetBytes("OggS sk"));
            // leftovers DRBR must not copy (a stray save, mod files, logs, the old package)
            File.WriteAllText(Path.Combine(ch, "filech3_1"), "a stray save");
            File.WriteAllText(Path.Combine(ch, "knight_hub_install.log"), "log");
            File.WriteAllText(Path.Combine(ch, "KNIGHT_HUB_MANIFEST.txt"), "old");
            File.WriteAllBytes(Path.Combine(ch, "knight_hub_chapter3.xdelta.part0"), new byte[1000]);
            Directory.CreateDirectory(Path.Combine(ch, "Knight Hub v2 (build 10)"));
            File.WriteAllText(Path.Combine(ch, "Knight Hub v2 (build 10)", "README.txt"), "old");
            File.WriteAllText(Path.Combine(g, "dxgi.dll"), "another mod");
            if (knightHubInPlace)
            {
                Link(Vanilla, Path.Combine(ch, "data.win.vanilla"));
                File.WriteAllBytes(Path.Combine(ch, "data.win"), new byte[60 * 1048576]);   // stands in for an older Knight Hub data.win
                File.WriteAllText(Path.Combine(ch, "knight_hub_build.txt"), "mod_version=51\r\n");
            }
            else Link(Vanilla, Path.Combine(ch, "data.win"));
            return g;
        }

        static DrbrPaths NewPaths(string name)
        {
            string r = Path.Combine(Work, name);
            if (Directory.Exists(r)) Fs.DeleteDir(r);
            string sa = Path.Combine(Work, name + "-savearea");
            if (Directory.Exists(sa)) Fs.DeleteDir(sa);
            Directory.CreateDirectory(sa);
            // the player's own saves (stand-ins) and the mod's settings
            File.WriteAllText(Path.Combine(sa, "filech3_0"), "player's own chapter 3 save");
            File.WriteAllText(Path.Combine(sa, "filech3_9"), "player's own chapter 3 save copy");
            File.WriteAllText(Path.Combine(sa, "filech2_0"), "player's own chapter 2 save");
            File.WriteAllText(Path.Combine(sa, "dr.ini"), "[G3_0]\r\nName=\"KRIS\"\r\n");
            File.WriteAllText(Path.Combine(sa, "keyconfig_0.ini"), "[KEYBOARD_CONTROLS]\r\n0=40\r\n");
            File.WriteAllText(Path.Combine(sa, "knightfights_online.ini"), "[online]\r\nskin=3\r\n");
            return new DrbrPaths(r, sa);
        }

        static Manifest Payload() { return Manifest.Load(Path.Combine(PayloadDir, "payload.json")); }

        // ------------------------------------------------------------------------------------------------ groups
        static void Basics()
        {
            JsonObject o = Json.ParseObject("{\"a\": 1, \"b\": [true, null, 2.5, \"x\\\"y\\u0041\"], \"c\": {\"d\": -3}}");
            Ok(o.Long("a") == 1 && o.Arr("b").Count == 4 && (string)o.Arr("b")[3] == "x\"yA" && o.Obj("c").Long("d") == -3, "JSON reads objects, arrays, escapes");
            Ok(Json.ParseObject(Json.Write(o)).Obj("c").Long("d") == -3, "JSON writes what it reads");
            Ok(Throws(() => Json.Parse("{\"a\": }")) != null && Throws(() => Json.Parse("[1,2")) != null, "JSON refuses broken text");
            Ok(Ver.Compare("1.2.10", "1.2.9") > 0 && Ver.Compare("1.0", "1.0.0") == 0 && Ver.Compare("1.0.0-beta", "1.0.0") < 0 && Ver.IsNewer("v2.0.0", "1.9.9"), "versions compare by number");
            Ok(Throws(() => Fs.Under(Work, "../escape")) != null && Throws(() => Fs.Under(Work, "a/../../b")) != null && Fs.Under(Work, "a/b").StartsWith(Work), "paths cannot leave their folder");
            Ok(GameCheck.IsVanillaChapterFile("snd_x.ogg") && GameCheck.IsVanillaChapterFile("lang/lang_ja.json") && GameCheck.IsVanillaChapterFile("vid/a.mp4") &&
               GameCheck.IsVanillaChapterFile("options.ini") && !GameCheck.IsVanillaChapterFile("data.win") && !GameCheck.IsVanillaChapterFile("filech3_1") &&
               !GameCheck.IsVanillaChapterFile("kf_steam.dll") && !GameCheck.IsVanillaChapterFile("mus/a.ogg") && !GameCheck.IsVanillaChapterFile("knight_hub_install.log"),
               "only Chapter 3's own files are copied from the player's game");
            string vdf = Path.Combine(Work, "libraryfolders.vdf");
            File.WriteAllText(vdf, "\"libraryfolders\"\n{\n\t\"0\"\n\t{\n\t\t\"path\"\t\t\"C:\\\\Program Files (x86)\\\\Steam\"\n\t}\n\t\"1\"\n\t{\n\t\t\"path\"\t\t\"D:\\\\SteamLibrary\"\n\t}\n}\n");
            List<string> libs = GameLocator.LibraryFolders(vdf);
            Ok(libs.Count == 2 && libs[1] == @"D:\SteamLibrary", "Steam's library list is read (custom library folders) " + string.Join("|", libs));
        }

        static void SignatureTests()
        {
            if (Key == null) { Ok(false, "DRBR_TEST_KEY is not set"); return; }
            byte[] data = Encoding.UTF8.GetBytes("{\"schema\": 1, \"version\": \"9.9.9\"}");
            string f = Path.Combine(Work, "sig-test.json");
            File.WriteAllBytes(f, data);
            Sh("openssl dgst -sha256 -sign '" + Key + "' -out '" + f + ".bin' '" + f + "' && base64 -w0 '" + f + ".bin' > '" + f + ".sig'");
            string sig = File.ReadAllText(f + ".sig");
            Ok(Signature.Verify(data, sig), "a manifest signed with DRBR's release key verifies with the key built into DRBR");
            byte[] t = (byte[])data.Clone(); t[5] ^= 1;
            Ok(!Signature.Verify(t, sig), "one changed byte: refused");
            Ok(!Signature.Verify(data, "AAAA" + sig.Substring(4)) && !Signature.Verify(data, "not base64!") && !Signature.Verify(data, ""), "a damaged / missing signature: refused");
            Sh("openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out '" + Work + "/other.pem' 2>/dev/null && openssl dgst -sha256 -sign '" + Work + "/other.pem' -out '" + f + ".o' '" + f + "' && base64 -w0 '" + f + ".o' > '" + f + ".osig'");
            Ok(!Signature.Verify(data, File.ReadAllText(f + ".osig")), "signed by another key: refused");
        }

        static void ManifestTests()
        {
            Manifest m = Payload();
            Ok(m.Version.Length > 0 && m.FullPatch != null && m.Template != null && m.SupportedGameBuilds.Count > 0 && m.Music.Count > 0, "the release payload.json reads (" + m.Version + ", " + m.Files.Count + " files, " + m.Music.Count + " songs)");
            Ok(m.SaveProfile.StartingRoomId == 30108 && m.SaveProfile.StartingPlot == 320 && m.SaveProfile.StartingLocation == "room_dw_snow_zone", "its save profile: room_dw_snow_zone (30108), story point 320");
            string raw = File.ReadAllText(Path.Combine(PayloadDir, "payload.json"));
            Ok(Throws(() => Manifest.Parse(raw.Replace("\"file\": \"start_filech3\"", "\"file\": \"../../start_filech3\""))) != null, "a file name that leaves the folder: refused");
            Ok(Throws(() => Manifest.Parse(raw.Replace("\"product\": \"DRBR\"", "\"product\": \"OTHER\""))) != null, "another product's manifest: refused");
            Ok(Throws(() => Manifest.Parse(raw.Replace("\"schema\": 1", "\"schema\": 2"))) != null, "a newer manifest schema: refused (needs a newer launcher)");
            Ok(InstallEngine.VerifyPayload(PayloadDir) != null, "the payload verifies byte for byte");
        }

        static void SaveTests()
        {
            Manifest m = Payload();
            byte[] tpl = File.ReadAllBytes(Path.Combine(PayloadDir, "start_filech3"));
            Ok(Hash.Sha256Bytes(tpl) == "fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082", "the payload's starting save is the provided save, byte for byte");
            Ok(SaveProfile.ValidateTemplate(tpl, m.SaveProfile) == "", "the provided save validates: a Chapter 3 save at room 30108, story point 320");
            long plot, room;
            SaveProfile.ReadStart(tpl, out plot, out room);
            Ok(plot == 320 && room == 30108, "its story point / room read from the file " + plot + " " + room);
            Ok(SaveProfile.CheckSaveFormat(tpl.Take(tpl.Length / 2).ToArray()).Contains("3055"), "a cut-off save: not a Chapter 3 save");
            byte[] t2 = (byte[])tpl.Clone(); t2[2000] ^= 1;
            Ok(SaveProfile.ValidateTemplate(t2, m.SaveProfile).Contains("checksum"), "one changed byte: refused (checksum)");
            byte[] t3 = Encoding.UTF8.GetBytes(Encoding.UTF8.GetString(tpl).Replace("30108 \r\n", "30107 \r\n"));
            SaveProfileInfo noHash = new SaveProfileInfo { TemplateSha256 = "", StartingRoomId = 30108, StartingPlot = 320 };
            Ok(SaveProfile.ValidateTemplate(t3, noHash).Contains("expected start"), "a save in another room: refused (not the pre-Knight room)");
            Ok(SaveProfile.CheckSaveFormat(Encoding.UTF8.GetBytes("hello\r\nworld")).Length > 0 && SaveProfile.CheckSaveFormat(new byte[0]).Length > 0, "unsupported formats: a clear error");
            string cfg = SaveProfile.CfgText(m.SaveProfile, "continue");
            Ok(cfg.Contains("start_mode=continue\r\n") && cfg.Contains("starting_room_id=30108\r\n") && cfg.Contains("save_template_version=1\r\n"), "the profile config the game reads");
            Ok(SaveProfile.CfgText(m.SaveProfile, "anything").Contains("start_mode=template"), "an unknown start mode means template");
            // RESTORE STARTING SAVE: only the DRBR story saves move; the DRBR controls stay; the player's own saves are not involved
            DrbrPaths p = NewPaths("save-restore");
            Directory.CreateDirectory(p.LiveProfile);
            File.WriteAllText(Path.Combine(p.LiveProfile, "filech3_0"), "drbr save");
            File.WriteAllText(Path.Combine(p.LiveProfile, "filech3_9"), "drbr save copy");
            File.WriteAllText(Path.Combine(p.LiveProfile, "dr.ini"), "[G3_0]");
            File.WriteAllText(Path.Combine(p.LiveProfile, "keyconfig_0.ini"), "keys");
            SortedDictionary<string, string> before = SaveProfile.VanillaSnapshot(p.SaveArea);
            int n = SaveProfile.RestoreStartingSave(p);
            Ok(n == 3 && !File.Exists(Path.Combine(p.LiveProfile, "filech3_0")) && File.Exists(Path.Combine(p.LiveProfile, "keyconfig_0.ini")), "RESTORE STARTING SAVE moves the DRBR story saves aside (3), keeps the DRBR controls");
            Ok(Directory.GetDirectories(p.BackupDir).Length == 1, "  ... into backups (nothing is deleted)");
            Ok(SaveProfile.CompareSnapshots(before, SaveProfile.VanillaSnapshot(p.SaveArea)).Count == 0, "  ... the player's own saves are untouched");
            File.WriteAllText(Path.Combine(p.SaveArea, "filech3_0"), "changed");
            Ok(SaveProfile.CompareSnapshots(before, SaveProfile.VanillaSnapshot(p.SaveArea)).Contains("filech3_0 changed"), "the snapshot notices a changed player save");
            // migrations: a profile from a newer DRBR is refused; the first run writes profile.json
            Ok(SaveProfile.Migrate(p, m.SaveProfile).Count >= 0 && File.Exists(Path.Combine(p.SaveProfileDir, "profile.json")), "the profile record is written (profile.json)");
            File.WriteAllText(Path.Combine(p.SaveProfileDir, "profile.json"), "{\"schema_version\": 99}");
            Ok(Throws(() => SaveProfile.Migrate(p, m.SaveProfile)) != null, "a profile made by a newer DRBR: refused with a message");
        }

        static void GameTests()
        {
            Manifest m = Payload();
            string g1 = FakeGame("game-vanilla");
            GameReport r1 = GameCheck.Inspect(g1, m.SupportedGameBuilds);
            Ok(r1.Compatible && r1.State == "vanilla" && r1.VanillaSource.EndsWith("data.win"), "a vanilla DELTARUNE: compatible (" + r1.Summary + ")");
            Ok(r1.Notes.Any(x => x.Contains("dxgi.dll")), "another mod's DLL in the game folder is noticed");
            string g2 = FakeGame("game-kh", true);
            GameReport r2 = GameCheck.Inspect(g2, m.SupportedGameBuilds);
            Ok(r2.Compatible && r2.State == "knight_hub_in_place" && r2.VanillaSource.EndsWith("data.win.vanilla"), "the old in-place Knight Hub: DRBR uses its verified clean backup (" + r2.State + ")");
            // a modified data.win of the SAME size as the vanilla one, with the clean backup next to it (update 10: the backup
            // was refused here - its checksum was taken from data.win when the sizes matched)
            string g2s = FakeGame("game-kh-samesize", true);
            string dws = Path.Combine(g2s, "chapter3_windows", "data.win");
            File.Delete(dws);
            File.Copy(Vanilla, dws);
            using (FileStream fs = new FileStream(dws, FileMode.Open, FileAccess.Write)) { fs.Seek(1000, SeekOrigin.Begin); byte[] b = Encoding.ASCII.GetBytes("KNIGHT HUB IN PLACE"); fs.Write(b, 0, b.Length); }
            GameReport r2s = GameCheck.Inspect(g2s, m.SupportedGameBuilds);
            Ok(r2s.Compatible && r2s.State == "knight_hub_in_place" && r2s.VanillaSource.EndsWith("data.win.vanilla"), "a changed data.win of the vanilla size, with the clean backup: the backup is used (" + r2s.State + ")");
            Fs.DeleteDir(g2s);
            File.Delete(Path.Combine(g2, "chapter3_windows", "data.win.vanilla"));
            GameReport r3 = GameCheck.Inspect(g2, m.SupportedGameBuilds);
            Ok(!r3.Compatible && r3.Summary.Contains("Verify integrity"), "a modified data.win with no clean backup: not compatible, says how to fix it");
            List<SupportedBuild> other = new List<SupportedBuild> { new SupportedBuild { Name = "x", Size = 1, Sha256 = new string('0', 64) } };
            GameReport r4 = GameCheck.Inspect(g1, other);
            Ok(!r4.Compatible && r4.State == "unsupported", "an unsupported game version: refused with a message");
            GameReport r5 = GameCheck.Inspect(Path.Combine(Work, "nowhere"), m.SupportedGameBuilds);
            Ok(!r5.Found && !r5.Compatible, "no DELTARUNE there: not found");
        }

        static DrbrPaths installed;
        static string steamGame;

        static void InstallTests()
        {
            DrbrPaths p = NewPaths("drbr-install");
            steamGame = FakeGame("steam-game");
            Dictionary<string, string> steamBefore = Snapshot(steamGame);
            SortedDictionary<string, string> savesBefore = SaveProfile.VanillaSnapshot(p.SaveArea);
            List<int> pct = new List<int>();
            InstallResult r = new InstallEngine(p).Install(new InstallOptions { GameDir = steamGame, PayloadDir = PayloadDir, Shortcuts = false, RegisterUninstall = false, Progress = (t, x) => pct.Add(x) });
            Manifest m = Payload();
            Ok(r.Ok && r.Version == m.Version, "fresh install: DRBR " + r.Version);
            Ok(Hash.Sha256File(p.DataWin) == m.DrbrDataWinSha256, "DRBR's data.win is built (real vanilla data.win + the real patch = the DRBR build)");
            Ok(Hash.Sha256File(p.BundleTemplate) == m.SaveProfile.TemplateSha256, "the provided starting save is next to it (drbr_data/start_filech3)");
            Ok(File.ReadAllText(p.BundleProfileCfg).Contains("start_mode=template"), "the profile config: start from the starting save");
            Ok(File.Exists(p.GameExe) && File.Exists(Path.Combine(p.Chapter3, "audiogroup1.dat")) && File.Exists(Path.Combine(p.Chapter3, "lang", "lang_ja.json")) &&
               File.Exists(Path.Combine(p.Chapter3, "vid", "tennaIntroF1_compressed_28.mp4")) && File.Exists(Path.Combine(p.Chapter3, "options.ini")), "the game's own files are copied (exe, sounds, language, videos, options)");
            Ok(File.Exists(Path.Combine(p.Chapter3, "mus", "joker.ogg")) && File.Exists(Path.Combine(p.Chapter3, "mus", "superchargedknight", "other.ogg")), "the game's music is next to DRBR's data.win (mus)");
            Ok(m.Music.All(x => File.Exists(Fs.Under(Path.Combine(p.Chapter3, "mus"), x.Rel))), "every DRBR song is installed (" + m.Music.Count + ")");
            Ok(File.Exists(Path.Combine(p.Chapter3, "kf_steam.dll")) && File.Exists(Path.Combine(p.Chapter3, "steam_appid.txt")) && Directory.Exists(Path.Combine(p.Chapter3, "kfsongs")), "the multiplayer files and the song pack");
            Ok(File.Exists(p.LauncherExe) && File.Exists(p.UpdaterExe) && File.Exists(p.Xdelta), "DRBR Launcher, DRBR Updater and xdelta3 are installed");
            Ok(!File.Exists(Path.Combine(p.Chapter3, "filech3_1")) && !File.Exists(Path.Combine(p.Chapter3, "knight_hub_install.log")) && !File.Exists(Path.Combine(p.Chapter3, "KNIGHT_HUB_MANIFEST.txt")) &&
               !Directory.Exists(Path.Combine(p.Chapter3, "Knight Hub v2 (build 10)")) && !File.Exists(Path.Combine(p.GameDir, "dxgi.dll")) && !File.Exists(Path.Combine(p.Chapter3, "knight_hub_chapter3.xdelta.part0")),
               "nothing else from the player's game folder is copied (stray save, old mod files, other mods)");
            string diff;
            Ok(SameSnap(steamBefore, Snapshot(steamGame), out diff), "the player's DELTARUNE folder is byte for byte unchanged " + diff);
            Ok(SaveProfile.CompareSnapshots(savesBefore, SaveProfile.VanillaSnapshot(p.SaveArea)).Count == 0, "the player's own DELTARUNE saves are unchanged");
            Ok(File.Exists(p.VanillaCopy) && Hash.Sha256File(p.VanillaCopy) == m.SupportedGameBuilds[0].Sha256, "a clean copy of the vanilla data.win is kept (base) for repairs and updates");
            Ok(new InstallEngine(p).VerifyInstall(true) == null, "the installation verifies");
            Ok(pct.Count > 5 && pct.Last() == 100, "progress is reported to the end");
            Ok(!Directory.Exists(p.StagingDir) || Directory.GetDirectories(p.StagingDir).Length == 0, "no staging leftovers");
            Ok(!File.Exists(p.LockFile), "no transaction left open");
            JsonObject st = new InstallEngine(p).ReadState();
            Ok(st.Str("version") == m.Version && st.Str("game_source") == steamGame, "drbr-install.json records the version and the source");
            // the launcher's PLAY preparation (all of it except starting the Windows game)
            LauncherCore c = new LauncherCore(p);
            Ok(c.Engine.VerifyInstall(false) == null && SaveProfile.EnsureBundle(p, m.SaveProfile, c.Settings.StartMode).Count == 0, "PLAY's checks pass on a fresh install (nothing to repair)");
            // reinstall over it: same result, settings kept
            Settings s = Settings.Load(p); s.StartMode = SaveProfile.ModeContinue; s.Save(p);
            InstallResult r2 = new InstallEngine(p).Install(new InstallOptions { GameDir = steamGame, PayloadDir = PayloadDir, Shortcuts = false, RegisterUninstall = false, Operation = "reinstall" });
            Ok(r2.Ok && new InstallEngine(p).VerifyInstall(true) == null && File.ReadAllText(p.BundleProfileCfg).Contains("start_mode=continue"), "reinstall: verifies again, the start mode setting is kept");
            Ok(Directory.GetDirectories(p.BackupDir).Length == 0, "  ... the replaced copy is removed after the new one verified");
            installed = p;
            // from the old in-place Knight Hub's backup
            DrbrPaths p2 = NewPaths("drbr-from-kh");
            string kh = FakeGame("steam-game-kh", true);
            Dictionary<string, string> khBefore = Snapshot(kh);
            InstallResult r3 = new InstallEngine(p2).Install(new InstallOptions { GameDir = kh, PayloadDir = PayloadDir, Shortcuts = false, RegisterUninstall = false });
            Ok(r3.Ok && Hash.Sha256File(p2.DataWin) == m.DrbrDataWinSha256 && SameSnap(khBefore, Snapshot(kh), out diff), "installs from a game with the old Knight Hub in place (its clean backup); that game is not changed " + diff);
            Fs.DeleteDir(p2.Root);
        }

        static void RepairTests()
        {
            DrbrPaths p = installed ?? NewPaths("x");
            Manifest m = Payload();
            using (FileStream fs = new FileStream(p.DataWin, FileMode.Open, FileAccess.ReadWrite)) { fs.Seek(1000, SeekOrigin.Begin); fs.WriteByte(0x5A); }
            File.Delete(p.BundleTemplate);
            File.Delete(Path.Combine(p.Chapter3, "kf_steam.dll"));
            string bad = new InstallEngine(p).VerifyInstall(true);
            Ok(bad != null, "a damaged installation is noticed: " + bad);
            Ok(Throws(() => new LauncherCore(p).Play(null, 0)) != null, "PLAY refuses a damaged installation (it asks for a repair)");
            List<string> notes = new LauncherCore(p).Repair(null);
            Ok(new InstallEngine(p).VerifyInstall(true) == null && Hash.Sha256File(p.DataWin) == m.DrbrDataWinSha256 && Hash.Sha256File(p.BundleTemplate) == m.SaveProfile.TemplateSha256,
               "REPAIR rebuilds data.win, the starting save and the missing file; it verifies");
            // only the starting save missing: PLAY's own check puts it back without a repair
            File.Delete(p.BundleTemplate);
            List<string> did = SaveProfile.EnsureBundle(p, m.SaveProfile, "template");
            Ok(did.Any(x => x.Contains("restored")) && Hash.Sha256File(p.BundleTemplate) == m.SaveProfile.TemplateSha256, "a missing starting save is restored from DRBR's own copy");
            File.WriteAllText(p.BundleTemplate, "garbage");
            did = SaveProfile.EnsureBundle(p, m.SaveProfile, "template");
            Ok(did.Any(x => x.Contains("replaced")) && Hash.Sha256File(p.BundleTemplate) == m.SaveProfile.TemplateSha256, "a damaged starting save is replaced");
        }

        static void FailureTests()
        {
            DrbrPaths p = installed;
            Manifest m = Payload();
            string verBefore = new InstallEngine(p).InstalledVersion();
            foreach (string stage in new[] { "copy", "patch", "music", "profile", "commit", "verify" })
            {
                Environment.SetEnvironmentVariable("DRBR_TEST_FAIL_AT", stage);
                string err = Throws(() => new InstallEngine(p).Install(new InstallOptions { GameDir = steamGame, PayloadDir = PayloadDir, Shortcuts = false, RegisterUninstall = false, Operation = "update" }));
                Environment.SetEnvironmentVariable("DRBR_TEST_FAIL_AT", null);
                Ok(err != null && new InstallEngine(p).VerifyInstall(true) == null && new InstallEngine(p).InstalledVersion() == verBefore && !File.Exists(p.LockFile) &&
                   (!Directory.Exists(p.StagingDir) || Directory.GetDirectories(p.StagingDir).Length == 0),
                   "an update failing at '" + stage + "' is rolled back: the previous DRBR still verifies, no leftovers");
            }
            // a failed FIRST install leaves nothing half-installed
            DrbrPaths q = NewPaths("drbr-failed-first");
            Environment.SetEnvironmentVariable("DRBR_TEST_FAIL_AT", "verify");
            string e2 = Throws(() => new InstallEngine(q).Install(new InstallOptions { GameDir = steamGame, PayloadDir = PayloadDir, Shortcuts = false, RegisterUninstall = false }));
            Environment.SetEnvironmentVariable("DRBR_TEST_FAIL_AT", null);
            Ok(e2 != null && !Directory.Exists(q.GameDir) && !File.Exists(q.StateFile), "a first install that fails leaves no half-installed DRBR");
            // a damaged package is refused before anything changes
            string bad = Path.Combine(Work, "payload-bad");
            if (Directory.Exists(bad)) Fs.DeleteDir(bad);
            Directory.CreateDirectory(bad);
            foreach (string f in Directory.GetFiles(PayloadDir)) Link(f, Path.Combine(bad, Path.GetFileName(f)));
            File.Delete(Path.Combine(bad, "steam_appid.txt"));
            File.WriteAllText(Path.Combine(bad, "steam_appid.txt"), "999");
            string e3 = Throws(() => new InstallEngine(p).Install(new InstallOptions { GameDir = steamGame, PayloadDir = bad, Shortcuts = false, RegisterUninstall = false, Operation = "update" }));
            Ok(e3 != null && e3.Contains("payload_damaged") && new InstallEngine(p).VerifyInstall(true) == null, "a damaged package is refused before anything changes (" + e3 + ")");
        }

        static void InterruptTests()
        {
            DrbrPaths p = installed;
            // a crash between "old copy aside" and "new copy in": the lock file and the backup are there, the game folder is not
            string backup = Path.Combine(p.BackupDir, "game-crash");
            Directory.CreateDirectory(p.BackupDir);
            Directory.Move(p.GameDir, backup);
            JsonObject l = new JsonObject(); l["op"] = "update"; l["phase"] = "commit"; l["staging"] = Path.Combine(p.StagingDir, "update-crash"); l["backup"] = backup;
            File.WriteAllText(p.LockFile, Json.Write(l));
            Ok(new InstallEngine(p).VerifyInstall(false) != null, "after the crash the installation is incomplete");
            string msg = new InstallEngine(p).RecoverInterrupted();
            Ok(msg != null && msg.Contains("undone") && new InstallEngine(p).VerifyInstall(true) == null && !File.Exists(p.LockFile), "the next start puts the previous DRBR back (" + msg + ")");
        }

        /// <summary>The room the game could not join (newer DRBR): the note the game writes (GameMaker's ini_write_*: quoted
        /// values) is read by the launcher, which then offers the update; a note older than an hour is dropped.</summary>
        static void JoinTests()
        {
            DrbrPaths p = NewPaths("join");
            LauncherCore c = new LauncherCore(p);
            Ok(c.PendingJoin().Count == 0, "no note: nothing pending");
            Directory.CreateDirectory(p.LiveProfile);
            File.WriteAllText(p.PendingJoin, "[join]\r\nlobby=\"109775241234567890\"\r\ntheir_build=\"52.000000\"\r\nmy_build=\"51.000000\"\r\nhost=\"Tester\"\r\nstamp=\"46312.500000\"\r\nwhen=\"10/17/2026 12:00:00\"\r\n");
            Dictionary<string, string> d = c.PendingJoin();
            string lobby, theirs, host;
            d.TryGetValue("lobby", out lobby); d.TryGetValue("their_build", out theirs); d.TryGetValue("host", out host);
            Ok(lobby == "109775241234567890" && theirs == "52.000000" && host == "Tester", "the game's note is read: lobby " + lobby + ", their build " + theirs + ", host " + host);
            Ok(File.Exists(p.PendingJoin), "  ... and kept for the updated game, which offers the room and uses the note up");
            File.SetLastWriteTime(p.PendingJoin, DateTime.Now.AddMinutes(-61));
            Ok(c.PendingJoin().Count == 0 && !File.Exists(p.PendingJoin), "a note older than an hour is dropped (the game does not offer it either)");
            File.WriteAllText(p.PendingJoin, "not an ini at all\r\n");
            Ok(c.PendingJoin().Count == 0, "a damaged note means nothing pending (no crash)");
        }

        static void UpdateTests()
        {
            string url = Env("DRBR_TEST_HTTP", null);
            if (url == null) { Ok(false, "DRBR_TEST_HTTP is not set (the update tests need a local release server)"); return; }
            string rel = Env("DRBR_TEST_RELEASES", "");
            string logf = Env("DRBR_TEST_HTTP_LOG", "");
            DrbrPaths p = installed;
            LauncherCore c = new LauncherCore(p);
            // DRBR 1.0.0's layout (update-manifest.json and its .sig on their own) is still understood
            c.Settings.UpdateUrlOverride = url + "/json/update-manifest.json";
            c.Settings.Save(p);
            UpdateInfo uj = new LauncherCore(p).Check();
            Ok(uj.Available && uj.PackageUrl == null && uj.Manifest.Version == TestVer(1), "a release in the old layout (update-manifest.json) is still read: " + uj.Manifest.Version);
            // the release is one file, DRBR.zip
            c.Settings.UpdateUrlOverride = url + "/good/DRBR.zip";
            c.Settings.Save(p);
            c = new LauncherCore(p);
            File.WriteAllText(logf, "");
            UpdateInfo u = c.Check();
            Ok(u.Available && Ver.IsNewer(u.Manifest.Version, u.Installed) && u.PackageUrl == url + "/good/DRBR.zip", "the newer release is found in DRBR.zip: " + u.Installed + " -> " + u.Manifest.Version);
            string[] checkLog = File.ReadAllLines(logf);
            long zipLen = new FileInfo(Path.Combine(rel, "good", "DRBR.zip")).Length;
            Ok(checkLog.Length > 0 && checkLog.All(l => l.StartsWith("RANGE good/DRBR.zip")) && checkLog.Sum(l => RangeLen(l)) < 200000,
               "the check read only the end of DRBR.zip (" + checkLog.Length + " requests, " + checkLog.Sum(l => RangeLen(l)) + " of " + zipLen + " bytes)");
            // where the files are inside it (read here from the file itself)
            Dictionary<string, PackagedFile> at;
            using (FileSource fs = new FileSource(Path.Combine(rel, "good", "DRBR.zip")))
                at = DrbrPackage.Open(fs).PayloadFiles(u.Manifest.Files.Select(f => f.File));
            // an interrupted download resumes: a .part file with the first bytes is there
            PayloadFile changed = u.Manifest.Files.First(f => f.Kind == "doc");
            string dl = Path.Combine(p.StagingDir, "download-" + u.Manifest.Version);
            Directory.CreateDirectory(dl);
            byte[] full;
            using (FileStream z = File.OpenRead(Path.Combine(rel, "good", "DRBR.zip")))
            {
                full = new byte[changed.Size];
                z.Seek(at[changed.File].Offset, SeekOrigin.Begin);
                z.Read(full, 0, full.Length);
            }
            Ok(Hash.Same(Hash.Sha256Bytes(full), changed.Sha256), "the changed file is where the package says (" + changed.File + " at " + at[changed.File].Offset + ")");
            File.WriteAllBytes(Path.Combine(dl, changed.File + ".part"), full.Take(full.Length / 2).ToArray());
            File.WriteAllText(logf, "");
            InstallResult r = c.ApplyUpdate(u, null);
            Ok(r.Ok && new InstallEngine(p).InstalledVersion() == u.Manifest.Version && new InstallEngine(p).VerifyInstall(true) == null, "the update is downloaded, installed and verifies (" + r.Version + ")");
            string[] dlLog = File.ReadAllLines(logf);
            long resumeAt = at[changed.File].Offset + full.Length / 2;
            Ok(dlLog.Any(l => l == "RANGE good/DRBR.zip " + resumeAt + "-" + (at[changed.File].Offset + full.Length - 1)), "the interrupted download was resumed (only the rest of " + changed.File + " was asked for)");
            Ok(!dlLog.Any(l => l.StartsWith("GET ")), "DRBR.zip was never downloaded whole");
            // (the zips' directories are read from their ends: up to 64 KB of whatever file lies just before them)
            string touched = "";
            foreach (PayloadFile f in u.Manifest.Files)
            {
                if (f.Kind == "doc") continue;
                long a0 = at[f.File].Offset, a1 = a0 + f.Size - 1, over = 0;
                foreach (string l in dlLog)
                {
                    long s0, s1;
                    if (RangeOf(l, out s0, out s1) && s0 <= a1 && s1 >= a0) over += Math.Min(a1, s1) - Math.Max(a0, s0) + 1;
                }
                if (over > 70000) touched += f.File + " (" + over + " bytes) ";
            }
            long docs = u.Manifest.Files.Where(f => f.Kind == "doc").Sum(f => f.Size);
            Ok(touched == "" && dlLog.Sum(l => RangeLen(l)) < docs + 300000, "unchanged files were not downloaded again (the game patch, the music): " + dlLog.Sum(l => RangeLen(l)) + " bytes read in all, " + docs + " of them the changed files " + touched);
            Ok(Hash.Sha256File(p.BundleTemplate) == u.Manifest.SaveProfile.TemplateSha256 && File.ReadAllText(p.BundleProfileCfg).Contains("start_mode=continue"), "after the update: the same starting save, the player's start mode kept");
            Ok(new LauncherCore(p).Check().Available == false, "after the update: up to date");
            // a DRBR.zip compressed again by hand: downloaded whole and unpacked here, still checked
            c.Settings.UpdateUrlOverride = url + "/rezip/DRBR.zip"; c.Settings.Save(p);
            File.WriteAllText(logf, "");
            LauncherCore c2 = new LauncherCore(p);
            UpdateInfo u2 = c2.Check();
            InstallResult r2 = c2.ApplyUpdate(u2, null);
            Ok(u2.Manifest.Version == TestVer(2) && r2.Ok && new InstallEngine(p).InstalledVersion() == TestVer(2) && new InstallEngine(p).VerifyInstall(true) == null && File.ReadAllText(logf).Contains("GET rezip/DRBR.zip"),
               "a DRBR.zip compressed again by hand still updates (downloaded whole): " + u2.Manifest.Version);
            // a server without HTTP ranges: the same, check and update
            c.Settings.UpdateUrlOverride = url + "/norange/DRBR.zip"; c.Settings.Save(p);
            LauncherCore c4 = new LauncherCore(p);
            UpdateInfo u4 = c4.Check();
            InstallResult r4 = c4.ApplyUpdate(u4, null);
            Ok(u4.Manifest.Version == TestVer(3) && r4.Ok && new InstallEngine(p).InstalledVersion() == TestVer(3) && new InstallEngine(p).VerifyInstall(true) == null, "a server without HTTP ranges: the check and the update still work (" + u4.Manifest.Version + ")");
            string[] left = Directory.Exists(p.StagingDir) ? Directory.GetFiles(p.StagingDir, "*", SearchOption.AllDirectories).Where(x => x.Contains(".whole") || Path.GetFileName(x).StartsWith("check-") || x.EndsWith(".unpacked")).ToArray() : new string[0];
            Ok(left.Length == 0, "no whole download or unpacked copy left behind (" + string.Join(", ", left.Select(Path.GetFileName)) + ")");
            // a release whose manifest is not signed by DRBR's key
            c.Settings.UpdateUrlOverride = url + "/badsig/DRBR.zip"; c.Settings.Save(p);
            string e1 = Throws(() => new LauncherCore(p).Check());
            Ok(e1 != null && e1.StartsWith("bad_signature"), "an unauthorized release (bad signature) is refused: " + e1);
            // a release whose file is damaged on the server
            c.Settings.UpdateUrlOverride = url + "/corrupt/DRBR.zip"; c.Settings.Save(p);
            LauncherCore c3 = new LauncherCore(p);
            UpdateInfo u3 = c3.Check();
            string ver = new InstallEngine(p).InstalledVersion();
            string e2 = Throws(() => c3.ApplyUpdate(u3, null));
            Ok(e2 != null && e2.StartsWith("bad_download") && new InstallEngine(p).InstalledVersion() == ver && new InstallEngine(p).VerifyInstall(true) == null, "a damaged download is refused; nothing changes: " + e2);
            // a release with a new launcher while the launcher runs: Windows does not let a running program be deleted ("access
            // denied") or overwritten, so its new copy waits in staging\pending for DRBR Updater - the update itself goes through
            c.Settings.UpdateUrlOverride = url + "/inuse/DRBR.zip"; c.Settings.Save(p);
            LauncherCore c5 = new LauncherCore(p);
            UpdateInfo u5 = c5.Check();
            PayloadFile nl = u5.Manifest.Files.First(f => f.Kind == "app" && f.Dest == "DRBR Launcher.exe");
            string oldLauncher = Hash.Sha256File(p.LauncherExe);
            InstallResult r5;
            Environment.SetEnvironmentVariable("DRBR_TEST_LAUNCHER_IN_USE", "1");
            try { r5 = c5.ApplyUpdate(u5, null); }
            finally { Environment.SetEnvironmentVariable("DRBR_TEST_LAUNCHER_IN_USE", null); }
            Ok(r5.Ok && new InstallEngine(p).InstalledVersion() == TestVer(5) && new InstallEngine(p).VerifyInstall(true) == null,
               "a release with a new launcher installs while the launcher runs (" + r5.Version + ")");
            Ok(r5.LauncherPending && r5.PendingLauncher == p.PendingLauncher && Hash.Same(Hash.Sha256File(p.PendingLauncher), nl.Sha256) && Hash.Same(r5.PendingLauncherSha, nl.Sha256),
               "  ... the new launcher waits in staging\\pending, checked (" + string.Join(" ", r5.Notes.ToArray()) + ")");
            Ok(Hash.Same(Hash.Sha256File(p.LauncherExe), oldLauncher) && !File.Exists(p.LauncherExe + ".part"), "  ... the running launcher was left alone, no half-copied file next to it");
            Ok(Hash.Same(LauncherSwap.Waiting(p), nl.Sha256), "  ... the next launcher start finds it to swap in");
            File.Copy(p.PendingLauncher, p.LauncherExe, true);   // (what DRBR Updater does, tested on Windows programs under Wine)
            Ok(LauncherSwap.Waiting(p) == null && !File.Exists(p.PendingLauncher), "  ... once it is in place, the staged copy is removed and nothing is swapped again");
            // no release there (yet): a clear message
            c.Settings.UpdateUrlOverride = url + "/nothing/DRBR.zip"; c.Settings.Save(p);
            string e4 = Throws(() => new LauncherCore(p).Check());
            Ok(e4 != null && e4.StartsWith("no_release"), "no release at the address: a clear message (" + e4 + ")");
            // the server is down: a clear message, the installed DRBR stays playable
            c.Settings.UpdateUrlOverride = "http://127.0.0.1:9/DRBR.zip"; c.Settings.Save(p);
            string e3 = Throws(() => new LauncherCore(p).Check());
            Ok(e3 != null && e3.StartsWith("offline") && new InstallEngine(p).VerifyInstall(false) == null, "no connection: a clear message, DRBR still playable");
            c.Settings.UpdateUrlOverride = ""; c.Settings.Save(p);
        }

        // "RANGE <path> <first>-<last>" -> its bytes
        static bool RangeOf(string l, out long a, out long b)
        {
            a = b = -1;
            if (!l.StartsWith("RANGE ")) return false;
            string[] w = l.Split(' ');
            string[] ab = w[w.Length - 1].Split('-');
            return ab.Length == 2 && long.TryParse(ab[0], out a) && long.TryParse(ab[1], out b);
        }

        static long RangeLen(string l)
        {
            long a, b;
            return RangeOf(l, out a, out b) ? b - a + 1 : 0;
        }

        /// <summary>The published release, as a player's launcher reads it: the check (the end of DRBR.zip, the signature), then
        /// where every file is inside it and a few of them read and checked by their bytes (DRBR_TEST_LIVE_FILES: how many; the
        /// smallest first).</summary>
        static void LiveTests()
        {
            string url = Env("DRBR_TEST_LIVE_URL", "https://github.com/ionizachip/DRBR/releases/latest/download/DRBR.zip");
            DrbrPaths p = new DrbrPaths(Path.Combine(Work, "live"));
            Directory.CreateDirectory(p.StagingDir);
            UpdateEngine ue = new UpdateEngine(p, url);
            UpdateInfo u = ue.Check("0.0.1", 0);
            Ok(u.Manifest != null, "the release's manifest is read from " + url + " and its signature is DRBR's: version " + u.Manifest.Version + ", " + u.Manifest.Files.Count + " files, package " + u.PackageUrl);
            HttpRangeSource src = new HttpRangeSource(u.PackageUrl ?? url);
            Console.WriteLine("  " + (u.PackageUrl ?? url) + " -> " + src.FinalUrl.Split('?')[0] + " (" + src.Length + " bytes, ranges " + src.Ranges + ")");
            DrbrPackage pkg = DrbrPackage.Open(src);
            Ok(Hash.Same(Hash.Sha256Bytes(pkg.ManifestBytes()), Hash.Sha256Bytes(u.ManifestBytes)), "the versioned DRBR.zip has the same manifest as the latest one");
            Dictionary<string, PackagedFile> at = pkg.PayloadFiles(u.Manifest.Files.Select(f => f.File));
            Ok(at != null, "every file can be read in place (DRBR-Setup.exe and its package are stored): " + (at == null ? "NO - the zip was compressed again" : at.Count + " files"));
            if (at == null) return;
            int n = int.Parse(Env("DRBR_TEST_LIVE_FILES", "4"));
            foreach (PayloadFile f in u.Manifest.Files.OrderBy(f => f.Size).Take(n))
            {
                string dst = Path.Combine(p.StagingDir, f.File);
                Http.DownloadRange(src, at[f.File].Offset, dst, f.Size, f.Sha256, null);
                Ok(Hash.Same(Hash.Sha256File(dst), f.Sha256), "  " + f.File + " (" + f.Size + " bytes at " + at[f.File].Offset + ") read from the release and checked");
                File.Delete(dst);
            }
            Console.WriteLine("  " + src.Requests + " requests");
        }

        static void UninstallTests()
        {
            DrbrPaths p = installed;
            Dictionary<string, string> steamBefore = Snapshot(steamGame);
            SortedDictionary<string, string> savesBefore = SaveProfile.VanillaSnapshot(p.SaveArea);
            Directory.CreateDirectory(p.LiveProfile);
            File.WriteAllText(Path.Combine(p.LiveProfile, "filech3_0"), "drbr save");
            new InstallEngine(p).Uninstall(false);
            Ok(!Directory.Exists(p.GameDir) && !File.Exists(p.StateFile) && !Directory.Exists(p.PayloadDir) && !Directory.Exists(p.BaseDir) && !File.Exists(p.LauncherExe), "uninstall removes DRBR's folder contents");
            string diff;
            Ok(SameSnap(steamBefore, Snapshot(steamGame), out diff), "uninstall leaves the player's DELTARUNE folder unchanged " + diff);
            Ok(SaveProfile.CompareSnapshots(savesBefore, SaveProfile.VanillaSnapshot(p.SaveArea)).Count == 0 && File.Exists(Path.Combine(p.SaveArea, "knightfights_online.ini")), "uninstall leaves the player's saves and the online settings");
            Ok(File.Exists(Path.Combine(p.LiveProfile, "filech3_0")), "the DRBR saves stay unless asked");
            new InstallEngine(p).Uninstall(true);
            Ok(!Directory.Exists(p.LiveProfile), "uninstall with 'remove saves' removes the DRBR saves (only those)");
        }
    }
}
