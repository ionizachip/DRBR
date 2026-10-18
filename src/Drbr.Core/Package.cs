// DRBR - the release package. A DRBR release is ONE file, DRBR.zip, kept uncompressed ("stored"):
//   DRBR-Setup.exe                    the installer with the whole DRBR package appended (a zip of its own + its length + DRBRPAY1)
//   README.txt                        how to install
//   update/update-manifest.json       the release manifest (what payload.json says, with the release's address) ...
//   update/update-manifest.json.sig   ... and DRBR's signature over it (the last two entries)
// The launcher never needs the whole file to update: it reads the end of DRBR.zip (the zip's directory, the manifest and its
// signature are there), checks the signature, then downloads only the byte ranges of the files that changed - they lie
// uncompressed inside DRBR-Setup.exe's appended package, which lies uncompressed inside DRBR.zip. Every file is still checked
// against the signed manifest's SHA-256. A DRBR.zip that was compressed again by hand is still read: then it is downloaded
// whole and unpacked here.
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Text;

namespace Drbr
{
    /// <summary>Bytes that can be read at any offset: a local file, a part of another source, or a file on a web server that
    /// answers HTTP range requests.</summary>
    public interface IByteSource
    {
        long Length { get; }
        byte[] Read(long offset, int count);
    }

    public sealed class FileSource : IByteSource, IDisposable
    {
        readonly FileStream fs;
        public FileSource(string path) { fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 16); }
        public long Length { get { return fs.Length; } }
        public byte[] Read(long offset, int count)
        {
            if (offset < 0 || count < 0 || offset + count > fs.Length) throw new DrbrException("package_damaged", "The DRBR package ends early (it is incomplete or damaged).");
            byte[] b = new byte[count];
            fs.Seek(offset, SeekOrigin.Begin);
            int got = 0;
            while (got < count)
            {
                int n = fs.Read(b, got, count - got);
                if (n <= 0) throw new DrbrException("package_damaged", "The DRBR package ends early (it is incomplete or damaged).");
                got += n;
            }
            return b;
        }
        public void Dispose() { fs.Dispose(); }
    }

    /// <summary>A part of another source (offset 0 here is offset Base there).</summary>
    public sealed class SubSource : IByteSource
    {
        public readonly IByteSource Inner;
        public readonly long Base;
        readonly long len;
        public SubSource(IByteSource inner, long baseOffset, long length)
        {
            if (baseOffset < 0 || length < 0 || baseOffset + length > inner.Length) throw new DrbrException("package_damaged", "The DRBR package's layout is damaged (a part reaches past its end).");
            Inner = inner; Base = baseOffset; len = length;
        }
        public long Length { get { return len; } }
        public byte[] Read(long offset, int count)
        {
            if (offset < 0 || count < 0 || offset + count > len) throw new DrbrException("package_damaged", "The DRBR package's layout is damaged (a read past the end of a part).");
            return Inner.Read(Base + offset, count);
        }
        /// <summary>Where offset 0 of this part is in the outermost source.</summary>
        public long AbsoluteBase { get { SubSource s = Inner as SubSource; return Base + (s != null ? s.AbsoluteBase : 0); } }
    }

    /// <summary>A file on a web server read by HTTP range requests. GitHub answers a release download with a redirect to a
    /// short-lived signed address: that address is used while it works, and the original one asked again when it expires.</summary>
    public sealed class HttpRangeSource : IByteSource
    {
        public readonly string Url;
        public string FinalUrl { get; private set; }
        public long Length { get; private set; }
        public bool Ranges { get; private set; }     // the server answers range requests (else: download it whole)
        public long Requests;                         // how many requests (the tests look)

        public HttpRangeSource(string url) { Url = url; Resolve(); }

        void Resolve()
        {
            Ask(Url);
            // (a redirect that dropped the range: ask its target itself, once)
            if (!Ranges && FinalUrl != Url) Ask(FinalUrl);
        }

        void Ask(string url)
        {
            HttpWebRequest r = Http.Req(url);
            r.AddRange(0L, 0L);
            Requests++;
            try
            {
                using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
                {
                    FinalUrl = resp.ResponseUri != null ? resp.ResponseUri.ToString() : url;
                    if (resp.StatusCode == HttpStatusCode.PartialContent)
                    {
                        Length = TotalOf(resp.Headers["Content-Range"]);
                        Ranges = Length > 0;
                    }
                    else
                    {
                        // the whole file is on its way: only its size is wanted here
                        Length = resp.ContentLength;
                        Ranges = false;
                        r.Abort();
                    }
                }
            }
            catch (WebException e)
            {
                if (e.Status == WebExceptionStatus.RequestCanceled && Length > 0) return;   // (the abort above)
                HttpWebResponse er = e.Response as HttpWebResponse;
                if (er != null && er.StatusCode == HttpStatusCode.NotFound)
                    throw new DrbrException("no_release", "There is no DRBR release to update from yet (" + Url + " was not found).", e);
                throw new DrbrException("offline", "Could not reach the DRBR update server (" + e.Message + "). You can still play the installed version.", e);
            }
            if (Length <= 0) throw new DrbrException("offline", "The DRBR update server did not say how big the release is (" + Url + ").");
        }

        static long TotalOf(string contentRange)
        {
            // "bytes 0-0/123456"
            if (string.IsNullOrEmpty(contentRange)) return -1;
            int i = contentRange.LastIndexOf('/');
            long n;
            if (i < 0 || !long.TryParse(contentRange.Substring(i + 1).Trim(), out n)) return -1;
            return n;
        }

        /// <summary>The response for bytes [offset, offset + count) - its stream gives exactly those bytes.</summary>
        public HttpWebResponse Open(long offset, long count)
        {
            if (offset < 0 || count <= 0 || offset + count > Length) throw new DrbrException("package_damaged", "A read past the end of the DRBR release (" + Url + ").");
            for (int attempt = 0; ; attempt++)
            {
                HttpWebRequest r = Http.Req(FinalUrl);
                r.AddRange(offset, offset + count - 1);
                Requests++;
                try
                {
                    HttpWebResponse resp = (HttpWebResponse)r.GetResponse();
                    if (resp.StatusCode != HttpStatusCode.PartialContent || !StartsAt(resp.Headers["Content-Range"], offset))
                    {
                        resp.Close();
                        throw new DrbrException("no_ranges", "The DRBR update server stopped answering partial downloads.");
                    }
                    return resp;
                }
                catch (WebException e)
                {
                    HttpWebResponse er = e.Response as HttpWebResponse;
                    int code = er != null ? (int)er.StatusCode : 0;
                    // the signed address expired (GitHub's last a few minutes): ask the release's own address again, once
                    if (attempt == 0 && (code == 400 || code == 401 || code == 403 || code == 410))
                    {
                        Log.Info("The download address expired (HTTP " + code + "); asking " + Url + " again.");
                        Resolve();
                        continue;
                    }
                    throw new DrbrException("download", "The download from the DRBR release stopped (" + e.Message + "). Run the update again to continue where it stopped.", e);
                }
            }
        }

        static bool StartsAt(string contentRange, long offset)
        {
            // "bytes 100-199/1000"
            if (string.IsNullOrEmpty(contentRange)) return false;
            int sp = contentRange.IndexOf(' '), dash = contentRange.IndexOf('-');
            long s;
            return sp >= 0 && dash > sp && long.TryParse(contentRange.Substring(sp + 1, dash - sp - 1), out s) && s == offset;
        }

        // the last bigger read (the zip's end: its directory, the manifest and the signature are all in it)
        byte[] cache;
        long cacheAt;

        public byte[] Read(long offset, int count)
        {
            byte[] b = new byte[count];
            if (count == 0) return b;
            if (cache != null && offset >= cacheAt && offset + count <= cacheAt + cache.Length)
            {
                Buffer.BlockCopy(cache, (int)(offset - cacheAt), b, 0, count);
                return b;
            }
            using (HttpWebResponse resp = Open(offset, count))
            using (Stream s = resp.GetResponseStream())
            {
                int got = 0;
                while (got < count)
                {
                    int n = s.Read(b, got, count - got);
                    if (n <= 0) throw new DrbrException("download", "The DRBR update server sent less than asked for.");
                    got += n;
                }
            }
            if (count >= 4096)
            {
                cache = b;
                cacheAt = offset;
            }
            return b;
        }
    }

    public sealed class ZipEntryInfo
    {
        public string Name;
        public int Method;          // 0 stored, 8 deflated
        public long CompressedSize, Size, HeaderOffset;
        public uint Crc;
    }

    /// <summary>A zip's directory read from its end, and its entries read from where they are - no whole-file reads.</summary>
    public static class ZipDir
    {
        static uint U32(byte[] b, int i) { return (uint)(b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24)); }
        static int U16(byte[] b, int i) { return b[i] | (b[i + 1] << 8); }
        static long U64(byte[] b, int i) { return (long)U32(b, i) | ((long)U32(b, i + 4) << 32); }

        static DrbrException Bad(string what) { return new DrbrException("package_damaged", "The DRBR package is not a readable zip (" + what + "). Download DRBR.zip again."); }

        /// <summary>The entries, from the zip's end record and its directory. firstTail: how much of the end to read at first (the
        /// end record is in the last 22 bytes unless the zip has a comment; more is read when it is not found).</summary>
        public static List<ZipEntryInfo> Entries(IByteSource s, int firstTail = 22 + 65535 + 20)
        {
            long len = s.Length;
            if (len < 22) throw Bad("too short");
            int tailLen = (int)Math.Min(len, firstTail);
            long tailAt = len - tailLen;
            byte[] tail = s.Read(tailAt, tailLen);
            int e = FindEnd(tail);
            if (e < 0 && tailLen < Math.Min(len, 22 + 65535 + 20))
            {
                tailLen = (int)Math.Min(len, 22 + 65535 + 20);
                tailAt = len - tailLen;
                tail = s.Read(tailAt, tailLen);
                e = FindEnd(tail);
            }
            if (e < 0) throw Bad("no end record");
            long count = U16(tail, e + 10);
            long cdSize = U32(tail, e + 12);
            long cdOff = U32(tail, e + 16);
            if (count == 0xFFFF || cdSize == 0xFFFFFFFF || cdOff == 0xFFFFFFFF)
            {
                // ZIP64: its end record, found by the locator just before the normal one
                if (e < 20 || U32(tail, e - 20) != 0x07064b50) throw Bad("no ZIP64 locator");
                long e64 = U64(tail, e - 20 + 8);
                byte[] r64 = s.Read(e64, 56);
                if (U32(r64, 0) != 0x06064b50) throw Bad("no ZIP64 end record");
                count = U64(r64, 32);
                cdSize = U64(r64, 40);
                cdOff = U64(r64, 48);
            }
            if (cdOff < 0 || cdSize < 0 || cdOff + cdSize > len || cdSize > 64L * 1048576 || count > 100000) throw Bad("its directory is out of place");
            byte[] cd = (cdOff >= tailAt) ? Slice(tail, (int)(cdOff - tailAt), (int)cdSize) : s.Read(cdOff, (int)cdSize);
            List<ZipEntryInfo> list = new List<ZipEntryInfo>();
            int p = 0;
            for (long k = 0; k < count; k++)
            {
                if (p + 46 > cd.Length || U32(cd, p) != 0x02014b50) throw Bad("a damaged directory entry");
                int flags = U16(cd, p + 8);
                ZipEntryInfo z = new ZipEntryInfo
                {
                    Method = U16(cd, p + 10), Crc = U32(cd, p + 16), CompressedSize = U32(cd, p + 20), Size = U32(cd, p + 24), HeaderOffset = U32(cd, p + 42)
                };
                int n = U16(cd, p + 28), m = U16(cd, p + 30), c = U16(cd, p + 32);
                if (p + 46 + n + m + c > cd.Length) throw Bad("a damaged directory entry");
                z.Name = ((flags & 0x800) != 0 ? Encoding.UTF8 : Encoding.ASCII).GetString(cd, p + 46, n).Replace('\\', '/');
                // ZIP64 sizes and offset (in that order, only the ones that did not fit)
                int x = p + 46 + n, xe = x + m;
                while (x + 4 <= xe)
                {
                    int id = U16(cd, x), sz = U16(cd, x + 2);
                    if (id == 1)
                    {
                        int q = x + 4;
                        if (z.Size == 0xFFFFFFFF && q + 8 <= x + 4 + sz) { z.Size = U64(cd, q); q += 8; }
                        if (z.CompressedSize == 0xFFFFFFFF && q + 8 <= x + 4 + sz) { z.CompressedSize = U64(cd, q); q += 8; }
                        if (z.HeaderOffset == 0xFFFFFFFF && q + 8 <= x + 4 + sz) { z.HeaderOffset = U64(cd, q); q += 8; }
                    }
                    x += 4 + sz;
                }
                list.Add(z);
                p += 46 + n + m + c;
            }
            return list;
        }

        static int FindEnd(byte[] tail)
        {
            for (int i = tail.Length - 22; i >= 0; i--)
            {
                if (U32(tail, i) == 0x06054b50 && i + 22 + U16(tail, i + 20) == tail.Length) return i;
            }
            return -1;
        }

        static byte[] Slice(byte[] b, int at, int n)
        {
            if (at < 0 || n < 0 || at + n > b.Length) throw Bad("its directory is out of place");
            byte[] o = new byte[n];
            Buffer.BlockCopy(b, at, o, 0, n);
            return o;
        }

        /// <summary>Where the entry's (compressed) bytes start: after its local header.</summary>
        public static long DataOffset(IByteSource s, ZipEntryInfo z)
        {
            byte[] h = s.Read(z.HeaderOffset, 30);
            if (U32(h, 0) != 0x04034b50) throw Bad("a damaged local header for " + z.Name);
            long at = z.HeaderOffset + 30 + U16(h, 26) + U16(h, 28);
            if (at + z.CompressedSize > s.Length) throw Bad(z.Name + " reaches past the end");
            return at;
        }

        /// <summary>A small entry's contents (stored or deflated).</summary>
        public static byte[] ReadSmall(IByteSource s, ZipEntryInfo z, int max)
        {
            if (z.Size > max || z.CompressedSize > max) throw Bad(z.Name + " is bigger than it can be");
            byte[] raw = s.Read(DataOffset(s, z), (int)z.CompressedSize);
            if (z.Method == 0) return raw;
            if (z.Method != 8) throw Bad(z.Name + " uses a compression DRBR cannot read");
            using (DeflateStream d = new DeflateStream(new MemoryStream(raw), CompressionMode.Decompress))
            using (MemoryStream o = new MemoryStream())
            {
                byte[] buf = new byte[65536];
                int k;
                while ((k = d.Read(buf, 0, buf.Length)) > 0)
                {
                    o.Write(buf, 0, k);
                    if (o.Length > max) throw Bad(z.Name + " is bigger than it can be");
                }
                return o.ToArray();
            }
        }

        /// <summary>A whole entry written to a file (stored: copied; deflated: unpacked), from a local source.</summary>
        public static void Extract(FileSource s, string path, ZipEntryInfo z, string dst)
        {
            long at = DataOffset(s, z);
            using (FileStream src = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20))
            using (FileStream o = new FileStream(dst, FileMode.Create, FileAccess.Write))
            {
                src.Seek(at, SeekOrigin.Begin);
                Stream body = new Window(src, z.CompressedSize);
                if (z.Method == 8) body = new DeflateStream(body, CompressionMode.Decompress);
                else if (z.Method != 0) throw Bad(z.Name + " uses a compression DRBR cannot read");
                byte[] buf = new byte[1 << 20];
                int k;
                long total = 0;
                while ((k = body.Read(buf, 0, buf.Length)) > 0)
                {
                    o.Write(buf, 0, k);
                    total += k;
                    if (total > z.Size) throw Bad(z.Name + " is bigger than its directory says");
                }
            }
        }

        /// <summary>At most n bytes of a stream from where it is.</summary>
        sealed class Window : Stream
        {
            readonly Stream s; long left;
            public Window(Stream s, long n) { this.s = s; left = n; }
            public override int Read(byte[] b, int o, int c)
            {
                if (left <= 0) return 0;
                int k = s.Read(b, o, (int)Math.Min(c, left));
                left -= k;
                return k;
            }
            public override bool CanRead { get { return true; } }
            public override bool CanSeek { get { return false; } }
            public override bool CanWrite { get { return false; } }
            public override long Length { get { throw new NotSupportedException(); } }
            public override long Position { get { throw new NotSupportedException(); } set { throw new NotSupportedException(); } }
            public override void Flush() { }
            public override long Seek(long a, SeekOrigin b) { throw new NotSupportedException(); }
            public override void SetLength(long a) { throw new NotSupportedException(); }
            public override void Write(byte[] a, int b, int c) { throw new NotSupportedException(); }
        }
    }

    /// <summary>One file of the DRBR package inside a release: where its bytes are in DRBR.zip (they are stored as they are).</summary>
    public sealed class PackagedFile
    {
        public string Name;
        public long Offset;   // in the release file
        public long Size;
    }

    /// <summary>A DRBR release file (DRBR.zip) seen through any byte source.</summary>
    public sealed class DrbrPackage
    {
        public const string Magic = "DRBRPAY1";
        public readonly IByteSource Src;
        public readonly List<ZipEntryInfo> Entries;
        public ZipEntryInfo ManifestEntry, SignatureEntry, SetupEntry;

        DrbrPackage(IByteSource s, List<ZipEntryInfo> e) { Src = s; Entries = e; }

        static bool EndsWith(string name, string what)
        {
            return name.Equals(what, StringComparison.OrdinalIgnoreCase) || name.EndsWith("/" + what, StringComparison.OrdinalIgnoreCase);
        }

        public static DrbrPackage Open(IByteSource s)
        {
            DrbrPackage p = new DrbrPackage(s, ZipDir.Entries(s));
            foreach (ZipEntryInfo z in p.Entries)
            {
                if (EndsWith(z.Name, "update-manifest.json")) p.ManifestEntry = z;
                else if (EndsWith(z.Name, "update-manifest.json.sig")) p.SignatureEntry = z;
                else if (EndsWith(z.Name, "DRBR-Setup.exe")) p.SetupEntry = z;
            }
            if (p.ManifestEntry == null || p.SignatureEntry == null)
                throw new DrbrException("package_damaged", "This is not a DRBR release (DRBR.zip has no update-manifest.json and signature).");
            if (p.SetupEntry == null)
                throw new DrbrException("package_damaged", "This DRBR release has no DRBR-Setup.exe.");
            return p;
        }

        public byte[] ManifestBytes() { return ZipDir.ReadSmall(Src, ManifestEntry, 4 * 1048576); }
        public string SignatureText() { return Encoding.ASCII.GetString(ZipDir.ReadSmall(Src, SignatureEntry, 64 * 1024)).Trim(); }

        /// <summary>The DRBR package appended to a DRBR-Setup.exe (its last 16 bytes: the package's length, then DRBRPAY1).</summary>
        public static SubSource AppendedPayload(IByteSource exe)
        {
            if (exe.Length < 32) throw new DrbrException("package_damaged", "DRBR-Setup.exe in the release carries no DRBR package.");
            byte[] t = exe.Read(exe.Length - 16, 16);
            if (Encoding.ASCII.GetString(t, 8, 8) != Magic) throw new DrbrException("package_damaged", "DRBR-Setup.exe in the release carries no DRBR package.");
            long n = BitConverter.ToInt64(t, 0);
            if (n <= 0 || n > exe.Length - 16) throw new DrbrException("package_damaged", "DRBR-Setup.exe's package in the release is damaged.");
            return new SubSource(exe, exe.Length - 16 - n, n);
        }

        /// <summary>The named payload files and where their bytes are in the release file - only when DRBR-Setup.exe and those
        /// files are stored as they are (null when DRBR.zip was compressed again: then it is downloaded whole).</summary>
        public Dictionary<string, PackagedFile> PayloadFiles(IEnumerable<string> names)
        {
            if (SetupEntry.Method != 0) return null;
            SubSource exe = new SubSource(Src, ZipDir.DataOffset(Src, SetupEntry), SetupEntry.CompressedSize);
            SubSource inner = AppendedPayload(exe);
            Dictionary<string, ZipEntryInfo> all = new Dictionary<string, ZipEntryInfo>(StringComparer.OrdinalIgnoreCase);
            foreach (ZipEntryInfo z in ZipDir.Entries(inner, 8192)) all[z.Name] = z;
            Dictionary<string, PackagedFile> d = new Dictionary<string, PackagedFile>(StringComparer.OrdinalIgnoreCase);
            foreach (string n in names)
            {
                ZipEntryInfo z;
                if (!all.TryGetValue(n, out z)) throw new DrbrException("package_damaged", "The DRBR release's package has no " + n + ".");
                if (z.Method != 0) return null;
                d[n] = new PackagedFile { Name = n, Offset = inner.AbsoluteBase + ZipDir.DataOffset(inner, z), Size = z.Size };
            }
            return d;
        }

        /// <summary>From a release file on disk: the named payload files written to dir (whatever DRBR.zip's compression).
        /// They are checked by the caller.</summary>
        public static void ExtractPayload(string zipPath, IEnumerable<string> names, string dir, string tempDir)
        {
            using (FileSource fs = new FileSource(zipPath))
            {
                DrbrPackage p = Open(fs);
                string exePath = null;
                IByteSource exe;
                FileSource exeSrc = null;
                try
                {
                    if (p.SetupEntry.Method == 0) exe = new SubSource(fs, ZipDir.DataOffset(fs, p.SetupEntry), p.SetupEntry.CompressedSize);
                    else
                    {
                        exePath = Path.Combine(tempDir, "DRBR-Setup.exe.unpacked");
                        ZipDir.Extract(fs, zipPath, p.SetupEntry, exePath);
                        exe = exeSrc = new FileSource(exePath);
                    }
                    SubSource inner = AppendedPayload(exe);
                    Dictionary<string, ZipEntryInfo> all = new Dictionary<string, ZipEntryInfo>(StringComparer.OrdinalIgnoreCase);
                    foreach (ZipEntryInfo z in ZipDir.Entries(inner)) all[z.Name] = z;
                    foreach (string n in names)
                    {
                        ZipEntryInfo z;
                        if (!all.TryGetValue(n, out z)) throw new DrbrException("package_damaged", "The DRBR release's package has no " + n + ".");
                        if (z.Method != 0) throw new DrbrException("package_damaged", "The DRBR release's package is not one DRBR made (" + n + " is compressed).");
                        long at = inner.AbsoluteBase + ZipDir.DataOffset(inner, z);
                        string src = exeSrc != null ? exePath : zipPath;
                        using (FileStream i = new FileStream(src, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20))
                        using (FileStream o = new FileStream(Path.Combine(dir, n), FileMode.Create, FileAccess.Write))
                        {
                            i.Seek(at, SeekOrigin.Begin);
                            byte[] buf = new byte[1 << 20];
                            long left = z.Size;
                            while (left > 0)
                            {
                                int k = i.Read(buf, 0, (int)Math.Min(buf.Length, left));
                                if (k <= 0) throw new DrbrException("package_damaged", "The DRBR release ends early.");
                                o.Write(buf, 0, k);
                                left -= k;
                            }
                        }
                    }
                }
                finally
                {
                    if (exeSrc != null) exeSrc.Dispose();
                    if (exePath != null) { try { File.Delete(exePath); } catch { } }
                }
            }
        }
    }
}
