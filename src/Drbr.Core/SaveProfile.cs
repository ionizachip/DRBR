// DRBR - the save profile: the provided starting save (an immutable template next to DRBR's data.win), the profile
// config the game reads, the live DRBR saves (%LOCALAPPDATA%\DELTARUNE\drbr_profile), restoring the start, migrations,
// and a check that the player's own DELTARUNE saves were not touched.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

namespace Drbr
{
    public static class SaveProfile
    {
        public const string ModeTemplate = "template";
        public const string ModeContinue = "continue";

        /// <summary>The text of chapter3_windows\drbr_data\drbr_profile.cfg (the game reads it with file_text, line by line).</summary>
        public static string CfgText(SaveProfileInfo sp, string startMode)
        {
            if (startMode != ModeContinue) startMode = ModeTemplate;
            StringBuilder b = new StringBuilder();
            b.Append("# DRBR save profile - written by DRBR Launcher, read by the game when it starts. Do not edit by hand.\r\n");
            b.Append("# start_mode: template = every launch starts from the provided starting save (the room before the Roaring Knight);\r\n");
            b.Append("#             continue = the last DRBR save, if it is a valid Chapter 3 save (else the starting save).\r\n");
            b.Append("schema_version=").Append(sp.SchemaVersion).Append("\r\n");
            b.Append("profile=").Append(sp.Profile).Append("\r\n");
            b.Append("starting_location=").Append(sp.StartingLocation).Append("\r\n");
            b.Append("starting_room_id=").Append(sp.StartingRoomId).Append("\r\n");
            b.Append("starting_plot=").Append(sp.StartingPlot).Append("\r\n");
            b.Append("save_template_version=").Append(sp.TemplateVersion).Append("\r\n");
            b.Append("save_template_sha256=").Append(sp.TemplateSha256).Append("\r\n");
            b.Append("start_mode=").Append(startMode).Append("\r\n");
            b.Append("migration_version=").Append(sp.MigrationVersion).Append("\r\n");
            return b.ToString();
        }

        public static Dictionary<string, string> ReadCfg(string path)
        {
            Dictionary<string, string> d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (!File.Exists(path)) return d;
            foreach (string raw in File.ReadAllLines(path))
            {
                string l = raw.Trim();
                if (l.Length == 0 || l.StartsWith("#")) continue;
                int i = l.IndexOf('=');
                if (i <= 0) continue;
                d[l.Substring(0, i).Trim()] = l.Substring(i + 1).Trim();
            }
            return d;
        }

        /// <summary>A Chapter 3 PC save, checked the way the game checks it: 3055 lines, the last three the story point, a
        /// Chapter 3 room id (30000-39999) and the play time. Returns "" when it is one, else what is wrong.</summary>
        public static string CheckSaveFormat(byte[] data)
        {
            if (data == null || data.Length == 0) return "the file is empty";
            string text;
            try { text = Encoding.UTF8.GetString(data); } catch { return "the file is not text"; }
            string[] lines = text.Split(new[] { "\r\n" }, StringSplitOptions.None);
            if (lines.Length == 1 && text.Contains("\n")) lines = text.Split('\n');
            int n = lines.Length;
            if (n > 0 && lines[n - 1].Length == 0) n--;
            if (n != 3055) return "it is not a DELTARUNE Chapter 3 save (" + n + " lines, 3055 expected)";
            string plot = lines[n - 3].Trim(), room = lines[n - 2].Trim();
            long p, r;
            if (!long.TryParse(plot, NumberStyles.Integer, CultureInfo.InvariantCulture, out p)) return "its story point is not a number";
            if (!long.TryParse(room, NumberStyles.Integer, CultureInfo.InvariantCulture, out r)) return "its room is not a number";
            if (r < 30000 || r >= 40000) return "its room (" + r + ") is not a Chapter 3 room";
            return "";
        }

        public static void ReadStart(byte[] data, out long plot, out long room)
        {
            string[] lines = Encoding.UTF8.GetString(data).Split(new[] { "\r\n" }, StringSplitOptions.None);
            int n = lines.Length;
            if (n > 0 && lines[n - 1].Length == 0) n--;
            plot = long.Parse(lines[n - 3].Trim(), CultureInfo.InvariantCulture);
            room = long.Parse(lines[n - 2].Trim(), CultureInfo.InvariantCulture);
        }

        /// <summary>The provided save as DRBR expects it: its checksum, its format, its starting room and story point.</summary>
        public static string ValidateTemplate(byte[] data, SaveProfileInfo sp)
        {
            if (data == null) return "the DRBR starting save is missing";
            if (sp != null && Hash.IsSha256(sp.TemplateSha256) && !Hash.Same(Hash.Sha256Bytes(data), sp.TemplateSha256))
                return "the DRBR starting save is damaged or is not the one this release ships (checksum mismatch)";
            string f = CheckSaveFormat(data);
            if (f.Length > 0) return "the DRBR starting save is unusable: " + f;
            if (sp != null)
            {
                long plot, room;
                ReadStart(data, out plot, out room);
                if (room != sp.StartingRoomId || plot != sp.StartingPlot)
                    return "the DRBR starting save is not at the expected start (room " + room + ", story point " + plot + "; expected " + sp.StartingRoomId + ", " + sp.StartingPlot + ")";
            }
            return "";
        }

        /// <summary>Makes sure the DRBR install's bundle has the provided save and the profile config (repairing them from the
        /// launcher's own copy). Returns what it had to do.</summary>
        public static List<string> EnsureBundle(DrbrPaths p, SaveProfileInfo sp, string startMode)
        {
            List<string> did = new List<string>();
            Directory.CreateDirectory(p.BundleDataDir);
            byte[] cur = File.Exists(p.BundleTemplate) ? File.ReadAllBytes(p.BundleTemplate) : null;
            if (ValidateTemplate(cur, sp).Length > 0)
            {
                string store = Path.Combine(p.SaveProfileDir, "start_filech3");
                byte[] good = File.Exists(store) ? File.ReadAllBytes(store) : null;
                string why = ValidateTemplate(good, sp);
                if (why.Length > 0)
                {
                    string pay = Path.Combine(p.PayloadDir, sp.TemplateFile);
                    good = File.Exists(pay) ? File.ReadAllBytes(pay) : null;
                    why = ValidateTemplate(good, sp);
                }
                if (why.Length > 0) throw new DrbrException("template_missing", "The DRBR starting save is missing and no good copy of it was found (" + why + "). Reinstall DRBR with DRBR-Setup.exe.");
                Fs.WriteAtomic(p.BundleTemplate, good);
                did.Add(cur == null ? "restored the missing DRBR starting save" : "replaced a damaged DRBR starting save");
            }
            string cfg = CfgText(sp, startMode);
            string old = File.Exists(p.BundleProfileCfg) ? File.ReadAllText(p.BundleProfileCfg) : null;
            if (old != cfg)
            {
                Fs.WriteAtomicText(p.BundleProfileCfg, cfg);
                did.Add(old == null ? "wrote the DRBR profile config" : "updated the DRBR profile config");
            }
            // the launcher's own copy (used to repair the bundle)
            string storeT = Path.Combine(p.SaveProfileDir, "start_filech3");
            byte[] bt = File.ReadAllBytes(p.BundleTemplate);
            if (!File.Exists(storeT) || !Hash.Same(Hash.Sha256File(storeT), Hash.Sha256Bytes(bt))) Fs.WriteAtomic(storeT, bt);
            return did;
        }

        /// <summary>The installed profile's versions (save-profile\profile.json): the migrations step from it.</summary>
        public static JsonObject ReadProfileState(DrbrPaths p)
        {
            string f = Path.Combine(p.SaveProfileDir, "profile.json");
            try { if (File.Exists(f)) return Json.ParseObject(File.ReadAllText(f)); } catch { }
            return null;
        }

        /// <summary>Brings the DRBR profile up to this release (save template / migration versions). Migrations never touch
        /// the player's own DELTARUNE saves, and never the mod's settings files.</summary>
        public static List<string> Migrate(DrbrPaths p, SaveProfileInfo sp)
        {
            List<string> did = new List<string>();
            JsonObject st = ReadProfileState(p);
            int fromMig = st != null ? (int)st.Long("migration_version", 0) : 0;
            int fromTpl = st != null ? (int)st.Long("save_template_version", 0) : 0;
            if (st != null && (int)st.Long("schema_version", 1) > sp.SchemaVersion)
                throw new DrbrException("profile_newer", "This DRBR profile was made by a newer DRBR version (profile schema " + st.Long("schema_version") + "). Update DRBR.");
            // migration 1: none (the first DRBR profile). A later release adds its steps here, e.g. moving a renamed file.
            if (fromTpl != 0 && fromTpl != sp.TemplateVersion)
                did.Add("the starting save changed (template v" + fromTpl + " -> v" + sp.TemplateVersion + "): the next start uses the new one");
            JsonObject o = new JsonObject();
            o["schema_version"] = (long)sp.SchemaVersion;
            o["profile"] = sp.Profile;
            o["save_template_version"] = (long)sp.TemplateVersion;
            o["save_template_sha256"] = sp.TemplateSha256;
            o["migration_version"] = (long)sp.MigrationVersion;
            o["starting_location"] = sp.StartingLocation;
            o["starting_room_id"] = (long)sp.StartingRoomId;
            o["starting_plot"] = (long)sp.StartingPlot;
            o["updated"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
            Directory.CreateDirectory(p.SaveProfileDir);
            string text = Json.Write(o);
            string f = Path.Combine(p.SaveProfileDir, "profile.json");
            bool same = st != null && fromMig == sp.MigrationVersion && fromTpl == sp.TemplateVersion && Hash.Same(st.Str("save_template_sha256", ""), sp.TemplateSha256);
            if (!same)
            {
                Fs.WriteAtomicText(f, text);
                // (a first install has nothing to migrate: only an upgrade of an existing profile is worth saying)
                if (fromMig != 0 && fromMig != sp.MigrationVersion) did.Add("the DRBR profile was brought up to date (" + fromMig + " -> " + sp.MigrationVersion + ")");
            }
            return did;
        }

        /// <summary>RESTORE STARTING SAVE: the DRBR story saves are moved aside (to backups\profile-...), so the next start is
        /// the provided save in either start mode. The DRBR controls (keyconfig) and the mod's settings stay.</summary>
        public static int RestoreStartingSave(DrbrPaths p)
        {
            if (!Directory.Exists(p.LiveProfile)) return 0;
            string dest = Path.Combine(p.BackupDir, "profile-" + DateTime.Now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture));
            int n = 0;
            foreach (string f in Directory.GetFiles(p.LiveProfile))
            {
                string name = Path.GetFileName(f).ToLowerInvariant();
                if (!(name.StartsWith("filech") || name == "dr.ini")) continue;
                Directory.CreateDirectory(dest);
                File.Move(f, Path.Combine(dest, Path.GetFileName(f)));
                n++;
            }
            Log.Info("Restore starting save: " + n + " DRBR save file(s) moved to " + dest);
            return n;
        }

        /// <summary>drbr_profile\last_start.ini, written by the game at its DRBR start ([start] result=ok / error / wrong_room ...).</summary>
        public static Dictionary<string, string> ReadLastStart(DrbrPaths p)
        {
            Dictionary<string, string> d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (!File.Exists(p.LastStart)) return d;
            foreach (string raw in File.ReadAllLines(p.LastStart))
            {
                string l = raw.Trim();
                int i = l.IndexOf('=');
                if (i <= 0 || l.StartsWith("[")) continue;
                d[l.Substring(0, i).Trim()] = l.Substring(i + 1).Trim().Trim('"');
            }
            return d;
        }

        /// <summary>The player's own DELTARUNE save files (never DRBR's): name -> SHA-256. Compared before / after DRBR runs.</summary>
        public static SortedDictionary<string, string> VanillaSnapshot(string saveArea)
        {
            SortedDictionary<string, string> d = new SortedDictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (!Directory.Exists(saveArea)) return d;
            foreach (string f in Directory.GetFiles(saveArea))
            {
                string n = Path.GetFileName(f).ToLowerInvariant();
                // (true_config.ini is the game's shared settings - window size, language - not a save: DRBR shares it on purpose)
                if (n.StartsWith("filech") || n == "dr.ini" || n.StartsWith("keyconfig_") || n.StartsWith("config_"))
                {
                    try { d[Path.GetFileName(f)] = Hash.Sha256File(f); } catch { d[Path.GetFileName(f)] = "unreadable"; }
                }
            }
            return d;
        }

        public static List<string> CompareSnapshots(SortedDictionary<string, string> before, SortedDictionary<string, string> after)
        {
            List<string> diff = new List<string>();
            foreach (KeyValuePair<string, string> kv in before)
            {
                string a;
                if (!after.TryGetValue(kv.Key, out a)) diff.Add(kv.Key + " was removed");
                else if (!Hash.Same(a, kv.Value)) diff.Add(kv.Key + " changed");
            }
            foreach (string k in after.Keys) if (!before.ContainsKey(k)) diff.Add(k + " was added");
            return diff;
        }
    }
}
