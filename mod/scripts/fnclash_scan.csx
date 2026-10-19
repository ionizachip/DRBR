// DRBR 1.0.4 (fnclash.py): identifiers the code reads as variables but the compiler resolved to a global function (push.i [function]gml_Script_X
// where X is also an instance variable the code assigns) or to an asset constant (an assigned variable named like an asset)
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Collections.Generic;
var popRx = new Regex(@"^\s*pop\.\w\.\w\s+(?:\[\w+\])?([\w-]+)\.(\w+)", RegexOptions.Multiline);
var fnRx = new Regex(@"push\.i \[function\]gml_Script_(\w+)");
var assigned = new Dictionary<string, HashSet<string>>();
var fnrefs = new Dictionary<string, HashSet<string>>();
int n = 0;
foreach (var c in Data.Code)
{
    if (c == null || c.ParentEntry != null) continue;
    string d;
    try { d = c.Disassemble(Data.Variables, Data.CodeLocals?.For(c)); } catch { continue; }
    n++;
    foreach (Match m in popRx.Matches(d))
    {
        var inst = m.Groups[1].Value;
        if (inst == "global" || inst == "local" || inst == "builtin" || inst == "arg") continue;
        var v = m.Groups[2].Value;
        if (!c.Name.Content.StartsWith("gml_Object_") && !c.Name.Content.StartsWith("gml_Room")) continue;
        if (!assigned.ContainsKey(v)) assigned[v] = new HashSet<string>();
        assigned[v].Add(c.Name.Content);
    }
    foreach (Match m in fnRx.Matches(d))
    {
        var f = m.Groups[1].Value;
        if (!fnrefs.ContainsKey(f)) fnrefs[f] = new HashSet<string>();
        fnrefs[f].Add(c.Name.Content);
    }
}
var sb = new System.Text.StringBuilder();
sb.AppendLine("code entries " + n + ", assigned instance variables " + assigned.Count + ", function names referenced bare " + fnrefs.Count);
foreach (var f in fnrefs.Keys.OrderBy(k => k))
{
    if (!assigned.ContainsKey(f)) continue;
    sb.AppendLine("FUNC-VS-VAR " + f + " | read as function in: " + string.Join(" ", fnrefs[f].OrderBy(x => x).Take(40)) + " | assigned in: " + string.Join(" ", assigned[f].OrderBy(x => x).Take(12)));
}
var assets = new Dictionary<string, string>();
foreach (var a in Data.Sprites) if (a != null) assets[a.Name.Content] = "sprite";
foreach (var a in Data.GameObjects) if (a != null) assets[a.Name.Content] = "object";
foreach (var a in Data.Sounds) if (a != null) assets[a.Name.Content] = "sound";
foreach (var a in Data.Rooms) if (a != null) assets[a.Name.Content] = "room";
foreach (var a in Data.Backgrounds) if (a != null) assets[a.Name.Content] = "tileset";
foreach (var a in Data.Paths) if (a != null) assets[a.Name.Content] = "path";
foreach (var a in Data.Fonts) if (a != null) assets[a.Name.Content] = "font";
foreach (var a in Data.Shaders) if (a != null) assets[a.Name.Content] = "shader";
foreach (var a in Data.Timelines) if (a != null) assets[a.Name.Content] = "timeline";
foreach (var a in Data.Sequences ?? new UndertaleModLib.UndertalePointerList<UndertaleModLib.Models.UndertaleSequence>()) if (a != null) assets[a.Name.Content] = "sequence";
foreach (var v in assigned.Keys.OrderBy(k => k))
{
    if (assets.ContainsKey(v))
        sb.AppendLine("ASSET-VS-VAR " + v + " (" + assets[v] + ") | assigned in: " + string.Join(" ", assigned[v].OrderBy(x => x).Take(12)));
}
int nf = sb.ToString().Split(new[] {"\n"}, StringSplitOptions.None).Count(l => l.StartsWith("FUNC-VS-VAR ") || l.StartsWith("ASSET-VS-VAR "));
sb.AppendLine("FNCLASH: " + nf);
File.WriteAllText(Environment.GetEnvironmentVariable("OUTF"), sb.ToString());
Console.WriteLine("SCAN DONE");
