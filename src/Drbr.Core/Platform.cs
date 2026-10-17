// DRBR - processes (the game, xdelta3), shortcuts, the Windows uninstall entry, junctions.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;

namespace Drbr
{
    public static class Proc
    {
        public static bool IsWindows { get { return Environment.OSVersion.Platform == PlatformID.Win32NT; } }

        /// <summary>A DELTARUNE.exe running from DRBR's own copy of the game (any DELTARUNE.exe whose path cannot be read
        /// counts too: better to wait than to change files under a running game).</summary>
        public static bool DrbrGameRunning(DrbrPaths p, out string detail)
        {
            detail = "";
            Process[] ps;
            try { ps = Process.GetProcessesByName("DELTARUNE"); } catch { return false; }
            string game = Path.GetFullPath(p.GameDir).TrimEnd('\\', '/') + Path.DirectorySeparatorChar;
            foreach (Process x in ps)
            {
                string path = null;
                try { path = x.MainModule.FileName; } catch { }
                if (path == null) { detail = "DELTARUNE.exe (pid " + x.Id + ")"; return true; }
                if (path.StartsWith(game, StringComparison.OrdinalIgnoreCase)) { detail = path + " (pid " + x.Id + ")"; return true; }
            }
            return false;
        }

        public static Process StartGame(DrbrPaths p, string extraArgs = "")
        {
            // as Knight Hub's PLAY_KNIGHT_HUB.bat started it (the working folder is the game folder, the data file relative)
            ProcessStartInfo si = new ProcessStartInfo(p.GameExe, "-game \"chapter3_windows\\data.win\"" + (string.IsNullOrEmpty(extraArgs) ? "" : " " + extraArgs))
            {
                WorkingDirectory = p.GameDir,
                UseShellExecute = false
            };
            Log.Info("Starting " + si.FileName + " " + si.Arguments + " in " + si.WorkingDirectory);
            return Process.Start(si);
        }

        /// <summary>Runs a tool, waits, returns (exit code, its output).</summary>
        public static int Run(string exe, string args, string workDir, out string output, int timeoutMs = 30 * 60 * 1000)
        {
            ProcessStartInfo si = new ProcessStartInfo(exe, args)
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = string.IsNullOrEmpty(workDir) ? Environment.CurrentDirectory : workDir
            };
            StringBuilder sb = new StringBuilder();
            using (Process x = new Process { StartInfo = si })
            {
                x.OutputDataReceived += (s, e) => { if (e.Data != null) lock (sb) sb.AppendLine(e.Data); };
                x.ErrorDataReceived += (s, e) => { if (e.Data != null) lock (sb) sb.AppendLine(e.Data); };
                x.Start();
                x.BeginOutputReadLine();
                x.BeginErrorReadLine();
                if (!x.WaitForExit(timeoutMs))
                {
                    try { x.Kill(); } catch { }
                    output = sb.ToString();
                    return -1;
                }
                x.WaitForExit();
                output = sb.ToString();
                return x.ExitCode;
            }
        }
    }

    /// <summary>xdelta3 (VCDIFF): the same tool and arguments Knight Hub's installer used ("-d -s source patch out").</summary>
    public static class Xdelta
    {
        public static string ToolPath(DrbrPaths p, string payloadDir)
        {
            string env = Environment.GetEnvironmentVariable("DRBR_XDELTA");
            if (!string.IsNullOrEmpty(env)) return env;
            if (!Proc.IsWindows) return "xdelta3";   // the Linux tests use the system's xdelta3
            if (!string.IsNullOrEmpty(payloadDir) && File.Exists(Path.Combine(payloadDir, "xdelta3.exe"))) return Path.Combine(payloadDir, "xdelta3.exe");
            return p.Xdelta;
        }

        public static void Apply(string tool, string source, string patch, string output)
        {
            if (File.Exists(output)) File.Delete(output);
            string text;
            int rc = Proc.Run(tool, "-d -f -s " + Q(source) + " " + Q(patch) + " " + Q(output), Path.GetDirectoryName(output), out text);
            if (rc != 0 || !File.Exists(output))
            {
                if (text.Length > 1500) text = text.Substring(0, 1500);
                throw new DrbrException("patch_failed", "Applying the DRBR game patch failed (xdelta3 exit code " + rc + "). " + text.Trim());
            }
        }

        static string Q(string s) { return "\"" + s + "\""; }
    }

    public static class Shell
    {
        /// <summary>A .lnk through Windows' own WScript.Shell (no extra library).</summary>
        public static bool CreateShortcut(string lnk, string target, string args, string workDir, string description)
        {
            if (!Proc.IsWindows) return false;
            try
            {
                Type t = Type.GetTypeFromProgID("WScript.Shell");
                if (t == null) return false;
                object shell = Activator.CreateInstance(t);
                object sc = t.InvokeMember("CreateShortcut", System.Reflection.BindingFlags.InvokeMethod, null, shell, new object[] { lnk });
                Type st = sc.GetType();
                st.InvokeMember("TargetPath", System.Reflection.BindingFlags.SetProperty, null, sc, new object[] { target });
                st.InvokeMember("Arguments", System.Reflection.BindingFlags.SetProperty, null, sc, new object[] { args ?? "" });
                st.InvokeMember("WorkingDirectory", System.Reflection.BindingFlags.SetProperty, null, sc, new object[] { workDir });
                st.InvokeMember("Description", System.Reflection.BindingFlags.SetProperty, null, sc, new object[] { description ?? "" });
                st.InvokeMember("IconLocation", System.Reflection.BindingFlags.SetProperty, null, sc, new object[] { target + ",0" });
                st.InvokeMember("Save", System.Reflection.BindingFlags.InvokeMethod, null, sc, null);
                return File.Exists(lnk);
            }
            catch (Exception e)
            {
                Log.Warn("Shortcut not made (" + lnk + "): " + e.Message);
                return false;
            }
        }

        public static void Shortcuts(DrbrPaths p, bool desktop, bool startMenu)
        {
            if (desktop)
            {
                string d = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                if (!string.IsNullOrEmpty(d)) CreateShortcut(Path.Combine(d, "DRBR.lnk"), p.LauncherExe, "", p.Root, "DRBR - DELTARUNE BATTLE ROYALE");
            }
            if (startMenu)
            {
                string sm = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                if (!string.IsNullOrEmpty(sm))
                {
                    string dir = Path.Combine(sm, "DRBR");
                    Directory.CreateDirectory(dir);
                    CreateShortcut(Path.Combine(dir, "DRBR.lnk"), p.LauncherExe, "", p.Root, "DRBR - DELTARUNE BATTLE ROYALE");
                    CreateShortcut(Path.Combine(dir, "Uninstall DRBR.lnk"), p.LauncherExe, "--uninstall", p.Root, "Remove DRBR (your DELTARUNE and its saves stay)");
                }
            }
        }

        public static void RemoveShortcuts()
        {
            if (!Proc.IsWindows) return;
            try
            {
                string d = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                if (!string.IsNullOrEmpty(d) && File.Exists(Path.Combine(d, "DRBR.lnk"))) File.Delete(Path.Combine(d, "DRBR.lnk"));
                string sm = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                if (!string.IsNullOrEmpty(sm) && Directory.Exists(Path.Combine(sm, "DRBR"))) Fs.DeleteDir(Path.Combine(sm, "DRBR"));
            }
            catch (Exception e) { Log.Warn("Shortcuts not removed: " + e.Message); }
        }

        const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\DRBR";

        /// <summary>Apps & features entry (per user: HKCU, no admin rights).</summary>
        public static void RegisterUninstall(DrbrPaths p, string version, long sizeBytes)
        {
            if (!Proc.IsWindows) return;
            try
            {
                using (var k = Microsoft.Win32.Registry.CurrentUser.CreateSubKey(UninstallKey))
                {
                    k.SetValue("DisplayName", "DRBR - DELTARUNE BATTLE ROYALE");
                    k.SetValue("DisplayVersion", version);
                    k.SetValue("Publisher", "DRBR (fan mod by ImperfectNORE)");
                    k.SetValue("InstallLocation", p.Root);
                    k.SetValue("DisplayIcon", p.LauncherExe + ",0");
                    k.SetValue("UninstallString", "\"" + p.LauncherExe + "\" --uninstall");
                    k.SetValue("QuietUninstallString", "\"" + p.LauncherExe + "\" --uninstall --quiet");
                    k.SetValue("EstimatedSize", (int)Math.Min(int.MaxValue, sizeBytes / 1024), Microsoft.Win32.RegistryValueKind.DWord);
                    k.SetValue("NoModify", 1, Microsoft.Win32.RegistryValueKind.DWord);
                    k.SetValue("NoRepair", 1, Microsoft.Win32.RegistryValueKind.DWord);
                }
            }
            catch (Exception e) { Log.Warn("Uninstall entry not written: " + e.Message); }
        }

        public static void UnregisterUninstall()
        {
            if (!Proc.IsWindows) return;
            try { Microsoft.Win32.Registry.CurrentUser.DeleteSubKeyTree(UninstallKey, false); } catch { }
        }

        /// <summary>A directory junction (no admin rights needed), through cmd's mklink /J.</summary>
        public static bool Junction(string link, string target)
        {
            if (!Proc.IsWindows || Directory.Exists(link)) return false;
            string o;
            int rc = Proc.Run("cmd.exe", "/c mklink /J \"" + link + "\" \"" + target + "\"", Path.GetDirectoryName(link), out o, 60000);
            return rc == 0 && Directory.Exists(link);
        }
    }
}
