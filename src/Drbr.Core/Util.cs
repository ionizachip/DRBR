// DRBR - logging, hashing, versions, file helpers.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Drbr
{
    /// <summary>One log for every DRBR program: %LOCALAPPDATA%\DRBR\logs\drbr-YYYY-MM-DD.log (plus whatever listens).</summary>
    public static class Log
    {
        static readonly object Gate = new object();
        public static string FilePath;
        public static event Action<string, string> Line;   // (level, text)

        public static void Open(string logDir, string program)
        {
            try
            {
                Directory.CreateDirectory(logDir);
                FilePath = Path.Combine(logDir, "drbr-" + DateTime.Now.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) + ".log");
                Write("INFO", "==== " + program + " " + BuildInfo.Version + " (mod " + BuildInfo.ModBuild + ") started ====");
            }
            catch { FilePath = null; }
        }

        public static void Info(string t) { Write("INFO", t); }
        public static void Warn(string t) { Write("WARN", t); }
        public static void Error(string t) { Write("ERROR", t); }

        public static void Write(string level, string text)
        {
            string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture) + " [" + level + "] " + text;
            lock (Gate)
            {
                if (FilePath != null)
                {
                    try { File.AppendAllText(FilePath, line + Environment.NewLine, Encoding.UTF8); } catch { }
                }
            }
            Action<string, string> h = Line;
            if (h != null) { try { h(level, text); } catch { } }
        }
    }

    public static class Hash
    {
        public static string Sha256File(string path)
        {
            using (FileStream fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20))
                return Sha256Stream(fs);
        }

        public static string Sha256Stream(Stream s)
        {
            using (SHA256 h = SHA256.Create()) return Hex(h.ComputeHash(s));
        }

        public static string Sha256Bytes(byte[] b)
        {
            using (SHA256 h = SHA256.Create()) return Hex(h.ComputeHash(b));
        }

        public static string Sha1Bytes(byte[] b)
        {
            using (SHA1 h = SHA1.Create()) return Hex(h.ComputeHash(b));
        }

        public static string Hex(byte[] b)
        {
            StringBuilder sb = new StringBuilder(b.Length * 2);
            foreach (byte x in b) sb.Append(x.ToString("x2", CultureInfo.InvariantCulture));
            return sb.ToString();
        }

        public static bool IsSha256(string s)
        {
            if (s == null || s.Length != 64) return false;
            foreach (char c in s) if (!Uri.IsHexDigit(c)) return false;
            return true;
        }

        public static bool Same(string a, string b) { return string.Equals(a, b, StringComparison.OrdinalIgnoreCase); }
    }

    /// <summary>"1.2.10" style versions (any number of numeric parts; a "-beta" suffix sorts before the plain version).</summary>
    public static class Ver
    {
        public static int Compare(string a, string b)
        {
            string sa, sb;
            int[] pa = Parts(a, out sa), pb = Parts(b, out sb);
            for (int i = 0; i < Math.Max(pa.Length, pb.Length); i++)
            {
                int x = i < pa.Length ? pa[i] : 0, y = i < pb.Length ? pb[i] : 0;
                if (x != y) return x < y ? -1 : 1;
            }
            if (sa.Length == 0 && sb.Length > 0) return 1;
            if (sa.Length > 0 && sb.Length == 0) return -1;
            return string.CompareOrdinal(sa, sb) < 0 ? -1 : (string.CompareOrdinal(sa, sb) > 0 ? 1 : 0);
        }

        static int[] Parts(string v, out string suffix)
        {
            v = (v ?? "0").Trim().TrimStart('v', 'V');
            int dash = v.IndexOf('-');
            suffix = dash >= 0 ? v.Substring(dash + 1) : "";
            if (dash >= 0) v = v.Substring(0, dash);
            string[] s = v.Split('.');
            List<int> r = new List<int>();
            foreach (string p in s)
            {
                int n;
                r.Add(int.TryParse(p, NumberStyles.Integer, CultureInfo.InvariantCulture, out n) ? n : 0);
            }
            return r.ToArray();
        }

        public static bool IsNewer(string candidate, string installed) { return Compare(candidate, installed) > 0; }
    }

    public static class Fs
    {
        /// <summary>Write a file so a crash never leaves half of it: a temp file next to it, then a replace.</summary>
        public static void WriteAtomic(string path, byte[] data)
        {
            string dir = Path.GetDirectoryName(Path.GetFullPath(path));
            Directory.CreateDirectory(dir);
            string tmp = path + ".tmp-" + Guid.NewGuid().ToString("N").Substring(0, 8);
            File.WriteAllBytes(tmp, data);
            if (File.Exists(path))
            {
                try { File.Replace(tmp, path, null); return; }
                catch (PlatformNotSupportedException) { }
                catch (IOException) { }
                File.Delete(path);
            }
            File.Move(tmp, path);
        }

        public static void WriteAtomicText(string path, string text) { WriteAtomic(path, new UTF8Encoding(false).GetBytes(text)); }

        public static void CopyVerified(string src, string dst, string expectSha = null)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(dst)));
            string tmp = dst + ".part";
            if (File.Exists(tmp)) File.Delete(tmp);
            File.Copy(src, tmp, true);
            if (expectSha != null && !Hash.Same(Hash.Sha256File(tmp), expectSha))
            {
                File.Delete(tmp);
                throw new IOException("copied file failed its checksum: " + dst);
            }
            if (new FileInfo(tmp).Length != new FileInfo(src).Length)
            {
                File.Delete(tmp);
                throw new IOException("copied file has the wrong size: " + dst);
            }
            if (File.Exists(dst)) File.Delete(dst);
            File.Move(tmp, dst);
        }

        public static void DeleteDir(string dir)
        {
            if (!Directory.Exists(dir)) return;
            // a junction is removed as a link, never followed
            if ((File.GetAttributes(dir) & FileAttributes.ReparsePoint) != 0) { Directory.Delete(dir, false); return; }
            foreach (string f in Directory.GetFiles(dir))
            {
                try { File.SetAttributes(f, FileAttributes.Normal); } catch { }
                File.Delete(f);
            }
            foreach (string d in Directory.GetDirectories(dir)) DeleteDir(d);
            Directory.Delete(dir, false);
        }

        public static long DirSize(string dir)
        {
            if (!Directory.Exists(dir)) return 0;
            long n = 0;
            foreach (string f in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
            {
                try { n += new FileInfo(f).Length; } catch { }
            }
            return n;
        }

        public static string Mb(long bytes) { return (bytes / 1048576.0).ToString("0.0", CultureInfo.InvariantCulture) + " MB"; }

        /// <summary>Free bytes on the drive that holds path (-1 if it cannot be told).</summary>
        public static long FreeBytes(string path)
        {
            try
            {
                string full = Path.GetFullPath(path);
                string root = Path.GetPathRoot(full);
                if (string.IsNullOrEmpty(root) || root == "/")
                {
                    // Linux (tests): the longest mount point that holds the path
                    DriveInfo best = null;
                    foreach (DriveInfo d in DriveInfo.GetDrives())
                    {
                        try
                        {
                            if (d.IsReady && full.StartsWith(d.Name, StringComparison.Ordinal) && (best == null || d.Name.Length > best.Name.Length)) best = d;
                        }
                        catch { }
                    }
                    return best != null ? best.AvailableFreeSpace : -1;
                }
                return new DriveInfo(root).AvailableFreeSpace;
            }
            catch { return -1; }
        }

        public static string Rel(string root, string full)
        {
            string r = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
            string f = Path.GetFullPath(full);
            return f.StartsWith(r, StringComparison.OrdinalIgnoreCase) ? f.Substring(r.Length) : f;
        }

        /// <summary>a/b/c with any separator -> a path under root; refuses anything that would leave root.</summary>
        public static string Under(string root, string rel)
        {
            string norm = rel.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar).TrimStart(Path.DirectorySeparatorChar);
            string full = Path.GetFullPath(Path.Combine(root, norm));
            string r = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!full.StartsWith(r, StringComparison.OrdinalIgnoreCase)) throw new IOException("refused a path outside " + root + ": " + rel);
            return full;
        }
    }

    /// <summary>An error the player is shown as it is (a clear sentence and what to do).</summary>
    public sealed class DrbrException : Exception
    {
        public readonly string Code;
        public DrbrException(string code, string message) : base(message) { Code = code; }
        public DrbrException(string code, string message, Exception inner) : base(message, inner) { Code = code; }
    }
}
