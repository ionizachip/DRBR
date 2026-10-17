using System;
using System.IO;
using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string dir = Environment.GetEnvironmentVariable("IMPORT_DIR");
var files = Directory.GetFiles(dir, "*.gml");
var g = new UndertaleModLib.Compiler.CodeImportGroup(Data) { AutoCreateAssets = true };
int bad = 0;
foreach (var f in files)
{
    try { g.QueueReplace(Path.GetFileNameWithoutExtension(f), File.ReadAllText(f)); }
    catch (Exception e) { bad++; Console.WriteLine("QUEUE FAIL " + Path.GetFileName(f) + ": " + e.Message.Split('\n')[0]); }
}
try { g.Import(); Console.WriteLine("IMPORT OK, queued " + (files.Length - bad)); }
catch (Exception e) { Console.WriteLine("IMPORT FAIL: " + e.Message); }
