// DRBR Launcher - PLAY, updates, repair, the starting save, settings. Also runs without a window for scripts and tests:
//   --play --check --update --repair --restore-save --verify --uninstall [--quiet] [--keep-saves|--remove-saves]
//   [--root <DRBR folder>] [--result <file.json>]
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace Drbr
{
    static class LauncherProgram
    {
        [STAThread]
        static int Main(string[] args)
        {
            Dictionary<string, string> a = Args(args);
            DrbrPaths p = new DrbrPaths(a.ContainsKey("root") ? a["root"] : RootFromExe());
            Log.Open(p.LogDir, "DRBR Launcher");
            string cli = null;
            foreach (string k in new[] { "play", "check", "update", "repair", "restore-save", "verify", "uninstall", "status" })
                if (a.ContainsKey(k)) { cli = k; break; }
            if (cli != null && (a.ContainsKey("quiet") || a.ContainsKey("result") || cli != "uninstall"))
                return Headless.Run(p, cli, a);
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            using (Mutex single = new Mutex(false, "DRBR-Launcher-" + p.Root.GetHashCode()))
            {
                bool mine = false;
                try { mine = single.WaitOne(0); } catch (AbandonedMutexException) { mine = true; }
                if (!mine)
                {
                    MessageBox.Show("DRBR Launcher is already open.", "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return 0;
                }
                // a new launcher that could not go in while this one ran (an update, or a reinstall with the launcher open):
                // DRBR Updater swaps it in now and starts it (once per start: not again right after a swap)
                if (!a.ContainsKey("updated") && !a.ContainsKey("update-failed"))
                {
                    string sha = LauncherSwap.Waiting(p);
                    if (sha != null && LauncherSwap.Start(p, sha, Process.GetCurrentProcess().Id, true)) return 0;
                }
                Application.Run(new LauncherForm(p, a));
            }
            return 0;
        }

        /// <summary>The launcher lives in the DRBR folder; started from anywhere else (a test, a copy) it uses the default.</summary>
        static string RootFromExe()
        {
            try
            {
                string dir = Path.GetDirectoryName(Process.GetCurrentProcess().MainModule.FileName);
                if (File.Exists(Path.Combine(dir, "drbr-install.json")) || Directory.Exists(Path.Combine(dir, "game"))) return dir;
            }
            catch { }
            return null;
        }

        public static Dictionary<string, string> Args(string[] args)
        {
            Dictionary<string, string> a = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < args.Length; i++)
            {
                string s = args[i];
                if (!s.StartsWith("--") && !s.StartsWith("/")) continue;
                string k = s.TrimStart('-', '/');
                string v = (i + 1 < args.Length && !args[i + 1].StartsWith("--")) ? args[++i] : "1";
                a[k] = v;
            }
            return a;
        }
    }

    /// <summary>The same actions as the window's buttons, without a window: exit code 0 = done; the result as JSON if asked.</summary>
    static class Headless
    {
        public static int Run(DrbrPaths p, string what, Dictionary<string, string> a)
        {
            JsonObject r = new JsonObject();
            r["action"] = what;
            int rc = 0;
            try
            {
                LauncherCore c = new LauncherCore(p);
                // an install / update a crash or a closed window interrupted is undone first (as the window does at its start)
                if (what != "status")
                {
                    string rec = c.Engine.RecoverInterrupted();
                    if (rec != null) r["recovered"] = rec;
                }
                switch (what)
                {
                    case "verify":
                        string bad = c.Engine.VerifyInstall(true);
                        r["ok"] = bad == null;
                        r["problem"] = bad ?? "";
                        rc = bad == null ? 0 : 10;
                        break;
                    case "repair":
                        r["notes"] = c.Repair(null);
                        r["ok"] = true;
                        break;
                    case "restore-save":
                        r["moved"] = (long)SaveProfile.RestoreStartingSave(p);
                        r["ok"] = true;
                        break;
                    case "check":
                        UpdateInfo u = c.Check();
                        r["installed"] = u.Installed ?? "";
                        r["available"] = u.Manifest.Version;
                        r["update"] = u.Available;
                        r["launcher_update"] = u.LauncherNewer;
                        r["protocol_changed"] = u.ProtocolChanged;
                        r["ok"] = true;
                        break;
                    case "update":
                        UpdateInfo u2 = c.Check();
                        r["installed_before"] = u2.Installed ?? "";
                        r["available"] = u2.Manifest.Version;
                        if (u2.Available || a.ContainsKey("force"))
                        {
                            InstallResult ir = c.ApplyUpdate(u2, null);
                            r["installed_after"] = ir.Version;
                            r["notes"] = ir.Notes;
                            if (ir.LauncherPending)
                            {
                                // as the window does: DRBR Updater swaps the new launcher in once this process has ended
                                r["launcher_pending"] = ir.PendingLauncher;
                                r["launcher_swap"] = LauncherSwap.Start(p, ir.PendingLauncherSha ?? Hash.Sha256File(ir.PendingLauncher), Process.GetCurrentProcess().Id, false);
                            }
                        }
                        r["ok"] = true;
                        break;
                    case "play":
                        PlayResult pr = c.Play(null, a.ContainsKey("no-wait") ? 0 : 120);
                        r["ok"] = pr.Started;
                        r["start"] = pr.StartResult;
                        r["room"] = pr.Room;
                        r["notes"] = pr.Notes;
                        if (a.ContainsKey("wait-exit") && pr.Game != null)
                        {
                            pr.Game.WaitForExit();
                            List<string> diff = c.AfterGame();
                            r["vanilla_changes"] = diff;
                        }
                        rc = pr.Started ? 0 : 11;
                        break;
                    case "status":
                        r["installed"] = c.Engine.InstalledVersion() ?? "";
                        r["last_start"] = SaveProfile.ReadLastStart(p);
                        r["ok"] = true;
                        break;
                    case "uninstall":
                        c.Engine.Uninstall(a.ContainsKey("remove-saves"), Process.GetCurrentProcess().MainModule.FileName);
                        r["ok"] = true;
                        break;
                }
            }
            catch (DrbrException e)
            {
                r["ok"] = false; r["error"] = e.Message; r["code"] = e.Code;
                Log.Error(what + ": " + e.Message);
                rc = 20;
            }
            catch (Exception e)
            {
                r["ok"] = false; r["error"] = e.ToString();
                Log.Error(what + ": " + e);
                rc = 21;
            }
            if (a.ContainsKey("result")) { try { Fs.WriteAtomicText(a["result"], Json.Write(r)); } catch { } }
            return rc;
        }
    }
}
