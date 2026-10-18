// DRBR - the release manifest (payload.json inside a payload, update-manifest.json on GitHub) and its signature.
using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace Drbr
{
    public sealed class PayloadFile
    {
        public string File;      // its name in the payload / the release (no spaces)
        public string Kind;      // copy | music_zip | kfsongs_zip | tool | app | template | patch | patch_incremental | doc
        public string Dest;      // where it goes, relative to the DRBR root (copy / tool / app / doc)
        public long Size;
        public string Sha256;
        public string Version;   // apps: their version
        public string FromSha256;  // patch_incremental: the DRBR data.win it applies to
    }

    public sealed class MusicFile { public string Rel; public string Sha256; }

    public sealed class SaveProfileInfo
    {
        public int SchemaVersion = 1;
        public string Profile = "drbr_default";
        public int TemplateVersion = 1;
        public int MigrationVersion = 1;
        public string TemplateFile = "start_filech3";
        public long TemplateSize;
        public string TemplateSha256;
        public string TemplateSha1;
        public string StartingLocation = "room_dw_snow_zone";
        public int StartingRoomId = 30108;
        public int StartingPlot = 320;
    }

    public sealed class Manifest
    {
        public int Schema = 1;
        public string Product = "DRBR";
        public string Version = "0.0.0";
        public string ModBuild = "";
        public int Protocol;
        public string LauncherVersion = "0.0.0";
        public string MinLauncherVersion = "0.0.0";
        public string Released = "";
        public string Notes = "";
        public string BaseUrl = "";
        public string PackageName = "DRBR.zip";   // the release's one file (DRBR.zip): the files are read from inside it
        public readonly List<SupportedBuild> SupportedGameBuilds = new List<SupportedBuild>();
        public long DrbrDataWinSize;
        public string DrbrDataWinSha256;
        public readonly List<PayloadFile> Files = new List<PayloadFile>();
        public readonly List<MusicFile> Music = new List<MusicFile>();
        public SaveProfileInfo SaveProfile = new SaveProfileInfo();
        public JsonObject Raw;

        public PayloadFile FullPatch { get { return Files.Find(f => f.Kind == "patch"); } }
        public PayloadFile Template { get { return Files.Find(f => f.Kind == "template"); } }
        public IEnumerable<PayloadFile> OfKind(string k) { return Files.FindAll(f => f.Kind == k); }
        public PayloadFile Incremental(string fromSha) { return Files.Find(f => f.Kind == "patch_incremental" && Hash.Same(f.FromSha256, fromSha)); }

        public static Manifest Parse(string json)
        {
            JsonObject o = Json.ParseObject(json);
            Manifest m = new Manifest { Raw = o };
            m.Schema = (int)o.Long("schema", 1);
            if (m.Schema != 1) throw new DrbrException("manifest_schema", "This release needs a newer DRBR Launcher (manifest schema " + m.Schema + ").");
            m.Product = o.Str("product", "DRBR");
            if (m.Product != "DRBR") throw new DrbrException("manifest_product", "This is not a DRBR release manifest.");
            m.Version = o.Str("version", "0.0.0");
            m.ModBuild = o.Str("mod_build", "");
            m.Protocol = (int)o.Long("protocol", 0);
            m.LauncherVersion = o.Str("launcher_version", "0.0.0");
            m.MinLauncherVersion = o.Str("min_launcher_version", "0.0.0");
            m.Released = o.Str("released", "");
            m.Notes = o.Str("notes", "");
            m.BaseUrl = o.Str("base_url", "");
            m.PackageName = o.Str("package", "DRBR.zip");
            if (m.PackageName.Length == 0 || m.PackageName.IndexOfAny(new[] { '/', '\\', ':' }) >= 0 || m.PackageName.Contains(".."))
                throw new DrbrException("manifest_file", "The release manifest names a package DRBR refuses: " + m.PackageName);
            foreach (object x in o.Arr("supported_game_builds"))
            {
                JsonObject b = x as JsonObject;
                if (b == null) continue;
                m.SupportedGameBuilds.Add(new SupportedBuild { Name = b.Str("name", "DELTARUNE"), Size = b.Long("size"), Sha256 = b.Str("sha256", "") });
            }
            JsonObject dw = o.Obj("drbr_data_win");
            if (dw != null) { m.DrbrDataWinSize = dw.Long("size"); m.DrbrDataWinSha256 = dw.Str("sha256", ""); }
            foreach (object x in o.Arr("files"))
            {
                JsonObject f = x as JsonObject;
                if (f == null) continue;
                PayloadFile pf = new PayloadFile
                {
                    File = f.Str("file", ""), Kind = f.Str("kind", "copy"), Dest = f.Str("dest", ""), Size = f.Long("size"),
                    Sha256 = f.Str("sha256", ""), Version = f.Str("version", ""), FromSha256 = f.Str("from_sha256", "")
                };
                if (pf.File.Length == 0 || pf.File.IndexOfAny(new[] { '/', '\\', ':' }) >= 0 || pf.File.Contains(".."))
                    throw new DrbrException("manifest_file", "The release manifest names a file DRBR refuses: " + pf.File);
                if (!Hash.IsSha256(pf.Sha256)) throw new DrbrException("manifest_hash", "The release manifest has no valid checksum for " + pf.File + ".");
                m.Files.Add(pf);
            }
            foreach (object x in o.Arr("music"))
            {
                JsonObject f = x as JsonObject;
                if (f == null) continue;
                string rel = f.Str("rel", "");
                if (rel.Length == 0 || rel.Contains("..") || rel.Contains(":") || rel.StartsWith("/") || rel.StartsWith("\\")) continue;
                m.Music.Add(new MusicFile { Rel = rel, Sha256 = f.Str("sha256", "") });
            }
            JsonObject sp = o.Obj("save_profile");
            if (sp != null)
            {
                SaveProfileInfo s = m.SaveProfile;
                s.SchemaVersion = (int)sp.Long("schema_version", 1);
                s.Profile = sp.Str("profile", "drbr_default");
                s.TemplateVersion = (int)sp.Long("save_template_version", 1);
                s.MigrationVersion = (int)sp.Long("migration_version", 1);
                s.StartingLocation = sp.Str("starting_location", "room_dw_snow_zone");
                s.StartingRoomId = (int)sp.Long("starting_room_id", 30108);
                s.StartingPlot = (int)sp.Long("starting_plot", 320);
                JsonObject t = sp.Obj("template");
                if (t != null)
                {
                    s.TemplateFile = t.Str("file", "start_filech3");
                    s.TemplateSize = t.Long("size");
                    s.TemplateSha256 = t.Str("sha256", "");
                    s.TemplateSha1 = t.Str("sha1", "");
                }
            }
            if (!Hash.IsSha256(m.DrbrDataWinSha256)) throw new DrbrException("manifest_datawin", "The release manifest has no checksum for DRBR's data.win.");
            if (m.FullPatch == null) throw new DrbrException("manifest_patch", "The release manifest lists no game patch.");
            if (m.SupportedGameBuilds.Count == 0) throw new DrbrException("manifest_builds", "The release manifest lists no supported DELTARUNE version.");
            return m;
        }

        public static Manifest Load(string path) { return Parse(File.ReadAllText(path, Encoding.UTF8)); }
    }

    /// <summary>RSA (PKCS#1 v1.5, SHA-256) signatures over the exact bytes of update-manifest.json. Only the public key is in DRBR.</summary>
    public static class Signature
    {
        public static bool Verify(byte[] data, string signatureBase64, string modulusB64 = null, string exponentB64 = null)
        {
            if (string.IsNullOrEmpty(signatureBase64)) return false;
            byte[] sig;
            try { sig = Convert.FromBase64String(signatureBase64.Trim()); }
            catch { return false; }
            RSAParameters p = new RSAParameters
            {
                Modulus = Convert.FromBase64String(modulusB64 ?? BuildInfo.PublicKeyModulus),
                Exponent = Convert.FromBase64String(exponentB64 ?? BuildInfo.PublicKeyExponent)
            };
            foreach (Func<RSA> make in Makers())
            {
                RSA rsa = null;
                try
                {
                    rsa = make();
                    rsa.ImportParameters(p);
                    return rsa.VerifyData(data, sig, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
                }
                catch (PlatformNotSupportedException) { }
                catch (NotImplementedException) { }
                catch (CryptographicException) { return false; }
                catch (TypeLoadException) { }
                finally { if (rsa != null) rsa.Dispose(); }
            }
            return false;
        }

        static IEnumerable<Func<RSA>> Makers()
        {
            if (Environment.OSVersion.Platform == PlatformID.Win32NT) yield return MakeCng;
            yield return () => RSA.Create();
            yield return () => new RSACryptoServiceProvider();
        }

        static RSA MakeCng() { return new RSACng(); }
    }
}
