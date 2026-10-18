// DRBR - update checks and downloads from GitHub Releases. The manifest is accepted only with a valid signature from
// DRBR's release key (its public half is built into the launcher); every file is accepted only with the checksum the
// signed manifest gives. Nothing a multiplayer host or room says can choose what is downloaded.
using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;

namespace Drbr
{
    public sealed class UpdateInfo
    {
        public Manifest Manifest;
        public byte[] ManifestBytes;
        public string Installed;
        public bool Available;
        public bool LauncherNewer;
        public bool LauncherTooOld;      // this launcher is older than the release's min_launcher_version
        public bool ProtocolChanged;     // online play needs the update (the other players will have it)
        public string Url;
        public string PackageUrl;        // a release that is one DRBR.zip: the files are downloaded from inside it
    }

    public sealed class UpdateEngine
    {
        public readonly DrbrPaths P;
        public string ManifestUrl;
        public UpdateEngine(DrbrPaths p, string manifestUrl) { P = p; ManifestUrl = manifestUrl; }

        static UpdateEngine()
        {
            try { ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12; } catch { }
        }

        public static string DefaultUrl(Settings s)
        {
            string env = Environment.GetEnvironmentVariable("DRBR_UPDATE_URL");
            if (!string.IsNullOrEmpty(env)) return env;
            if (s != null && !string.IsNullOrEmpty(s.UpdateUrlOverride)) return s.UpdateUrlOverride;
            return BuildInfo.UpdatesConfigured ? BuildInfo.UpdateManifestUrl : null;
        }

        /// <summary>A release that is one file (DRBR.zip): the update address names a .zip.</summary>
        public static bool IsPackageUrl(string url)
        {
            if (string.IsNullOrEmpty(url)) return false;
            string u = url.Split('?')[0];
            return u.EndsWith(".zip", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>Reads the release's manifest and its signature (from the end of DRBR.zip, or update-manifest.json and its
        /// .sig), checks the signature, compares versions.</summary>
        public UpdateInfo Check(string installedVersion, int installedProtocol)
        {
            if (string.IsNullOrEmpty(ManifestUrl)) throw new DrbrException("updates_off", "Update checks are not set up in this DRBR build (no GitHub repository yet).");
            byte[] mb;
            string sig;
            string packageUrl = null;
            if (IsPackageUrl(ManifestUrl))
            {
                // DRBR.zip: only its end is read (the zip's directory, the manifest and the signature are the last entries)
                HttpRangeSource src = new HttpRangeSource(ManifestUrl);
                DrbrPackage pkg;
                if (src.Ranges) pkg = DrbrPackage.Open(src);
                else
                {
                    string whole = Path.Combine(P.StagingDir, "check-" + Guid.NewGuid().ToString("N") + ".zip");
                    Directory.CreateDirectory(P.StagingDir);
                    try
                    {
                        Http.DownloadWhole(ManifestUrl, whole, src.Length, null);
                        using (FileSource fs = new FileSource(whole))
                        {
                            DrbrPackage p2 = DrbrPackage.Open(fs);
                            mb = p2.ManifestBytes();
                            sig = p2.SignatureText();
                        }
                    }
                    finally { try { File.Delete(whole); } catch { } }
                    pkg = null;
                    goto verify;
                }
                mb = pkg.ManifestBytes();
                sig = pkg.SignatureText();
            }
            else
            {
                mb = Http.GetBytes(ManifestUrl, 4 * 1048576);
                sig = Encoding.ASCII.GetString(Http.GetBytes(ManifestUrl + ".sig", 64 * 1024));
            }
        verify:
            if (!Signature.Verify(mb, sig))
            {
                Log.Error("Update manifest REJECTED: its signature is not DRBR's (" + ManifestUrl + ").");
                throw new DrbrException("bad_signature", "The update information is not signed by DRBR's release key, so it was refused. Nothing was downloaded or changed.");
            }
            Manifest m = Manifest.Parse(Encoding.UTF8.GetString(mb));
            if (IsPackageUrl(ManifestUrl))
            {
                // the files come from this exact release's DRBR.zip (its own address - not "latest", which could move on meanwhile)
                string b = m.BaseUrl;
                packageUrl = string.IsNullOrEmpty(b) ? ManifestUrl : (b.EndsWith("/") ? b : b + "/") + Uri.EscapeDataString(m.PackageName);
            }
            UpdateInfo u = new UpdateInfo { Manifest = m, ManifestBytes = mb, Installed = installedVersion, Url = ManifestUrl, PackageUrl = packageUrl };
            u.Available = installedVersion == null || Ver.IsNewer(m.Version, installedVersion);
            u.LauncherNewer = Ver.IsNewer(m.LauncherVersion, BuildInfo.Version);
            u.LauncherTooOld = Ver.IsNewer(m.MinLauncherVersion, BuildInfo.Version);
            u.ProtocolChanged = installedProtocol != 0 && m.Protocol != installedProtocol;
            Log.Info("Update check: installed " + (installedVersion ?? "none") + ", available " + m.Version + (u.Available ? " (newer)" : "") + ", protocol " + m.Protocol);
            return u;
        }

        /// <summary>Builds the new release's full payload in staging: every file whose checksum the installed package already
        /// has is copied from it; the rest is downloaded (resumed if a download was cut off) and checked. Returns the folder.</summary>
        public string Download(UpdateInfo u, Action<string, int> progress)
        {
            Manifest m = u.Manifest;
            string baseUrl = m.BaseUrl;
            if (string.IsNullOrEmpty(baseUrl))
            {
                int i = ManifestUrl.LastIndexOf('/');
                baseUrl = ManifestUrl.Substring(0, i + 1);
            }
            if (!baseUrl.EndsWith("/")) baseUrl += "/";
            string dir = Path.Combine(P.StagingDir, "download-" + m.Version);
            Directory.CreateDirectory(dir);
            // the installed package's files by checksum (what does not need downloading)
            Dictionary<string, string> have = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            try
            {
                if (File.Exists(Path.Combine(P.PayloadDir, "payload.json")))
                {
                    Manifest old = Manifest.Load(Path.Combine(P.PayloadDir, "payload.json"));
                    foreach (PayloadFile f in old.Files)
                    {
                        string fp = Path.Combine(P.PayloadDir, f.File);
                        if (File.Exists(fp) && new FileInfo(fp).Length == f.Size) have[f.Sha256] = fp;
                    }
                }
            }
            catch (Exception e) { Log.Warn("Installed package unreadable (everything is downloaded): " + e.Message); }

            // an incremental game patch from the installed data.win, when the release has one: then the full patch can wait
            long total = 0, done = 0;
            List<PayloadFile> todo = new List<PayloadFile>();
            foreach (PayloadFile f in m.Files)
            {
                if (f.Kind == "patch_incremental") continue;
                string dst = Path.Combine(dir, f.File);
                if (File.Exists(dst) && new FileInfo(dst).Length == f.Size && Hash.Same(Hash.Sha256File(dst), f.Sha256)) continue;
                string src;
                if (have.TryGetValue(f.Sha256, out src)) { Fs.CopyVerified(src, dst, f.Sha256); continue; }
                todo.Add(f);
                total += f.Size;
            }
            if (u.PackageUrl != null && todo.Count > 0)
                DownloadFromPackage(u, todo, dir, total, progress);
            else
            {
                foreach (PayloadFile f in todo)
                {
                    string dst = Path.Combine(dir, f.File);
                    long before = done;
                    Http.Download(baseUrl + Uri.EscapeDataString(f.File), dst, f.Size, f.Sha256, (got) =>
                    {
                        if (progress != null && total > 0) progress("Downloading " + f.File + " (" + Fs.Mb(before + got) + " of " + Fs.Mb(total) + ")", (int)(100 * (before + got) / total));
                    });
                    done += f.Size;
                }
            }
            // the signed manifest is the new package's payload.json (the install checks every file against it again)
            File.WriteAllBytes(Path.Combine(dir, "payload.json"), u.ManifestBytes);
            Log.Info("Update " + m.Version + ": " + todo.Count + " file(s) downloaded (" + Fs.Mb(total) + "), the rest reused.");
            return dir;
        }

        /// <summary>The changed files, from inside the release's DRBR.zip: just their bytes (HTTP ranges, resumed when cut off);
        /// a DRBR.zip that was compressed again (or a server without ranges) is downloaded whole and unpacked here instead.
        /// Every file is checked against the signed manifest either way.</summary>
        void DownloadFromPackage(UpdateInfo u, List<PayloadFile> todo, string dir, long total, Action<string, int> progress)
        {
            HttpRangeSource src;
            try { src = new HttpRangeSource(u.PackageUrl); }
            catch (DrbrException e) when (e.Code == "no_release" && !string.IsNullOrEmpty(u.Url) && u.Url != u.PackageUrl)
            {
                // DRBR 1.0.2: the release's own address (its tag, named in the signed manifest) is not there - a release put up
                // under another tag than its version (v1.01 for 1.0.1 did that): the DRBR.zip the check read is used instead. Its
                // manifest has to be the one that was checked (just below), so nothing else can come in this way.
                Log.Warn("The release's own address " + u.PackageUrl + " was not found (its tag is not v" + u.Manifest.Version + "?) - reading the DRBR.zip the check read: " + u.Url);
                u.PackageUrl = u.Url;
                src = new HttpRangeSource(u.PackageUrl);
            }
            Dictionary<string, PackagedFile> where = null;
            if (src.Ranges)
            {
                DrbrPackage pkg = DrbrPackage.Open(src);
                // (it has to be the release whose manifest was checked)
                if (!Hash.Same(Hash.Sha256Bytes(pkg.ManifestBytes()), Hash.Sha256Bytes(u.ManifestBytes)))
                    throw new DrbrException("bad_download", "The DRBR release changed while it was being read (its manifest differs). Check for updates again.");
                where = pkg.PayloadFiles(todo.ConvertAll(f => f.File));
            }
            if (where != null)
            {
                long done = 0;
                foreach (PayloadFile f in todo)
                {
                    PackagedFile pf = where[f.File];
                    if (pf.Size != f.Size) throw new DrbrException("bad_download", "The DRBR release's " + f.File + " is not the size its manifest says. Nothing was changed.");
                    long before = done;
                    Http.DownloadRange(src, pf.Offset, Path.Combine(dir, f.File), f.Size, f.Sha256, (got) =>
                    {
                        if (progress != null && total > 0) progress("Downloading " + f.File + " (" + Fs.Mb(before + got) + " of " + Fs.Mb(total) + ")", (int)(100 * (before + got) / total));
                    });
                    done += f.Size;
                }
                Log.Info("Update: " + todo.Count + " file(s) read from inside " + u.PackageUrl + " (" + src.Requests + " requests).");
                return;
            }
            // the whole release, then its files from it
            Log.Info("The release " + u.PackageUrl + " cannot be read in parts (" + (src.Ranges ? "it was compressed again" : "no HTTP ranges") + "): downloading it whole.");
            string whole = Path.Combine(dir, u.Manifest.PackageName + ".whole");
            Http.DownloadWhole(u.PackageUrl, whole, src.Length, (got) =>
            {
                if (progress != null) progress("Downloading " + u.Manifest.PackageName + " (" + Fs.Mb(got) + " of " + Fs.Mb(src.Length) + ")", (int)(100 * got / Math.Max(1, src.Length)));
            });
            try
            {
                using (FileSource fs = new FileSource(whole))
                {
                    DrbrPackage pkg = DrbrPackage.Open(fs);
                    if (!Hash.Same(Hash.Sha256Bytes(pkg.ManifestBytes()), Hash.Sha256Bytes(u.ManifestBytes)))
                        throw new DrbrException("bad_download", "The DRBR release changed while it was being read (its manifest differs). Check for updates again.");
                }
                DrbrPackage.ExtractPayload(whole, todo.ConvertAll(f => f.File), dir, dir);
            }
            finally { try { File.Delete(whole); } catch { } }
            foreach (PayloadFile f in todo)
            {
                string p = Path.Combine(dir, f.File);
                if (new FileInfo(p).Length != f.Size || !Hash.Same(Hash.Sha256File(p), f.Sha256))
                {
                    File.Delete(p);
                    throw new DrbrException("bad_download", "The download of " + f.File + " was damaged and was refused. Nothing was changed.");
                }
            }
        }
    }

    public static class Http
    {
        public static int TimeoutMs = 60000;

        internal static HttpWebRequest Req(string url)
        {
            HttpWebRequest r = (HttpWebRequest)WebRequest.Create(url);
            r.UserAgent = "DRBR-Launcher/" + BuildInfo.Version;
            r.AllowAutoRedirect = true;
            r.Timeout = TimeoutMs;
            r.ReadWriteTimeout = TimeoutMs;
            return r;
        }

        public static byte[] GetBytes(string url, int max)
        {
            try
            {
                using (HttpWebResponse resp = (HttpWebResponse)Req(url).GetResponse())
                using (Stream s = resp.GetResponseStream())
                using (MemoryStream ms = new MemoryStream())
                {
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = s.Read(buf, 0, buf.Length)) > 0)
                    {
                        ms.Write(buf, 0, n);
                        if (ms.Length > max) throw new DrbrException("too_big", "The server sent more than expected for " + url);
                    }
                    return ms.ToArray();
                }
            }
            catch (WebException e)
            {
                throw new DrbrException("offline", "Could not reach the DRBR update server (" + e.Message + "). You can still play the installed version.", e);
            }
        }

        /// <summary>Bytes [offset, offset + size) of a release file to dst (via dst.part, resumed when one is there), then checks
        /// size and SHA-256 - a file that fails is downloaded once more, then refused.</summary>
        public static void DownloadRange(HttpRangeSource src, long offset, string dst, long size, string sha, Action<long> progress)
        {
            string part = dst + ".part";
            for (int attempt = 0; attempt < 2; attempt++)
            {
                long have = File.Exists(part) ? new FileInfo(part).Length : 0;
                if (have > size) { File.Delete(part); have = 0; }
                if (have < size)
                {
                    try
                    {
                        using (HttpWebResponse resp = src.Open(offset + have, size - have))
                        using (Stream s = resp.GetResponseStream())
                        using (FileStream fs = new FileStream(part, have > 0 ? FileMode.Append : FileMode.Create, FileAccess.Write))
                        {
                            byte[] buf = new byte[1 << 20];
                            int n;
                            long got = have;
                            while ((n = s.Read(buf, 0, buf.Length)) > 0)
                            {
                                if (got + n > size) throw new DrbrException("too_big", "The server sent more than expected for " + Path.GetFileName(dst));
                                fs.Write(buf, 0, n);
                                got += n;
                                if (progress != null) progress(got);
                            }
                        }
                    }
                    catch (IOException e)
                    {
                        throw new DrbrException("download", "The download of " + Path.GetFileName(dst) + " stopped (" + e.Message + "). Run the update again to continue where it stopped.", e);
                    }
                }
                if (new FileInfo(part).Length == size && Hash.Same(Hash.Sha256File(part), sha))
                {
                    if (File.Exists(dst)) File.Delete(dst);
                    File.Move(part, dst);
                    return;
                }
                Log.Warn("Downloaded " + Path.GetFileName(dst) + " failed its checksum; downloading it again.");
                File.Delete(part);
            }
            throw new DrbrException("bad_download", "The download of " + Path.GetFileName(dst) + " was damaged twice and was refused. Nothing was changed.");
        }

        /// <summary>A whole file of a known size to dst (via dst.part, resumed when one is there). No checksum here: what is
        /// inside it is checked.</summary>
        public static void DownloadWhole(string url, string dst, long size, Action<long> progress)
        {
            string part = dst + ".part";
            long have = File.Exists(part) ? new FileInfo(part).Length : 0;
            if (have > size) { File.Delete(part); have = 0; }
            if (have < size)
            {
                HttpWebRequest r = Req(url);
                if (have > 0) r.AddRange(have);
                try
                {
                    using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
                    {
                        bool append = have > 0 && resp.StatusCode == HttpStatusCode.PartialContent;
                        if (!append) have = 0;
                        using (Stream s = resp.GetResponseStream())
                        using (FileStream fs = new FileStream(part, append ? FileMode.Append : FileMode.Create, FileAccess.Write))
                        {
                            byte[] buf = new byte[1 << 20];
                            int n;
                            long got = have;
                            while ((n = s.Read(buf, 0, buf.Length)) > 0)
                            {
                                if (got + n > size) throw new DrbrException("too_big", "The server sent more than expected for " + url);
                                fs.Write(buf, 0, n);
                                got += n;
                                if (progress != null) progress(got);
                            }
                        }
                    }
                }
                catch (WebException e)
                {
                    throw new DrbrException("download", "The download of " + Path.GetFileName(dst) + " stopped (" + e.Message + "). Run the update again to continue where it stopped.", e);
                }
            }
            if (new FileInfo(part).Length != size) throw new DrbrException("download", "The download of " + url + " is incomplete. Run the update again to continue where it stopped.");
            if (File.Exists(dst)) File.Delete(dst);
            File.Move(part, dst);
        }

        /// <summary>Downloads to dst (via dst.part, resumed with an HTTP Range when a .part is there), then checks size and
        /// SHA-256. A file that fails is deleted - a damaged download is never used.</summary>
        public static void Download(string url, string dst, long size, string sha, Action<long> progress)
        {
            string part = dst + ".part";
            for (int attempt = 0; attempt < 2; attempt++)
            {
                long have = File.Exists(part) ? new FileInfo(part).Length : 0;
                if (have > size) { File.Delete(part); have = 0; }
                if (have < size)
                {
                    HttpWebRequest r = Req(url);
                    if (have > 0) r.AddRange(have);
                    try
                    {
                        using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
                        {
                            bool append = have > 0 && resp.StatusCode == HttpStatusCode.PartialContent;
                            if (!append) have = 0;
                            using (Stream s = resp.GetResponseStream())
                            using (FileStream fs = new FileStream(part, append ? FileMode.Append : FileMode.Create, FileAccess.Write))
                            {
                                byte[] buf = new byte[1 << 20];
                                int n;
                                long got = have;
                                while ((n = s.Read(buf, 0, buf.Length)) > 0)
                                {
                                    fs.Write(buf, 0, n);
                                    got += n;
                                    if (got > size) throw new DrbrException("too_big", "The server sent more than expected for " + url);
                                    if (progress != null) progress(got);
                                }
                            }
                        }
                    }
                    catch (WebException e)
                    {
                        throw new DrbrException("download", "The download of " + Path.GetFileName(dst) + " stopped (" + e.Message + "). Run the update again to continue where it stopped.", e);
                    }
                }
                if (new FileInfo(part).Length == size && Hash.Same(Hash.Sha256File(part), sha))
                {
                    if (File.Exists(dst)) File.Delete(dst);
                    File.Move(part, dst);
                    return;
                }
                Log.Warn("Downloaded " + Path.GetFileName(dst) + " failed its checksum; downloading it again.");
                File.Delete(part);
            }
            throw new DrbrException("bad_download", "The download of " + Path.GetFileName(dst) + " was damaged twice and was refused. Nothing was changed.");
        }
    }
}
