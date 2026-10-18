// DRBR - where things are, finding DELTARUNE, and telling what state the player's game is in.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

namespace Drbr
{
    /// <summary>Every place DRBR uses. Root is the DRBR install (default %LOCALAPPDATA%\DRBR - per user, no admin rights).</summary>
    public sealed class DrbrPaths
    {
        public readonly string Root;
        public readonly string SaveArea;      // GameMaker's save folder for DELTARUNE: %LOCALAPPDATA%\DELTARUNE

        public DrbrPaths(string root = null, string saveArea = null)
        {
            string local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            Root = Path.GetFullPath(string.IsNullOrEmpty(root) ? Path.Combine(local, "DRBR") : root);
            SaveArea = Path.GetFullPath(string.IsNullOrEmpty(saveArea) ? Path.Combine(local, "DELTARUNE") : saveArea);
        }

        public string GameDir { get { return Path.Combine(Root, "game"); } }
        public string Chapter3 { get { return Path.Combine(GameDir, "chapter3_windows"); } }
        public string DataWin { get { return Path.Combine(Chapter3, "data.win"); } }
        public string GameExe { get { return Path.Combine(GameDir, "DELTARUNE.exe"); } }
        public string BundleDataDir { get { return Path.Combine(Chapter3, "drbr_data"); } }
        public string BundleTemplate { get { return Path.Combine(BundleDataDir, "start_filech3"); } }
        public string BundleProfileCfg { get { return Path.Combine(BundleDataDir, "drbr_profile.cfg"); } }
        public string BaseDir { get { return Path.Combine(Root, "base"); } }
        public string VanillaCopy { get { return Path.Combine(BaseDir, "data.win.vanilla"); } }
        public string PayloadDir { get { return Path.Combine(Root, "payload"); } }
        public string StagingDir { get { return Path.Combine(Root, "staging"); } }
        public string BackupDir { get { return Path.Combine(Root, "backups"); } }
        public string LogDir { get { return Path.Combine(Root, "logs"); } }
        public string StateFile { get { return Path.Combine(Root, "drbr-install.json"); } }
        public string SettingsFile { get { return Path.Combine(Root, "drbr-settings.json"); } }
        public string LockFile { get { return Path.Combine(Root, "drbr-transaction.json"); } }
        public string LauncherExe { get { return Path.Combine(Root, "DRBR Launcher.exe"); } }
        public string UpdaterExe { get { return Path.Combine(Root, "DRBR Updater.exe"); } }
        public string PendingLauncher { get { return Path.Combine(StagingDir, "pending", "DRBR Launcher.exe"); } }   // waits for DRBR Updater
        public string Xdelta { get { return Path.Combine(Root, "tools", "xdelta3.exe"); } }
        public string SaveProfileDir { get { return Path.Combine(Root, "save-profile"); } }   // the launcher's own copy of the template + profile.json
        public string LiveProfile { get { return Path.Combine(SaveArea, "drbr_profile"); } }  // what the game writes in DRBR mode
        public string LastStart { get { return Path.Combine(LiveProfile, "last_start.ini"); } }
        public string PendingJoin { get { return Path.Combine(LiveProfile, "pending_join.ini"); } }
    }

    /// <summary>Finds the player's DELTARUNE (Steam): the registry's Steam folders, every Steam library, the usual places.</summary>
    public static class GameLocator
    {
        public const string SteamAppId = "1671210";

        public static bool IsGameDir(string dir)
        {
            try
            {
                return !string.IsNullOrEmpty(dir) && File.Exists(Path.Combine(dir, "DELTARUNE.exe")) &&
                       File.Exists(Path.Combine(dir, "chapter3_windows", "data.win"));
            }
            catch { return false; }
        }

        public static List<string> Candidates()
        {
            List<string> steamRoots = new List<string>();
            foreach (string s in RegistrySteamPaths()) Add(steamRoots, s);
            string pf86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
            string pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            if (!string.IsNullOrEmpty(pf86)) Add(steamRoots, Path.Combine(pf86, "Steam"));
            if (!string.IsNullOrEmpty(pf)) Add(steamRoots, Path.Combine(pf, "Steam"));

            List<string> libraries = new List<string>();
            foreach (string root in steamRoots)
            {
                Add(libraries, root);
                foreach (string lib in LibraryFolders(Path.Combine(root, "steamapps", "libraryfolders.vdf"))) Add(libraries, lib);
            }
            foreach (char d in "CDEFGHIJ")
            {
                Add(libraries, d + @":\SteamLibrary");
                Add(libraries, d + @":\Steam");
                Add(libraries, d + @":\Games\Steam");
                Add(libraries, d + @":\Program Files (x86)\Steam");
            }

            List<string> found = new List<string>();
            foreach (string lib in libraries)
            {
                string installdir = "DELTARUNE";
                try
                {
                    string acf = Path.Combine(lib, "steamapps", "appmanifest_" + SteamAppId + ".acf");
                    if (File.Exists(acf))
                    {
                        Match m = Regex.Match(File.ReadAllText(acf), "\"installdir\"\\s+\"([^\"]+)\"", RegexOptions.IgnoreCase);
                        if (m.Success) installdir = m.Groups[1].Value;
                    }
                }
                catch { }
                string dir = Path.Combine(lib, "steamapps", "common", installdir);
                if (IsGameDir(dir)) Add(found, dir);
            }
            return found;
        }

        static void Add(List<string> l, string p)
        {
            if (string.IsNullOrEmpty(p)) return;
            try { p = Path.GetFullPath(p.Replace('/', Path.DirectorySeparatorChar)); } catch { return; }
            foreach (string x in l) if (string.Equals(x, p, StringComparison.OrdinalIgnoreCase)) return;
            l.Add(p);
        }

        public static List<string> LibraryFolders(string vdf)
        {
            List<string> r = new List<string>();
            try
            {
                if (!File.Exists(vdf)) return r;
                foreach (Match m in Regex.Matches(File.ReadAllText(vdf), "\"path\"\\s+\"([^\"]+)\"", RegexOptions.IgnoreCase))
                    r.Add(m.Groups[1].Value.Replace("\\\\", "\\"));
            }
            catch { }
            return r;
        }

        static IEnumerable<string> RegistrySteamPaths()
        {
            List<string> r = new List<string>();
            if (Environment.OSVersion.Platform != PlatformID.Win32NT) return r;
            try
            {
                using (var k = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@"Software\Valve\Steam"))
                    if (k != null) { object v = k.GetValue("SteamPath"); if (v != null) r.Add(v.ToString()); }
            }
            catch { }
            foreach (string sub in new[] { @"SOFTWARE\WOW6432Node\Valve\Steam", @"SOFTWARE\Valve\Steam" })
            {
                try
                {
                    using (var k = Microsoft.Win32.Registry.LocalMachine.OpenSubKey(sub))
                        if (k != null) { object v = k.GetValue("InstallPath"); if (v != null) r.Add(v.ToString()); }
                }
                catch { }
            }
            return r;
        }
    }

    /// <summary>A vanilla Chapter 3 data.win this DRBR release can be built from.</summary>
    public sealed class SupportedBuild
    {
        public string Name;
        public long Size;
        public string Sha256;
    }

    /// <summary>What the player's DELTARUNE is: where a clean (vanilla) Chapter 3 data.win can be read from, and what else is there.</summary>
    public sealed class GameReport
    {
        public string GameDir;
        public bool Found;
        public string State = "missing";     // vanilla | knight_hub_in_place | modified | unsupported | missing
        public string VanillaSource;          // a verified vanilla data.win (the game's own, or the old Knight Hub's data.win.vanilla)
        public SupportedBuild Build;
        public string DataWinSha256;
        public long DataWinSize;
        public readonly List<string> Notes = new List<string>();   // other mods and things worth knowing
        public string Summary = "";

        public bool Compatible { get { return Found && VanillaSource != null; } }
    }

    public static class GameCheck
    {
        // the knight hub files the old in-place installer put into Steam's chapter3_windows (never copied into DRBR)
        static readonly string[] InjectorDlls = { "dxgi.dll", "d3d11.dll", "d3d9.dll", "dinput8.dll", "winmm.dll", "version.dll", "opengl32.dll", "sl.interposer.dll" };

        public static GameReport Inspect(string gameDir, IList<SupportedBuild> supported, Func<string, string> sha = null)
        {
            if (sha == null) sha = Hash.Sha256File;
            GameReport r = new GameReport { GameDir = gameDir };
            if (!GameLocator.IsGameDir(gameDir))
            {
                r.Summary = "DELTARUNE was not found there (no DELTARUNE.exe with chapter3_windows\\data.win).";
                return r;
            }
            r.Found = true;
            string dw = Path.Combine(gameDir, "chapter3_windows", "data.win");
            r.DataWinSize = new FileInfo(dw).Length;
            r.DataWinSha256 = sha(dw);
            SupportedBuild b = Match(supported, r.DataWinSize, r.DataWinSha256);
            if (b != null)
            {
                r.State = "vanilla";
                r.VanillaSource = dw;
                r.Build = b;
                r.Summary = "DELTARUNE found: " + b.Name + " (unmodified).";
            }
            else
            {
                // the old in-place Knight Hub: its backup of the original is next to it
                string bak = Path.Combine(gameDir, "chapter3_windows", "data.win.vanilla");
                SupportedBuild bb = null;
                if (File.Exists(bak))
                {
                    // the backup is hashed for itself: a modified data.win of the same size is another file (update 10:
                    // this used to reuse data.win's checksum when the sizes were equal, and refused a good backup)
                    long bs = new FileInfo(bak).Length;
                    bool sized = false;
                    if (supported != null) foreach (SupportedBuild s in supported) if (s.Size == bs) sized = true;
                    if (sized) bb = Match(supported, bs, sha(bak));
                }
                bool hub = File.Exists(Path.Combine(gameDir, "chapter3_windows", "knight_hub_build.txt"));
                if (bb != null)
                {
                    r.State = hub ? "knight_hub_in_place" : "modified";
                    r.VanillaSource = bak;
                    r.Build = bb;
                    r.Summary = hub ? "DELTARUNE found. Its Chapter 3 has the older Knight Hub installed in place; DRBR uses the clean backup (data.win.vanilla) and leaves Steam's copy as it is."
                                    : "DELTARUNE found. Its Chapter 3 data.win is modified, but a clean backup (data.win.vanilla) is there; DRBR uses that.";
                    r.Notes.Add(hub ? "The older Knight Hub is installed in Steam's Chapter 3 (in place). DRBR does not need it; RESTORE_VANILLA.bat in chapter3_windows puts the original back." :
                                      "Steam's Chapter 3 data.win is modified (another mod?).");
                }
                else if (r.DataWinSize < 50L * 1024 * 1024 || r.DataWinSize > 400L * 1024 * 1024)
                {
                    r.State = "unsupported";
                    r.Summary = "This DELTARUNE's Chapter 3 is not one this DRBR version supports.";
                }
                else
                {
                    r.State = hub ? "knight_hub_in_place" : "unsupported";
                    r.Summary = hub ? "Steam's Chapter 3 has an older Knight Hub installed in place and no clean backup was found. In Steam: right-click DELTARUNE > Properties > Installed Files > Verify integrity of game files, then try again."
                                    : "This DELTARUNE's Chapter 3 data.win is not a version DRBR supports (a different game version, or modified by another mod). In Steam: right-click DELTARUNE > Properties > Installed Files > Verify integrity of game files. If DELTARUNE was updated, wait for a DRBR update.";
                }
            }
            foreach (string dll in InjectorDlls)
                if (File.Exists(Path.Combine(gameDir, dll))) r.Notes.Add("Another mod's " + dll + " is in the game folder (not copied into DRBR).");
            if (File.Exists(Path.Combine(gameDir, "ReShade.ini")) || File.Exists(Path.Combine(gameDir, "ReShade.log")) || File.Exists(Path.Combine(gameDir, "ReShade.log1")))
                r.Notes.Add("ReShade is in the game folder (not copied into DRBR).");
            return r;
        }

        public static SupportedBuild Match(IList<SupportedBuild> supported, long size, string sha)
        {
            if (supported == null) return null;
            foreach (SupportedBuild b in supported)
                if (b.Size == size && Hash.Same(b.Sha256, sha)) return b;
            return null;
        }

        /// <summary>The vanilla files of Chapter 3 DRBR copies from the player's game (everything the game reads; nothing a mod added).</summary>
        public static bool IsVanillaChapterFile(string rel)
        {
            string r = rel.Replace('\\', '/');
            string low = r.ToLowerInvariant();
            if (low.StartsWith("lang/") || low.StartsWith("vid/")) return true;
            if (low.Contains("/")) return false;
            if (low == "options.ini") return true;
            if (low.EndsWith(".ogg") || low.EndsWith(".dat")) return true;
            return false;
        }
    }
}
