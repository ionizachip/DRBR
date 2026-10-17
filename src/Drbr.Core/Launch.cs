// DRBR - what the launcher does (its window and its command line both call this): PLAY, check / apply updates, repair.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Threading;

namespace Drbr
{
    public sealed class PlayResult
    {
        public bool Started;
        public string StartResult = "";    // ok | wrong_room | error | timeout | not_waited
        public string Room = "";
        public string Error = "";
        public readonly List<string> Notes = new List<string>();
        public Process Game;
    }

    public sealed class LauncherCore
    {
        public readonly DrbrPaths P;
        public readonly InstallEngine Engine;
        public Settings Settings;

        public LauncherCore(DrbrPaths p)
        {
            P = p;
            Engine = new InstallEngine(p);
            Settings = Settings.Load(p);
        }

        public Manifest InstalledManifest()
        {
            string f = Path.Combine(P.PayloadDir, "payload.json");
            return File.Exists(f) ? Manifest.Load(f) : null;
        }

        int InstalledProtocol()
        {
            JsonObject s = Engine.ReadState();
            return s != null ? (int)s.Long("protocol", 0) : 0;
        }

        public UpdateInfo Check()
        {
            UpdateEngine u = new UpdateEngine(P, UpdateEngine.DefaultUrl(Settings));
            return u.Check(Engine.InstalledVersion(), InstalledProtocol());
        }

        /// <summary>Downloads (only what changed) and installs a release - the same transaction as an install, rolled back on failure.</summary>
        public InstallResult ApplyUpdate(UpdateInfo info, Action<string, int> progress)
        {
            if (info.LauncherTooOld)
                Log.Warn("This launcher (" + BuildInfo.Version + ") is older than the release needs (" + info.Manifest.MinLauncherVersion + "); the update brings the new launcher.");
            string running;
            if (Proc.DrbrGameRunning(P, out running)) throw new DrbrException("game_running", "DRBR is running (" + running + "). Close the game, then update.");
            UpdateEngine ue = new UpdateEngine(P, UpdateEngine.DefaultUrl(Settings));
            string dir = ue.Download(info, (t, pct) => { if (progress != null) progress(t, pct / 2); });
            InstallResult r = Engine.Install(new InstallOptions
            {
                GameDir = Settings.GameSource,
                PayloadDir = dir,
                Operation = "update",
                Shortcuts = false,
                Progress = (t, pct) => { if (progress != null) progress(t, 50 + pct / 2); }
            });
            try { Fs.DeleteDir(dir); } catch { }
            return r;
        }

        /// <summary>REPAIR: the whole install again from the package DRBR keeps (and the game's files), then the starting save.</summary>
        public List<string> Repair(Action<string, int> progress)
        {
            List<string> notes = new List<string>();
            string rec = Engine.RecoverInterrupted();
            if (rec != null) notes.Add(rec);
            if (!File.Exists(Path.Combine(P.PayloadDir, "payload.json")))
                throw new DrbrException("no_package", "DRBR's package is missing, so it cannot repair itself. Run DRBR-Setup.exe again (your DRBR settings and saves are kept).");
            InstallResult r = Engine.Install(new InstallOptions { GameDir = Settings.GameSource, PayloadDir = P.PayloadDir, Operation = "repair", Shortcuts = true, Progress = progress });
            notes.AddRange(r.Notes);
            Manifest m = InstalledManifest();
            notes.AddRange(SaveProfile.EnsureBundle(P, m.SaveProfile, Settings.StartMode));
            notes.Add("DRBR " + r.Version + " repaired and verified.");
            return notes;
        }

        SortedDictionary<string, string> before;

        /// <summary>PLAY: check the install, make sure the starting save and the profile are right, start the game, and (if
        /// waitSeconds > 0) wait for the game to report that it reached the starting room.</summary>
        public PlayResult Play(Action<string> status, int waitSeconds)
        {
            PlayResult pr = new PlayResult();
            Action<string> say = t => { Log.Info(t); if (status != null) status(t); };
            string rec = Engine.RecoverInterrupted();
            if (rec != null) pr.Notes.Add(rec);
            string running;
            if (Proc.DrbrGameRunning(P, out running)) throw new DrbrException("game_running", "DRBR is already running.");
            say("Checking the installation...");
            string bad = Engine.VerifyInstall(false);
            if (bad != null) throw new DrbrException("needs_repair", "DRBR needs a repair: " + bad + ".");
            Manifest m = InstalledManifest();
            if (m == null) throw new DrbrException("needs_repair", "DRBR needs a repair: its package record is missing.");
            say("Checking the DRBR starting save...");
            pr.Notes.AddRange(SaveProfile.EnsureBundle(P, m.SaveProfile, Settings.StartMode));
            pr.Notes.AddRange(SaveProfile.Migrate(P, m.SaveProfile));
            before = SaveProfile.VanillaSnapshot(P.SaveArea);
            DateTime t0 = DateTime.Now.AddSeconds(-2);
            string lastBefore = File.Exists(P.LastStart) ? File.ReadAllText(P.LastStart) : null;
            say("Starting DRBR...");
            pr.Game = Proc.StartGame(P);
            pr.Started = pr.Game != null;
            if (waitSeconds <= 0) { pr.StartResult = "not_waited"; return pr; }
            // the game writes drbr_profile\last_start.ini when it loads the starting save, and again in the first room
            DateTime end = DateTime.Now.AddSeconds(waitSeconds);
            while (DateTime.Now < end)
            {
                Thread.Sleep(500);
                if (File.Exists(P.LastStart) && File.GetLastWriteTime(P.LastStart) >= t0)
                {
                    Dictionary<string, string> ls = SaveProfile.ReadLastStart(P);
                    string res;
                    ls.TryGetValue("result", out res);
                    if (res == "ok" || res == "wrong_room" || res == "error")
                    {
                        pr.StartResult = res;
                        string room;
                        if (ls.TryGetValue("room", out room)) pr.Room = room;
                        string err;
                        if (ls.TryGetValue("error", out err)) pr.Error = err;
                        say(res == "ok" ? "DRBR started in " + (pr.Room.Length > 0 ? pr.Room : "the starting room") + " - the room before the Roaring Knight."
                            : res == "error" ? "DRBR could not start: " + pr.Error : "DRBR started, but not in the starting room (" + pr.Room + ").");
                        return pr;
                    }
                }
                try { if (pr.Game.HasExited) { pr.StartResult = "exited"; say("The game closed before it reached the starting room (exit code " + pr.Game.ExitCode + ")."); return pr; } } catch { }
            }
            pr.StartResult = "timeout";
            say("The game is running; it has not reported the starting room yet.");
            return pr;
        }

        /// <summary>After the game closed: were the player's own DELTARUNE saves left alone? (A list of changes, empty = yes.)</summary>
        public List<string> AfterGame()
        {
            if (before == null) return new List<string>();
            List<string> d = SaveProfile.CompareSnapshots(before, SaveProfile.VanillaSnapshot(P.SaveArea));
            if (d.Count == 0) Log.Info("After the game: your own DELTARUNE saves are unchanged.");
            else Log.Warn("After the game, these DELTARUNE save files changed: " + string.Join(", ", d.ToArray()) + " (DRBR writes only drbr_profile\\ - another program, Steam Cloud or vanilla DELTARUNE may have).");
            return d;
        }

        /// <summary>A room the game could not join because its players have a newer DRBR (written by the game).</summary>
        public Dictionary<string, string> PendingJoin()
        {
            Dictionary<string, string> d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            try
            {
                if (!File.Exists(P.PendingJoin)) return d;
                if ((DateTime.Now - File.GetLastWriteTime(P.PendingJoin)).TotalMinutes > 60) { File.Delete(P.PendingJoin); return d; }
                foreach (string raw in File.ReadAllLines(P.PendingJoin))
                {
                    int i = raw.IndexOf('=');
                    if (i > 0 && !raw.StartsWith("[")) d[raw.Substring(0, i).Trim()] = raw.Substring(i + 1).Trim().Trim('"');
                }
            }
            catch { }
            return d;
        }
    }
}
