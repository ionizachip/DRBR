using System;using System.IO;using System.Linq;
using UndertaleModLib.Util;
EnsureDataLoaded();
string od=Environment.GetEnvironmentVariable("OUT_DIR");
var names=Environment.GetEnvironmentVariable("SPRS").Split(',');
var w=new TextureWorker();
foreach(var n in names){var s=Data.Sprites.ByName(n);if(s==null){Console.WriteLine("MISSING "+n);continue;}
 int i=0;foreach(var t in s.Textures){try{var img=w.GetTextureFor(t.Texture,n,true);File.WriteAllBytes($"{od}/{n}_{i}.png",img.ToByteArray(ImageMagick.MagickFormat.Png));}catch(Exception e){Console.WriteLine("ERR "+n+i+e.Message);}i++;}
 Console.WriteLine(n+" "+s.Width+"x"+s.Height+" frames="+i+" origin "+s.OriginX+","+s.OriginY);}
