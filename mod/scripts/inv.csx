using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
EnsureDataLoaded();
string outp = Environment.GetEnvironmentVariable("OUT_DIR");
Directory.CreateDirectory(outp);
string H(string s){ using var h=SHA1.Create(); return BitConverter.ToString(h.ComputeHash(Encoding.UTF8.GetBytes(s))).Replace("-","").Substring(0,16);}
var sb = new StringBuilder();
foreach (var o in Data.GameObjects)
{
    var ev = new StringBuilder();
    for (int i = 0; i < o.Events.Count; i++)
        foreach (var e in o.Events[i])
        {
            foreach (var a in e.Actions) ev.Append(i + ":" + e.EventSubtype + ":" + (a.CodeId?.Name?.Content ?? "-") + ";");
        }
    string props = $"{o.ParentId?.Name?.Content}|{o.Sprite?.Name?.Content}|{o.TextureMaskId?.Name?.Content}|{o.Visible}|{o.Solid}|{o.Persistent}|{o.Depth}|{o.UsesPhysics}";
    sb.AppendLine(o.Name.Content + "\t" + H(props) + "\t" + H(ev.ToString()) + "\t" + props);
}
File.WriteAllText(Path.Combine(outp, "objects.tsv"), sb.ToString()); sb.Clear();
foreach (var s in Data.Sounds)
{
    string d = "";
    try { if (s.AudioFile != null) d = BitConverter.ToString(SHA1.HashData(s.AudioFile.Data)).Replace("-","").Substring(0,16); } catch {}
    sb.AppendLine(s.Name.Content + "\t" + d + "\t" + s.File?.Content + "\t" + s.Flags + "\t" + s.Volume + "\t" + s.Pitch + "\t" + (s.AudioGroup?.Name?.Content));
}
File.WriteAllText(Path.Combine(outp, "sounds.tsv"), sb.ToString()); sb.Clear();
foreach (var r in Data.Rooms)
{
    var inst = string.Join(";", r.GameObjects.Select(g => g.ObjectDefinition?.Name?.Content + "@" + g.X + "," + g.Y + "#" + (g.CreationCode?.Name?.Content ?? "-") + "#" + g.InstanceID));
    sb.AppendLine(r.Name.Content + "\t" + r.Width + "x" + r.Height + "\t" + r.GameObjects.Count + "\t" + H(inst) + "\t" + (r.CreationCodeId?.Name?.Content ?? "-") + "\t" + r.Layers.Count);
}
File.WriteAllText(Path.Combine(outp, "rooms.tsv"), sb.ToString()); sb.Clear();
foreach (var f in Data.Fonts) sb.AppendLine(f.Name.Content + "\t" + f.DisplayName?.Content + "\t" + f.EmSize);
File.WriteAllText(Path.Combine(outp, "fonts.tsv"), sb.ToString());
foreach (var s in Data.Scripts) sb.AppendLine(s.Name.Content);
Console.WriteLine($"DONE obj={Data.GameObjects.Count} snd={Data.Sounds.Count} rooms={Data.Rooms.Count}");
