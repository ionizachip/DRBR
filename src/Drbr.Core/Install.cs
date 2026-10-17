// DRBR - installing, repairing, updating (all one transaction) and uninstalling DRBR's own copy of the game.
// The player's Steam DELTARUNE is only ever READ: the vanilla Chapter 3 data.win (or the old Knight Hub's verified backup
// of it), DELTARUNE.exe, Chapter 3's sounds / language / videos and the music. Everything DRBR writes is under its own
// folder (%LOCALAPPDATA%\DRBR) - and, while the game runs, the game's DRBR saves in %LOCALAPPDATA%\DELTARUNE\drbr_profile.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Text;

namespace Drbr
{
    public sealed class Settings
    {
        public string StartMode = SaveProfile.ModeTemplate;
        public bool CheckUpdatesOnStart = true;
        public string UpdateUrlOverride = "";   // testing only (a local server); the signature key never changes
        public string GameSource = "";

        public static Settings Load(DrbrPaths p)
        {
            Settings s = new Settings();
            try
            {
                if (File.Exists(p.SettingsFile))
                {
                    JsonObject o = Json.ParseObject(File.ReadAllText(p.SettingsFile));
                    s.StartMode = o.Str("start_mode", s.StartMode) == SaveProfile.ModeContinue ? SaveProfile.ModeContinue : SaveProfile.ModeTemplate;
                    s.CheckUpdatesOnStart = o.Bool("check_updates_on_start", true);
                    s.UpdateUrlOverride = o.Str("update_url_override", "");
                    s.GameSource = o.Str("game_source", "");
                }
            }
            catch (Exception e) { Log.Warn("Settings unreadable, using defaults: " + e.Message); }
            return s;
        }

        public void Save(DrbrPaths p)
        {
            JsonObject o = new JsonObject();
            o["start_mode"] = StartMode;
            o["check_updates_on_start"] = CheckUpdatesOnStart;
            o["update_url_override"] = UpdateUrlOverride;
            o["game_source"] = GameSource;
            Fs.WriteAtomicText(p.SettingsFile, Json.Write(o));
        }
    }

    public sealed class InstallOptions
    {
        public string GameDir;
        public string PayloadDir;
        public string StartMode;           // null = keep the installed setting (default template)
        public bool Shortcuts = true;
        public bool RegisterUninstall = true;
        public string Operation = "install";   // install | repair | update
        public Action<string, int> Progress;
        public string FailAt = Environment.GetEnvironmentVariable("DRBR_TEST_FAIL_AT") ?? "";   // tests: copy | patch | music | profile | commit | verify
    }

    public sealed class InstallResult
    {
        public bool Ok;
        public string Version;
        public readonly List<string> Notes = new List<string>();
        public bool LauncherPending;     // a new launcher was staged; DRBR Updater swaps it once the launcher closes
        public string PendingLauncher;
    }

    public sealed class InstallEngine
    {
        public readonly DrbrPaths P;
        public InstallEngine(DrbrPaths p) { P = p; }

        void Step(InstallOptions o, string what, int pct)
        {
            Log.Info("[" + pct + "%] " + what);
            if (o.Progress != null) o.Progress(what, pct);
        }

        static void FailHook(InstallOptions o, string stage)
        {
            if (o.FailAt == stage) throw new DrbrException("test_fail", "Test failure injected at '" + stage + "' (DRBR_TEST_FAIL_AT).");
        }

        // ------------------------------------------------------------------------------------------------ payload
        /// <summary>The payload (payload.json + every file it lists), checked byte for byte. Throws on anything wrong.</summary>
        public static Manifest VerifyPayload(string dir, Action<string, int> progress = null)
        {
            string mf = Path.Combine(dir, "payload.json");
            if (!File.Exists(mf)) throw new DrbrException("payload_missing", "The DRBR package is incomplete (payload.json is missing).");
            Manifest m = Manifest.Load(mf);
            int i = 0;
            foreach (PayloadFile f in m.Files)
            {
                i++;
                if (f.Kind == "patch_incremental") continue;   // optional
                string path = Path.Combine(dir, f.File);
                if (progress != null) progress("Checking " + f.File, 2 + (i * 8 / Math.Max(1, m.Files.Count)));
                if (!File.Exists(path)) throw new DrbrException("payload_missing", "The DRBR package is incomplete: " + f.File + " is missing.");
                if (new FileInfo(path).Length != f.Size) throw new DrbrException("payload_damaged", "The DRBR package is damaged: " + f.File + " has the wrong size.");
                if (!Hash.Same(Hash.Sha256File(path), f.Sha256)) throw new DrbrException("payload_damaged", "The DRBR package is damaged: " + f.File + " failed its checksum.");
            }
            PayloadFile t = m.Template;
            if (t == null) throw new DrbrException("payload_template", "The DRBR package has no starting save.");
            string why = SaveProfile.ValidateTemplate(File.ReadAllBytes(Path.Combine(dir, t.File)), m.SaveProfile);
            if (why.Length > 0) throw new DrbrException("payload_template", "The DRBR package's starting save is not usable: " + why + ".");
            return m;
        }

        // ------------------------------------------------------------------------------------------------ state
        public JsonObject ReadState()
        {
            try { if (File.Exists(P.StateFile)) return Json.ParseObject(File.ReadAllText(P.StateFile)); } catch (Exception e) { Log.Warn("drbr-install.json unreadable: " + e.Message); }
            return null;
        }

        public string InstalledVersion()
        {
            JsonObject s = ReadState();
            return s != null ? s.Str("version", null) : null;
        }

        void WriteLock(string op, string phase, string staging, string backup)
        {
            JsonObject o = new JsonObject();
            o["op"] = op; o["phase"] = phase; o["staging"] = staging; o["backup"] = backup ?? "";
            o["time"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
            Directory.CreateDirectory(P.Root);
            Fs.WriteAtomicText(P.LockFile, Json.Write(o));
        }

        /// <summary>A transaction a crash / power cut / closed window interrupted: the previous DRBR is put back.</summary>
        public string RecoverInterrupted()
        {
            if (!File.Exists(P.LockFile)) return null;
            string msg;
            try
            {
                JsonObject l = Json.ParseObject(File.ReadAllText(P.LockFile));
                string phase = l.Str("phase", ""), backup = l.Str("backup", ""), staging = l.Str("staging", "");
                Log.Warn("An interrupted " + l.Str("op", "?") + " was found (phase " + phase + ").");
                if (!string.IsNullOrEmpty(backup) && Directory.Exists(backup))
                {
                    if (Directory.Exists(P.GameDir)) Fs.DeleteDir(P.GameDir);
                    Directory.Move(backup, P.GameDir);
                    msg = "An interrupted DRBR " + l.Str("op", "install") + " was undone: the previous DRBR was put back.";
                }
                else msg = "An interrupted DRBR " + l.Str("op", "install") + " was cleaned up.";
                if (!string.IsNullOrEmpty(staging) && Directory.Exists(staging)) Fs.DeleteDir(staging);
            }
            catch (Exception e) { msg = "An interrupted DRBR install was found and cleaned up (" + e.Message + ")."; }
            try { File.Delete(P.LockFile); } catch { }
            Log.Warn(msg);
            return msg;
        }

        // ------------------------------------------------------------------------------------------------ install
        public InstallResult Install(InstallOptions o)
        {
            InstallResult res = new InstallResult();
            Directory.CreateDirectory(P.Root);
            string rec = RecoverInterrupted();
            if (rec != null) res.Notes.Add(rec);
            Settings settings = Settings.Load(P);
            if (o.StartMode != null) settings.StartMode = o.StartMode == SaveProfile.ModeContinue ? SaveProfile.ModeContinue : SaveProfile.ModeTemplate;

            Step(o, "Checking the DRBR package", 1);
            Manifest m = VerifyPayload(o.PayloadDir, o.Progress);
            res.Version = m.Version;

            Step(o, "Checking DELTARUNE", 10);
            GameReport g = string.IsNullOrEmpty(o.GameDir) ? new GameReport { Summary = "No DELTARUNE folder was given." } : GameCheck.Inspect(o.GameDir, m.SupportedGameBuilds);
            // (other mods in the Steam folder matter when DRBR is first made from it, not on every update or repair)
            if (o.Operation == "install" || o.Operation == "reinstall") foreach (string n in g.Notes) res.Notes.Add(n);
            if (!g.Compatible)
            {
                // an update / repair can build from DRBR's own copy: its clean data.win (base\data.win.vanilla) and its copy of
                // the game's other files - so a DELTARUNE update in Steam never stops DRBR updating
                GameReport self = SelfSource(m);
                if (self == null) throw new DrbrException("game_" + g.State, g.Summary);
                Log.Info("Steam's DELTARUNE is not usable as the source (" + g.Summary + "); using DRBR's own copy.");
                res.Notes.Add("DRBR was built from its own copy of the game (Steam's DELTARUNE: " + g.Summary + ")");
                g = self;
                o.GameDir = P.GameDir;
            }
            string running;
            if (Proc.DrbrGameRunning(P, out running)) throw new DrbrException("game_running", "DRBR is running (" + running + "). Close the game first.");

            // space: the copy of the game, the patched data.win, the vanilla copy, the music, the package cache
            string srcMus = Directory.Exists(Path.Combine(o.GameDir, "mus")) ? Path.Combine(o.GameDir, "mus") : Path.Combine(o.GameDir, "chapter3_windows", "mus");
            long need = m.DrbrDataWinSize + Fs.DirSize(srcMus) + VanillaChapterSize(o.GameDir) + 64L * 1048576;
            if (!File.Exists(P.VanillaCopy)) need += g.DataWinSize;
            foreach (PayloadFile f in m.Files) need += f.Size * 2;
            long free = Fs.FreeBytes(P.Root);
            if (free >= 0 && free < need)
                throw new DrbrException("disk_space", "Not enough free disk space: DRBR needs about " + Fs.Mb(need) + " and the drive has " + Fs.Mb(free) + ".");

            string stamp = DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture);
            string staging = Path.Combine(P.StagingDir, o.Operation + "-" + stamp);
            string sg = Path.Combine(staging, "game");
            string backup = null;
            string oldState = File.Exists(P.StateFile) ? File.ReadAllText(P.StateFile) : null;
            string oldPayload = null;
            bool switched = false;
            WriteLock(o.Operation, "staging", staging, null);
            try
            {
                if (Directory.Exists(staging)) Fs.DeleteDir(staging);
                Directory.CreateDirectory(Path.Combine(sg, "chapter3_windows"));

                // 1. the player's own game files (read only)
                Step(o, "Copying DELTARUNE's files (your Steam copy is not changed)", 14);
                Fs.CopyVerified(Path.Combine(o.GameDir, "DELTARUNE.exe"), Path.Combine(sg, "DELTARUNE.exe"));
                if (File.Exists(Path.Combine(o.GameDir, "options.ini"))) Fs.CopyVerified(Path.Combine(o.GameDir, "options.ini"), Path.Combine(sg, "options.ini"));
                CopyVanillaChapter(o.GameDir, Path.Combine(sg, "chapter3_windows"));
                FailHook(o, "copy");
                Step(o, "Copying the music", 24);
                if (Directory.Exists(srcMus)) CopyTree(srcMus, Path.Combine(sg, "chapter3_windows", "mus"), f => f.EndsWith(".ogg", StringComparison.OrdinalIgnoreCase));

                // 2. the clean data.win DRBR is built from (kept for repairs and updates)
                Step(o, "Keeping a clean copy of Chapter 3's data.win", 38);
                string vanilla = P.VanillaCopy;
                bool stagedVanilla = false;
                if (!(File.Exists(vanilla) && new FileInfo(vanilla).Length == g.Build.Size && Hash.Same(Hash.Sha256File(vanilla), g.Build.Sha256)))
                {
                    vanilla = Path.Combine(staging, "base", "data.win.vanilla");
                    Fs.CopyVerified(g.VanillaSource, vanilla, g.Build.Sha256);
                    stagedVanilla = true;
                }

                // 3. DRBR's data.win
                Step(o, "Building DRBR's data.win (patching a copy)", 46);
                string dw = Path.Combine(sg, "chapter3_windows", "data.win");
                Xdelta.Apply(Xdelta.ToolPath(P, o.PayloadDir), vanilla, Path.Combine(o.PayloadDir, m.FullPatch.File), dw);
                FailHook(o, "patch");
                if (new FileInfo(dw).Length != m.DrbrDataWinSize || !Hash.Same(Hash.Sha256File(dw), m.DrbrDataWinSha256))
                    throw new DrbrException("patch_verify", "The patched data.win did not come out as expected (checksum mismatch). Nothing was changed.");

                // 4. the mod's files
                Step(o, "Adding DRBR's files", 62);
                foreach (PayloadFile f in m.OfKind("copy"))
                    Fs.CopyVerified(Path.Combine(o.PayloadDir, f.File), Fs.Under(staging, f.Dest), f.Sha256);
                Step(o, "Adding DRBR's music", 66);
                InstallMusic(m, o.PayloadDir, Path.Combine(sg, "chapter3_windows", "mus"), res);
                InstallKfSongs(m, o.PayloadDir, Path.Combine(sg, "chapter3_windows", "kfsongs"));
                FailHook(o, "music");

                // 5. the save profile: the provided starting save (immutable) + the profile config the game reads
                Step(o, "Setting up the DRBR starting save", 74);
                string bundle = Path.Combine(sg, "chapter3_windows", "drbr_data");
                Directory.CreateDirectory(bundle);
                byte[] tpl = File.ReadAllBytes(Path.Combine(o.PayloadDir, m.Template.File));
                string why = SaveProfile.ValidateTemplate(tpl, m.SaveProfile);
                if (why.Length > 0) throw new DrbrException("template", why);
                File.WriteAllBytes(Path.Combine(bundle, "start_filech3"), tpl);
                File.WriteAllText(Path.Combine(bundle, "drbr_profile.cfg"), SaveProfile.CfgText(m.SaveProfile, settings.StartMode), new UTF8Encoding(false));
                FailHook(o, "profile");

                // 6. the package itself (repairs and updates start from it)
                Step(o, "Keeping the DRBR package for repairs", 78);
                string stagedPayload = null;
                if (!SamePath(o.PayloadDir, P.PayloadDir))
                {
                    stagedPayload = Path.Combine(staging, "payload");
                    CopyTree(o.PayloadDir, stagedPayload, null);
                }

                // 7. the switch: the old copy aside, the new one in - one rename each, undone on any failure
                Step(o, "Switching to the new DRBR", 82);
                if (Directory.Exists(P.GameDir))
                {
                    backup = Path.Combine(P.BackupDir, "game-" + stamp);
                    Directory.CreateDirectory(P.BackupDir);
                    WriteLock(o.Operation, "commit", staging, backup);
                    Directory.Move(P.GameDir, backup);
                }
                else WriteLock(o.Operation, "commit", staging, null);
                FailHook(o, "commit");
                Directory.Move(sg, P.GameDir);
                switched = true;
                if (stagedVanilla)
                {
                    Directory.CreateDirectory(P.BaseDir);
                    if (File.Exists(P.VanillaCopy)) File.Delete(P.VanillaCopy);
                    File.Move(vanilla, P.VanillaCopy);
                }
                if (stagedPayload != null)
                {
                    oldPayload = P.PayloadDir + ".old";
                    if (Directory.Exists(oldPayload)) Fs.DeleteDir(oldPayload);
                    if (Directory.Exists(P.PayloadDir)) Directory.Move(P.PayloadDir, oldPayload);
                    else oldPayload = null;
                    Directory.Move(stagedPayload, P.PayloadDir);
                }
                // the programs (a running launcher cannot replace itself: its new copy waits for DRBR Updater)
                foreach (PayloadFile f in m.Files)
                {
                    if (f.Kind != "app" && f.Kind != "tool" && f.Kind != "doc") continue;
                    string dst = Fs.Under(P.Root, f.Dest);
                    if (File.Exists(dst) && Hash.Same(Hash.Sha256File(dst), f.Sha256)) continue;
                    try { Fs.CopyVerified(Path.Combine(P.PayloadDir, f.File), dst, f.Sha256); }
                    catch (IOException)
                    {
                        string pend = Path.Combine(P.StagingDir, "pending", Path.GetFileName(dst));
                        Fs.CopyVerified(Path.Combine(P.PayloadDir, f.File), pend, f.Sha256);
                        res.LauncherPending = true;
                        res.PendingLauncher = pend;
                        res.Notes.Add(Path.GetFileName(dst) + " is in use: its new version is installed when the launcher restarts.");
                    }
                }
                // the save profile's own records + the profile migrations
                Directory.CreateDirectory(P.SaveProfileDir);
                Fs.WriteAtomic(Path.Combine(P.SaveProfileDir, "start_filech3"), tpl);
                foreach (string d in SaveProfile.Migrate(P, m.SaveProfile)) res.Notes.Add(d);
                settings.GameSource = o.GameDir;
                settings.Save(P);
                WriteState(m, o.GameDir, g);

                // 8. everything where it should be?
                Step(o, "Verifying the installation", 90);
                FailHook(o, "verify");
                string bad = VerifyInstall(true);
                if (bad != null) throw new DrbrException("verify", "The installed files did not verify: " + bad);
            }
            catch (Exception e)
            {
                Log.Error(o.Operation + " failed: " + e.Message);
                RollBack(staging, backup, oldState, oldPayload, switched);
                if (e is DrbrException) throw;
                throw new DrbrException("install_failed", "DRBR could not be " + (o.Operation == "update" ? "updated" : "installed") + ": " + e.Message + " Your previous DRBR (if any) was kept.", e);
            }
            // done: the old copy, the old package and the staging go
            try { if (backup != null && Directory.Exists(backup)) Fs.DeleteDir(backup); } catch (Exception e) { Log.Warn("Old copy not removed: " + e.Message); }
            try { if (oldPayload != null && Directory.Exists(oldPayload)) Fs.DeleteDir(oldPayload); } catch { }
            try { if (Directory.Exists(staging)) Fs.DeleteDir(staging); } catch { }
            try { File.Delete(P.LockFile); } catch { }

            if (o.RegisterUninstall) Shell.RegisterUninstall(P, m.Version, Fs.DirSize(P.Root));
            if (o.Shortcuts) Shell.Shortcuts(P, true, true);
            if (Directory.Exists(Path.Combine(P.GameDir, "chapter3_windows", "mus")))
                Shell.Junction(Path.Combine(P.GameDir, "mus"), Path.Combine(P.GameDir, "chapter3_windows", "mus"));
            Step(o, "DRBR " + m.Version + " is installed", 100);
            res.Ok = true;
            return res;
        }

        /// <summary>DRBR's own copy as the source: its DELTARUNE.exe and Chapter 3 files, and base\data.win.vanilla.</summary>
        GameReport SelfSource(Manifest m)
        {
            if (!File.Exists(P.GameExe) || !File.Exists(P.VanillaCopy)) return null;
            long size = new FileInfo(P.VanillaCopy).Length;
            SupportedBuild b = null;
            foreach (SupportedBuild x in m.SupportedGameBuilds) if (x.Size == size) { b = x; break; }
            if (b == null || !Hash.Same(Hash.Sha256File(P.VanillaCopy), b.Sha256)) return null;
            GameReport r = new GameReport { GameDir = P.GameDir, Found = true, State = "drbr_copy", VanillaSource = P.VanillaCopy, Build = b, DataWinSize = size, DataWinSha256 = b.Sha256 };
            r.Summary = "DRBR's own copy of " + b.Name;
            return r;
        }

        void RollBack(string staging, string backup, string oldState, string oldPayload, bool switched)
        {
            try
            {
                if (backup != null && Directory.Exists(backup))
                {
                    if (Directory.Exists(P.GameDir)) Fs.DeleteDir(P.GameDir);
                    Directory.Move(backup, P.GameDir);
                    Log.Warn("Rolled back: the previous DRBR is back in place.");
                }
                else if (switched && Directory.Exists(P.GameDir))
                {
                    // a first install that failed after its switch: nothing half-installed is left behind
                    Fs.DeleteDir(P.GameDir);
                }
                if (oldPayload != null && Directory.Exists(oldPayload))
                {
                    if (Directory.Exists(P.PayloadDir)) Fs.DeleteDir(P.PayloadDir);
                    Directory.Move(oldPayload, P.PayloadDir);
                }
                if (oldState != null) Fs.WriteAtomicText(P.StateFile, oldState);
                else if (File.Exists(P.StateFile)) File.Delete(P.StateFile);
            }
            catch (Exception e) { Log.Error("Roll back failed: " + e.Message); }
            try { if (Directory.Exists(staging)) Fs.DeleteDir(staging); } catch { }
            try { File.Delete(P.LockFile); } catch { }
        }

        static bool SamePath(string a, string b)
        {
            try { return string.Equals(Path.GetFullPath(a).TrimEnd('\\', '/'), Path.GetFullPath(b).TrimEnd('\\', '/'), StringComparison.OrdinalIgnoreCase); }
            catch { return false; }
        }

        static long VanillaChapterSize(string gameDir)
        {
            long n = 0;
            string ch = Path.Combine(gameDir, "chapter3_windows");
            foreach (string f in EnumerateNoLinks(ch))
            {
                if (GameCheck.IsVanillaChapterFile(Fs.Rel(ch, f)) && !f.EndsWith("data.win", StringComparison.OrdinalIgnoreCase)) n += new FileInfo(f).Length;
            }
            return n;
        }

        /// <summary>Files under a folder, never following a junction / link (Steam's chapter3_windows\mus is one).</summary>
        static IEnumerable<string> EnumerateNoLinks(string dir)
        {
            if (!Directory.Exists(dir)) yield break;
            foreach (string f in Directory.GetFiles(dir)) yield return f;
            foreach (string d in Directory.GetDirectories(dir))
            {
                FileAttributes a;
                try { a = File.GetAttributes(d); } catch { continue; }
                if ((a & FileAttributes.ReparsePoint) != 0) continue;
                foreach (string f in EnumerateNoLinks(d)) yield return f;
            }
        }

        static void CopyVanillaChapter(string gameDir, string dst)
        {
            string ch = Path.Combine(gameDir, "chapter3_windows");
            int n = 0;
            foreach (string f in EnumerateNoLinks(ch))
            {
                string rel = Fs.Rel(ch, f);
                if (!GameCheck.IsVanillaChapterFile(rel)) continue;
                Fs.CopyVerified(f, Fs.Under(dst, rel));
                n++;
            }
            Log.Info("Copied " + n + " of Chapter 3's own files (sounds, language, videos, options).");
        }

        static void CopyTree(string src, string dst, Func<string, bool> filter)
        {
            int n = 0;
            foreach (string f in EnumerateNoLinks(src))
            {
                string rel = Fs.Rel(src, f);
                if (filter != null && !filter(rel)) continue;
                Fs.CopyVerified(f, Fs.Under(dst, rel));
                n++;
            }
            Log.Info("Copied " + n + " file(s) from " + src);
        }

        /// <summary>The mod's songs: each listed file from the music zips into mus\ (checked against its checksum).</summary>
        static void InstallMusic(Manifest m, string payload, string musDir, InstallResult res)
        {
            List<ZipArchive> zips = new List<ZipArchive>();
            try
            {
                foreach (PayloadFile z in m.OfKind("music_zip")) zips.Add(ZipFile.OpenRead(Path.Combine(payload, z.File)));
                int placed = 0, same = 0, missing = 0;
                foreach (MusicFile mu in m.Music)
                {
                    string dest = Fs.Under(musDir, mu.Rel);
                    if (File.Exists(dest) && (string.IsNullOrEmpty(mu.Sha256) || Hash.Same(Hash.Sha256File(dest), mu.Sha256))) { same++; continue; }
                    ZipArchiveEntry e = null;
                    foreach (ZipArchive za in zips)
                    {
                        e = Find(za, mu.Rel);
                        if (e != null) break;
                    }
                    if (e == null) { missing++; Log.Warn("Music not in the package: " + mu.Rel); continue; }
                    Directory.CreateDirectory(Path.GetDirectoryName(dest));
                    string tmp = dest + ".part";
                    using (Stream s = e.Open())
                    using (FileStream fs = new FileStream(tmp, FileMode.Create, FileAccess.Write)) s.CopyTo(fs, 1 << 20);
                    if (!string.IsNullOrEmpty(mu.Sha256) && !Hash.Same(Hash.Sha256File(tmp), mu.Sha256))
                    {
                        File.Delete(tmp);
                        throw new DrbrException("music_damaged", "A song in the DRBR package is damaged: " + mu.Rel);
                    }
                    if (File.Exists(dest)) File.Delete(dest);
                    File.Move(tmp, dest);
                    placed++;
                }
                Log.Info("Music: " + placed + " installed, " + same + " already there, " + missing + " missing.");
                if (missing > 0) res.Notes.Add(missing + " optional song(s) were not in the package (those fights use their own music).");
            }
            finally { foreach (ZipArchive z in zips) z.Dispose(); }
        }

        static ZipArchiveEntry Find(ZipArchive z, string rel)
        {
            string want = rel.Replace('\\', '/').TrimStart('/');
            foreach (ZipArchiveEntry e in z.Entries)
            {
                string n = e.FullName.Replace('\\', '/');
                if (string.Equals(n, want, StringComparison.OrdinalIgnoreCase) || string.Equals(n, "mus/" + want, StringComparison.OrdinalIgnoreCase)) return e;
            }
            return null;
        }

        /// <summary>The KF Song Pack (kfsongs\[song]\...) next to data.win.</summary>
        static void InstallKfSongs(Manifest m, string payload, string dst)
        {
            foreach (PayloadFile z in m.OfKind("kfsongs_zip"))
            {
                int n = 0;
                using (ZipArchive za = ZipFile.OpenRead(Path.Combine(payload, z.File)))
                {
                    foreach (ZipArchiveEntry e in za.Entries)
                    {
                        string name = e.FullName.Replace('\\', '/');
                        if (!name.StartsWith("kfsongs/", StringComparison.OrdinalIgnoreCase) || name.EndsWith("/")) continue;
                        string dest = Fs.Under(dst, name.Substring("kfsongs/".Length));
                        Directory.CreateDirectory(Path.GetDirectoryName(dest));
                        using (Stream s = e.Open())
                        using (FileStream fs = new FileStream(dest, FileMode.Create, FileAccess.Write)) s.CopyTo(fs, 1 << 20);
                        n++;
                    }
                }
                Log.Info("KF Song Pack: " + n + " file(s).");
            }
        }

        void WriteState(Manifest m, string gameDir, GameReport g)
        {
            JsonObject s = new JsonObject();
            s["schema"] = 1L;
            s["version"] = m.Version;
            s["mod_build"] = m.ModBuild;
            s["protocol"] = (long)m.Protocol;
            s["installed"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
            s["game_source"] = gameDir;
            s["game_build"] = g.Build != null ? g.Build.Name : "";
            s["vanilla_sha256"] = g.Build != null ? g.Build.Sha256 : "";
            JsonObject dw = new JsonObject();
            dw["size"] = m.DrbrDataWinSize;
            dw["sha256"] = m.DrbrDataWinSha256;
            dw["mtime_utc"] = File.GetLastWriteTimeUtc(P.DataWin).Ticks;
            s["data_win"] = dw;
            List<object> files = new List<object>();
            foreach (PayloadFile f in m.Files)
            {
                if (f.Kind != "copy") continue;
                JsonObject x = new JsonObject();
                x["path"] = f.Dest.Replace('\\', '/');
                x["size"] = f.Size;
                x["sha256"] = f.Sha256;
                files.Add(x);
            }
            JsonObject t = new JsonObject();
            t["path"] = "game/chapter3_windows/drbr_data/start_filech3";
            t["size"] = m.SaveProfile.TemplateSize;
            t["sha256"] = m.SaveProfile.TemplateSha256;
            files.Add(t);
            s["files"] = files;
            JsonObject sp = new JsonObject();
            sp["save_template_version"] = (long)m.SaveProfile.TemplateVersion;
            sp["migration_version"] = (long)m.SaveProfile.MigrationVersion;
            sp["starting_room_id"] = (long)m.SaveProfile.StartingRoomId;
            s["save_profile"] = sp;
            Fs.WriteAtomicText(P.StateFile, Json.Write(s));
        }

        /// <summary>null when the installed DRBR is complete; else the first thing wrong. full = hash data.win even if unchanged.</summary>
        public string VerifyInstall(bool full)
        {
            JsonObject s = ReadState();
            if (s == null) return "DRBR is not installed (drbr-install.json is missing)";
            if (!File.Exists(P.GameExe)) return "DELTARUNE.exe is missing from DRBR's copy of the game";
            if (!File.Exists(P.DataWin)) return "DRBR's data.win is missing";
            JsonObject dw = s.Obj("data_win");
            FileInfo fi = new FileInfo(P.DataWin);
            if (dw != null)
            {
                if (fi.Length != dw.Long("size")) return "DRBR's data.win has the wrong size";
                bool unchanged = fi.LastWriteTimeUtc.Ticks == dw.Long("mtime_utc");
                if ((full || !unchanged) && !Hash.Same(Hash.Sha256File(P.DataWin), dw.Str("sha256", ""))) return "DRBR's data.win is damaged (checksum mismatch)";
            }
            foreach (object x in s.Arr("files"))
            {
                JsonObject f = x as JsonObject;
                if (f == null) continue;
                string path;
                try { path = Fs.Under(P.Root, f.Str("path", "")); } catch { return "a bad path in drbr-install.json"; }
                if (!File.Exists(path)) return f.Str("path", "") + " is missing";
                if (new FileInfo(path).Length != f.Long("size")) return f.Str("path", "") + " has the wrong size";
                if (full && !Hash.Same(Hash.Sha256File(path), f.Str("sha256", ""))) return f.Str("path", "") + " is damaged";
            }
            if (!File.Exists(P.BundleProfileCfg)) return "the DRBR profile config is missing";
            return null;
        }

        // ------------------------------------------------------------------------------------------------ uninstall
        /// <summary>Removes DRBR's folder, shortcuts and Apps entry. The player's DELTARUNE and every save stay; the DRBR saves
        /// (drbr_profile) stay too unless removeProfile.</summary>
        public void Uninstall(bool removeProfile, string exceptRunningExe = null)
        {
            Log.Info("Uninstall: removing " + P.Root + (removeProfile ? " and the DRBR saves" : ""));
            Shell.RemoveShortcuts();
            Shell.UnregisterUninstall();
            if (removeProfile && Directory.Exists(P.LiveProfile)) Fs.DeleteDir(P.LiveProfile);
            foreach (string d in new[] { P.GameDir, P.BaseDir, P.PayloadDir, P.StagingDir, P.BackupDir, P.SaveProfileDir, Path.Combine(P.Root, "tools"), Path.Combine(P.Root, "docs") })
            {
                try { Fs.DeleteDir(d); } catch (Exception e) { Log.Warn("Could not remove " + d + ": " + e.Message); }
            }
            foreach (string f in new[] { P.StateFile, P.SettingsFile, P.LockFile, P.UpdaterExe })
            {
                try { if (File.Exists(f)) File.Delete(f); } catch { }
            }
            if (exceptRunningExe == null || !SamePath(exceptRunningExe, P.LauncherExe))
            {
                try { if (File.Exists(P.LauncherExe)) File.Delete(P.LauncherExe); } catch { }
            }
        }
    }
}
