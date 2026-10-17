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

        /// <summary>Downloads update-manifest.json and its .sig, checks the signature, compares versions.</summary>
        public UpdateInfo Check(string installedVersion, int installedProtocol)
        {
            if (string.IsNullOrEmpty(ManifestUrl)) throw new DrbrException("updates_off", "Update checks are not set up in this DRBR build (no GitHub repository yet).");
            byte[] mb = Http.GetBytes(ManifestUrl, 4 * 1048576);
            byte[] sb = Http.GetBytes(ManifestUrl + ".sig", 64 * 1024);
            if (!Signature.Verify(mb, Encoding.ASCII.GetString(sb)))
            {
                Log.Error("Update manifest REJECTED: its signature is not DRBR's (" + ManifestUrl + ").");
                throw new DrbrException("bad_signature", "The update information is not signed by DRBR's release key, so it was refused. Nothing was downloaded or changed.");
            }
            Manifest m = Manifest.Parse(Encoding.UTF8.GetString(mb));
            UpdateInfo u = new UpdateInfo { Manifest = m, ManifestBytes = mb, Installed = installedVersion, Url = ManifestUrl };
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
            // the signed manifest is the new package's payload.json (the install checks every file against it again)
            File.WriteAllBytes(Path.Combine(dir, "payload.json"), u.ManifestBytes);
            Log.Info("Update " + m.Version + ": " + todo.Count + " file(s) downloaded (" + Fs.Mb(total) + "), the rest reused.");
            return dir;
        }
    }

    public static class Http
    {
        public static int TimeoutMs = 60000;

        static HttpWebRequest Req(string url)
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
