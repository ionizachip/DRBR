using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UndertaleModLib.Util;
EnsureDataLoaded();
string outp = Environment.GetEnvironmentVariable("OUT_TSV");
var sb = new StringBuilder();
var worker = new TextureWorker();
int bad = 0;
foreach (var s in Data.Sprites)
{
    var h = SHA1.Create();
    var meta = $"{s.Width}x{s.Height}:{s.Textures.Count}:{s.OriginX},{s.OriginY}";
    h.TransformBlock(Encoding.UTF8.GetBytes(meta), 0, meta.Length, null, 0);
    foreach (var t in s.Textures)
    {
        try
        {
            if (t?.Texture == null) continue;
            var img = worker.GetTextureFor(t.Texture, s.Name.Content, false);
            var raw = img.ToByteArray(ImageMagick.MagickFormat.Rgba);
            h.TransformBlock(raw, 0, raw.Length, null, 0);
        }
        catch (Exception) { bad++; var m = Encoding.UTF8.GetBytes("ERR"); h.TransformBlock(m, 0, 3, null, 0); }
    }
    h.TransformFinalBlock(new byte[0], 0, 0);
    sb.AppendLine(s.Name.Content + "\t" + BitConverter.ToString(h.Hash).Replace("-", "").Substring(0, 16));
}
File.WriteAllText(outp, sb.ToString());
Console.WriteLine("DONE sprites=" + Data.Sprites.Count + " errs=" + bad);
