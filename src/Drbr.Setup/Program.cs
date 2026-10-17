// DRBR-Setup.exe - installs DRBR: finds DELTARUNE, checks it, builds DRBR's own copy of the game (Steam's stays as it is),
// sets up the provided starting save, installs DRBR Launcher, makes shortcuts, verifies everything, offers to play.
// The DRBR package (payload) is appended to this exe (or, for development, a "payload" folder next to it).
// Silent: DRBR-Setup.exe /S [--game "<DELTARUNE folder>"] [--dir "<DRBR folder>"] [--start-mode template|continue]
//         [--no-shortcuts] [--no-uninstall-entry] [--result <file.json>]
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Windows.Forms;

namespace Drbr
{
    static class SetupProgram
    {
        [STAThread]
        static int Main(string[] args)
        {
            Dictionary<string, string> a = Args(args);
            DrbrPaths p = new DrbrPaths(a.ContainsKey("dir") ? DrbrFolder(a["dir"]) : null);
            Log.Open(p.LogDir, "DRBR Setup");
            bool silent = a.ContainsKey("S") || a.ContainsKey("s") || a.ContainsKey("silent");
            if (silent) return Silent(p, a);
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm(p, a));
            return 0;
        }

        /// <summary>DRBR always installs into a folder of its own (a chosen "C:\Games" becomes "C:\Games\DRBR").</summary>
        public static string DrbrFolder(string chosen)
        {
            string full = Path.GetFullPath(chosen);
            return Path.GetFileName(full.TrimEnd('\\', '/')).Equals("DRBR", StringComparison.OrdinalIgnoreCase) ? full : Path.Combine(full, "DRBR");
        }

        static Dictionary<string, string> Args(string[] args)
        {
            Dictionary<string, string> a = new Dictionary<string, string>(StringComparer.Ordinal);
            for (int i = 0; i < args.Length; i++)
            {
                string s = args[i];
                if (!s.StartsWith("--") && !s.StartsWith("/")) continue;
                string k = s.TrimStart('-', '/');
                string v = (i + 1 < args.Length && !args[i + 1].StartsWith("--") && !args[i + 1].StartsWith("/")) ? args[++i] : "1";
                a[k] = v;
            }
            return a;
        }

        static int Silent(DrbrPaths p, Dictionary<string, string> a)
        {
            JsonObject r = new JsonObject();
            int rc = 0;
            string tmp = null;
            try
            {
                string payload = Payload.Extract(p, out tmp);
                Manifest m = Manifest.Load(Path.Combine(payload, "payload.json"));
                string game = a.ContainsKey("game") ? a["game"] : null;
                if (game == null)
                {
                    foreach (string c in GameLocator.Candidates()) { game = c; break; }
                }
                if (game == null) throw new DrbrException("game_missing", "DELTARUNE was not found. Give its folder with --game.");
                GameReport g = GameCheck.Inspect(game, m.SupportedGameBuilds);
                r["game"] = game;
                r["game_state"] = g.State;
                InstallResult ir = new InstallEngine(p).Install(new InstallOptions
                {
                    GameDir = game,
                    PayloadDir = payload,
                    StartMode = a.ContainsKey("start-mode") ? a["start-mode"] : null,
                    Shortcuts = !a.ContainsKey("no-shortcuts"),
                    RegisterUninstall = !a.ContainsKey("no-uninstall-entry"),
                    Operation = File.Exists(p.StateFile) ? "reinstall" : "install"
                });
                List<string> did = SaveProfile.EnsureBundle(p, m.SaveProfile, Settings.Load(p).StartMode);
                r["ok"] = true;
                r["version"] = ir.Version;
                r["notes"] = ir.Notes;
                r["profile"] = did;
                r["root"] = p.Root;
            }
            catch (DrbrException e) { r["ok"] = false; r["error"] = e.Message; r["code"] = e.Code; rc = 20; Log.Error(e.Message); }
            catch (Exception e) { r["ok"] = false; r["error"] = e.ToString(); rc = 21; Log.Error(e.ToString()); }
            finally { if (tmp != null) { try { Fs.DeleteDir(tmp); } catch { } } }
            if (a.ContainsKey("result")) { try { Fs.WriteAtomicText(a["result"], Json.Write(r)); } catch { } }
            return rc;
        }
    }

    /// <summary>The DRBR package carried by the Setup: a zip appended to DRBR-Setup.exe, followed by its length (8 bytes,
    /// little endian) and "DRBRPAY1". For development, a "payload" folder next to the exe works too.</summary>
    static class Payload
    {
        const string Magic = "DRBRPAY1";

        /// <summary>A "payload" folder next to the Setup (a package copied in pieces: a big file may be there as
        /// name.part0, name.part1 ...). Used as it is when complete; else copied to staging with the pieces joined.</summary>
        static string FromFolder(DrbrPaths p, string dir, out string tempDir)
        {
            tempDir = null;
            Manifest m = Manifest.Load(Path.Combine(dir, "payload.json"));
            bool split = false;
            foreach (PayloadFile f in m.Files)
                if (!File.Exists(Path.Combine(dir, f.File)) && File.Exists(Path.Combine(dir, f.File + ".part0"))) split = true;
            if (!split) { Log.Info("Using the payload folder next to the Setup: " + dir); return dir; }
            tempDir = Path.Combine(p.StagingDir, "setup-" + Guid.NewGuid().ToString("N").Substring(0, 8));
            Directory.CreateDirectory(tempDir);
            File.Copy(Path.Combine(dir, "payload.json"), Path.Combine(tempDir, "payload.json"));
            foreach (PayloadFile f in m.Files)
            {
                string dst = Path.Combine(tempDir, f.File);
                if (File.Exists(Path.Combine(dir, f.File))) { File.Copy(Path.Combine(dir, f.File), dst); continue; }
                if (!File.Exists(Path.Combine(dir, f.File + ".part0"))) continue;   // a missing file is reported by the payload check
                using (FileStream o = new FileStream(dst, FileMode.Create, FileAccess.Write))
                {
                    for (int i = 0; File.Exists(Path.Combine(dir, f.File + ".part" + i)); i++)
                        using (FileStream x = new FileStream(Path.Combine(dir, f.File + ".part" + i), FileMode.Open, FileAccess.Read)) x.CopyTo(o, 1 << 20);
                }
            }
            Log.Info("DRBR package pieces joined from " + dir + " into " + tempDir);
            return tempDir;
        }

        public static string Extract(DrbrPaths p, out string tempDir)
        {
            tempDir = null;
            // an earlier Setup that was closed or crashed may have left its unpacked package: it goes first
            if (Directory.Exists(p.StagingDir))
                foreach (string old in Directory.GetDirectories(p.StagingDir, "setup-*"))
                {
                    try { Fs.DeleteDir(old); } catch { }
                }
            string exe = Process.GetCurrentProcess().MainModule.FileName;
            string beside = Path.Combine(Path.GetDirectoryName(exe), "payload");
            if (File.Exists(Path.Combine(beside, "payload.json"))) return FromFolder(p, beside, out tempDir);
            using (FileStream fs = new FileStream(exe, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                if (fs.Length < 32) throw new DrbrException("no_payload", "This DRBR-Setup.exe carries no DRBR package (it is damaged or incomplete). Download DRBR-Setup.exe again.");
                byte[] tail = new byte[16];
                fs.Seek(-16, SeekOrigin.End);
                fs.Read(tail, 0, 16);
                if (Encoding.ASCII.GetString(tail, 8, 8) != Magic) throw new DrbrException("no_payload", "This DRBR-Setup.exe carries no DRBR package (it is damaged or incomplete). Download DRBR-Setup.exe again.");
                long len = BitConverter.ToInt64(tail, 0);
                if (len <= 0 || len > fs.Length - 16) throw new DrbrException("no_payload", "This DRBR-Setup.exe's package is damaged. Download DRBR-Setup.exe again.");
                tempDir = Path.Combine(p.StagingDir, "setup-" + Guid.NewGuid().ToString("N").Substring(0, 8));
                Directory.CreateDirectory(tempDir);
                using (SubStream ss = new SubStream(fs, fs.Length - 16 - len, len))
                using (ZipArchive z = new ZipArchive(ss, ZipArchiveMode.Read))
                {
                    foreach (ZipArchiveEntry e in z.Entries)
                    {
                        if (e.FullName.EndsWith("/")) continue;
                        string dest = Fs.Under(tempDir, e.FullName);
                        Directory.CreateDirectory(Path.GetDirectoryName(dest));
                        using (Stream s = e.Open())
                        using (FileStream o = new FileStream(dest, FileMode.Create, FileAccess.Write)) s.CopyTo(o, 1 << 20);
                    }
                }
                Log.Info("DRBR package unpacked (" + Fs.Mb(len) + ") to " + tempDir);
                return tempDir;
            }
        }
    }

    /// <summary>A read-only window onto part of a stream (the zip inside the exe).</summary>
    sealed class SubStream : Stream
    {
        readonly Stream s;
        readonly long start, len;
        long pos;
        public SubStream(Stream s, long start, long len) { this.s = s; this.start = start; this.len = len; }
        public override bool CanRead { get { return true; } }
        public override bool CanSeek { get { return true; } }
        public override bool CanWrite { get { return false; } }
        public override long Length { get { return len; } }
        public override long Position { get { return pos; } set { pos = value; } }
        public override void Flush() { }
        public override int Read(byte[] buffer, int offset, int count)
        {
            if (pos >= len) return 0;
            if (count > len - pos) count = (int)(len - pos);
            s.Seek(start + pos, SeekOrigin.Begin);
            int n = s.Read(buffer, offset, count);
            pos += n;
            return n;
        }
        public override long Seek(long offset, SeekOrigin origin)
        {
            long np = origin == SeekOrigin.Begin ? offset : origin == SeekOrigin.Current ? pos + offset : len + offset;
            if (np < 0) throw new IOException("seek before the start");
            pos = np;
            return pos;
        }
        public override void SetLength(long value) { throw new NotSupportedException(); }
        public override void Write(byte[] buffer, int offset, int count) { throw new NotSupportedException(); }
    }
}
