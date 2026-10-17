// TESTS ONLY - a stand-in for DELTARUNE.exe (see GameStub.csproj).
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

static class Stub
{
    static int Main(string[] args)
    {
        string game = null;
        for (int i = 0; i < args.Length - 1; i++) if (args[i] == "-game") game = args[i + 1];
        string dataWin = Path.GetFullPath(game ?? "data.win");
        string bundle = Path.GetDirectoryName(dataWin);
        string save = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "DELTARUNE");
        string prof = Path.Combine(save, "drbr_profile");
        Directory.CreateDirectory(prof);
        File.AppendAllText(Path.Combine(save, "stub_runs.log"), DateTime.Now.ToString("s") + " cwd=" + Environment.CurrentDirectory + " game=" + game + "\r\n");
        if (!File.Exists(dataWin)) { Last(prof, "error", "no data.win", "", 0, 0); return 3; }
        string cfg = Path.Combine(bundle, "drbr_data", "drbr_profile.cfg");
        if (!File.Exists(cfg)) { Last(prof, "error", "not a DRBR install (no drbr_profile.cfg)", "", 0, 0); return 4; }
        string mode = "template";
        foreach (string l in File.ReadAllLines(cfg)) if (l.StartsWith("start_mode=")) mode = l.Substring(11).Trim();
        string tpl = Path.Combine(bundle, "drbr_data", "start_filech3");
        if (!File.Exists(tpl)) { Last(prof, "error", "The DRBR starting save (drbr_data\\start_filech3) is missing.", "", 0, 0); return 5; }
        byte[] t = File.ReadAllBytes(tpl);
        string sha1;
        using (SHA1 h = SHA1.Create()) sha1 = BitConverter.ToString(h.ComputeHash(t)).Replace("-", "").ToLowerInvariant();
        if (sha1 != "e1b7086a53f5ac9ec46ecd23c1c465ae4f6a321b" || t.Length != 12385) { Last(prof, "error", "The DRBR starting save (drbr_data\\start_filech3) is damaged or is not one this DRBR version knows.", "", 0, 0); return 6; }
        string live = Path.Combine(prof, "filech3_0");
        string from = "template";
        if (mode == "continue" && File.Exists(live) && File.ReadAllText(live).Split(new[] { "\r\n" }, StringSplitOptions.None).Length == 3055) from = "continue";
        else File.WriteAllBytes(live, t);
        string[] lines = File.ReadAllText(live).Split(new[] { "\r\n" }, StringSplitOptions.None);
        int plot = int.Parse(lines[lines.Length - 3].Trim()), room = int.Parse(lines[lines.Length - 2].Trim());
        Last(prof, "ok", "", from, room, plot);
        int secs = 3;
        string env = Environment.GetEnvironmentVariable("DRBR_STUB_SECONDS");
        if (!string.IsNullOrEmpty(env)) int.TryParse(env, out secs);
        Thread.Sleep(secs * 1000);
        return 0;
    }

    static void Last(string prof, string result, string err, string from, int room, int plot)
    {
        StringBuilder b = new StringBuilder();
        b.Append("[start]\r\nresult=\"" + result + "\"\r\nerror=\"" + err + "\"\r\nfrom=\"" + from + "\"\r\n");
        if (room != 0) b.Append("room=\"" + (room == 30108 ? "room_dw_snow_zone" : "room_" + room) + "\"\r\nroom_id=" + room + ".000000\r\nplot=" + plot + ".000000\r\nx=120.000000\r\ny=240.000000\r\n");
        File.WriteAllText(Path.Combine(prof, "last_start.ini"), b.ToString());
    }
}
