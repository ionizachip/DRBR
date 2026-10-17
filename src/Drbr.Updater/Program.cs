// DRBR Updater - replaces DRBR Launcher.exe with its new version once the launcher has closed (a running program cannot
// overwrite itself), checks the new file's checksum, puts the old one back if anything fails, and restarts the launcher.
// Usage: "DRBR Updater.exe" --swap <staged file> --target <file> --sha256 <hash> [--wait-pid <pid>] [--restart] [--root <DRBR folder>]
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;

namespace Drbr
{
    static class UpdaterProgram
    {
        [STAThread]
        static int Main(string[] args)
        {
            Dictionary<string, string> a = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < args.Length; i++)
            {
                if (!args[i].StartsWith("--")) continue;
                string k = args[i].Substring(2);
                string v = (i + 1 < args.Length && !args[i + 1].StartsWith("--")) ? args[++i] : "1";
                a[k] = v;
            }
            string root = a.ContainsKey("root") ? a["root"] : null;
            DrbrPaths p = new DrbrPaths(root);
            Log.Open(p.LogDir, "DRBR Updater");
            if (!a.ContainsKey("swap") || !a.ContainsKey("target") || !a.ContainsKey("sha256"))
            {
                Log.Error("DRBR Updater: --swap, --target and --sha256 are needed.");
                return 2;
            }
            string staged = a["swap"], target = a["target"], sha = a["sha256"];
            int rc = Swap(staged, target, sha, a.ContainsKey("wait-pid") ? a["wait-pid"] : null);
            if (a.ContainsKey("restart") && File.Exists(target))
            {
                try { Process.Start(new ProcessStartInfo(target, rc == 0 ? "--updated" : "--update-failed") { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(target) }); }
                catch (Exception e) { Log.Error("Could not restart " + target + ": " + e.Message); }
            }
            return rc;
        }

        static int Swap(string staged, string target, string sha, string pid)
        {
            // 1. the launcher has to be gone
            if (!string.IsNullOrEmpty(pid))
            {
                try
                {
                    Process x = Process.GetProcessById(int.Parse(pid));
                    if (!x.WaitForExit(60000)) { Log.Error("The launcher (pid " + pid + ") did not close; the update of the launcher waits for the next start."); return 3; }
                }
                catch (ArgumentException) { }   // already gone
                catch (Exception e) { Log.Warn("Waiting for the launcher: " + e.Message); }
            }
            // 2. the new file has to be the right one
            if (!File.Exists(staged) || !Hash.Same(Hash.Sha256File(staged), sha))
            {
                Log.Error("The new launcher (" + staged + ") is missing or failed its checksum; nothing was changed.");
                return 4;
            }
            string old = target + ".old";
            for (int attempt = 0; attempt < 20; attempt++)
            {
                try
                {
                    if (File.Exists(old)) File.Delete(old);
                    if (File.Exists(target)) File.Move(target, old);
                    File.Copy(staged, target, false);
                    if (!Hash.Same(Hash.Sha256File(target), sha)) throw new IOException("the copied launcher failed its checksum");
                    try { File.Delete(old); } catch { }
                    try { File.Delete(staged); } catch { }
                    Log.Info("DRBR Launcher updated (" + target + ").");
                    return 0;
                }
                catch (Exception e)
                {
                    Log.Warn("Swap attempt " + (attempt + 1) + " failed: " + e.Message);
                    try
                    {
                        if (File.Exists(old))
                        {
                            if (File.Exists(target)) File.Delete(target);
                            File.Move(old, target);
                        }
                    }
                    catch (Exception e2) { Log.Error("Could not put the old launcher back: " + e2.Message); }
                    Thread.Sleep(500);
                }
            }
            Log.Error("The launcher could not be replaced; the old one was kept.");
            return 5;
        }
    }
}
