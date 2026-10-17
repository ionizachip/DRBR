using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UndertaleModLib;
using UndertaleModLib.Models;
using UndertaleModLib.Compiler;
using UndertaleModLib.Util;

EnsureDataLoaded();
string BUILD = Environment.GetEnvironmentVariable("BUILD_DIR");
string MODS = Environment.GetEnvironmentVariable("MODS_DIR");
string STAGE = Environment.GetEnvironmentVariable("STAGE") ?? "all";
var cfg = JObject.Parse(File.ReadAllText(Path.Combine(BUILD, "assets.json")));
var knights = JObject.Parse(File.ReadAllText(Environment.GetEnvironmentVariable("KNIGHTS_JSON")));
var keys = knights["variants"].Select(v => (string)v["key"]).ToList();
var rename = (JObject)cfg["rename"];
var man = (JObject)cfg["manifest"];
var log = new List<string>();
void L(string s) { Console.WriteLine(s); log.Add(s); }

UndertaleData LoadMod(string key)
{
    if (key == "base") return Data;
    using var fs = File.OpenRead(Path.Combine(MODS, key + ".win"));
    return UndertaleIO.Read(fs, (w, i) => { });
}
string Map(string variant, string name)
{
    if (name == null) return null;
    var m = rename[variant] as JObject;
    if (m != null && m.TryGetValue(name, out var v)) return (string)v;
    return name;
}
UndertaleString S(string s) => Data.Strings.MakeString(s);

// texture group that holds the Roaring Knight art, so copied art loads whenever the original does
UndertaleTextureGroupInfo grp = null;
var refSpr = Data.Sprites.ByName("spr_roaringknight_idle") ?? Data.Sprites[0];
if (Data.TextureGroupInfo != null)
    grp = Data.TextureGroupInfo.FirstOrDefault(g => g.Sprites.Any(r => r.Resource == refSpr)) ?? Data.TextureGroupInfo.FirstOrDefault();
L("texture group: " + (grp?.Name?.Content ?? "none"));

int pageCounter = Data.EmbeddedTextures.Count;
int itemCounter = Data.TexturePageItems.Count;
var pageMap = new Dictionary<(string, UndertaleEmbeddedTexture), UndertaleEmbeddedTexture>();
int copiedSprites = 0, copiedPages = 0, copiedSounds = 0, createdObjs = 0;

// DRBR: sprites marked "pack" in the manifest are cut out of their source pages and packed into new pages of their own (a
// source page of Chapters 2 / 4 / 5 holds many sprites: copying whole pages would add a lot of unused art). Each frame keeps
// its size, its place in the frame (Target / Bounding) and its pixels exactly.
void PackPages(List<(UndertaleTexturePageItem dst, UndertaleTexturePageItem src)> q, string key)
{
    if (q.Count == 0) return;
    const int PW = 2048, PH = 2048, PAD = 2;
    var tw = new TextureWorker();
    var srcPages = new Dictionary<UndertaleEmbeddedTexture, ImageMagick.MagickImage>();
    ImageMagick.MagickImage cur = null;
    UndertaleEmbeddedTexture page = null;
    int cx = 0, cy = 0, rowH = 0, npages = 0, nitems = 0;
    // the new pages are stored the way this game file stores its own (a raw RGBA page cannot be written: Chapter 3's are
    // BZip2-compressed QOI)
    var fmt = Data.EmbeddedTextures[0].TextureData.Image.Format;
    void Flush()
    {
        if (cur == null) return;
        page.TextureData.Image = GMImage.FromMagickImage(cur).ConvertToFormat(fmt);
        cur.Dispose(); cur = null;
    }
    foreach (var pr in q.OrderByDescending(p => p.src.SourceHeight).ThenByDescending(p => p.src.SourceWidth))
    {
        var s0 = pr.src;
        int w = s0.SourceWidth, h = s0.SourceHeight;
        if (w > PW || h > PH) { L("  PACK too big " + w + "x" + h + " (" + key + ")"); continue; }
        if (cur != null && cx + w > PW) { cx = 0; cy += rowH + PAD; rowH = 0; }
        if (cur == null || cy + h > PH)
        {
            Flush();
            cur = new ImageMagick.MagickImage(ImageMagick.MagickColors.Transparent, PW, PH);
            page = new UndertaleEmbeddedTexture { Name = S("Texture " + pageCounter++), Scaled = s0.TexturePage.Scaled, GeneratedMips = s0.TexturePage.GeneratedMips, TextureExternal = false, TextureLoaded = true };
            Data.EmbeddedTextures.Add(page);
            grp?.TexturePages.Add(new UndertaleResourceById<UndertaleEmbeddedTexture, UndertaleChunkTXTR>() { Resource = page });
            cx = 0; cy = 0; rowH = 0; npages++;
        }
        if (!srcPages.TryGetValue(s0.TexturePage, out var sp)) { sp = tw.GetEmbeddedTexture(s0.TexturePage); srcPages[s0.TexturePage] = sp; }
        using (var crop = (ImageMagick.MagickImage)sp.Clone())
        {
            crop.Crop(new ImageMagick.MagickGeometry(s0.SourceX, s0.SourceY, (uint)w, (uint)h));
            crop.ResetPage();
            cur.Composite(crop, cx, cy, ImageMagick.CompositeOperator.Copy);
        }
        pr.dst.SourceX = (ushort)cx; pr.dst.SourceY = (ushort)cy; pr.dst.SourceWidth = (ushort)w; pr.dst.SourceHeight = (ushort)h;
        pr.dst.TexturePage = page;
        cx += w + PAD; rowH = Math.Max(rowH, h); nitems++;
    }
    Flush();
    foreach (var sp in srcPages.Values) sp.Dispose();
    tw.Dispose();
    L($"  packed {nitems} frames of {key} into {npages} new page(s), format {fmt}");
}

if (STAGE == "all" || STAGE == "assets")
{
    // group manifest entries by source variant
    foreach (var key in keys.Concat(new[] { "c5", "c4", "c2", "c1" }).ToList())
    {
        var sprs = ((JArray)man["sprites"]).Where(m => (string)m["src"] == key && !((string)m["new"] == (string)m["name"] && key == "base")).ToList();
        var snds = ((JArray)man["sounds"]).Where(m => (string)m["src"] == key && !((string)m["new"] == (string)m["name"] && key == "base")).ToList();
        if (sprs.Count == 0 && snds.Count == 0) continue;
        L($"--- copying from {key}: {sprs.Count} sprites, {snds.Count} sounds");
        var src = LoadMod(key);
        var packQ = new List<(UndertaleTexturePageItem dst, UndertaleTexturePageItem src)>();
        foreach (var m in sprs)
        {
            string name = (string)m["name"], nn = (string)m["new"];
            if (Data.Sprites.ByName(nn) != null) { L("  sprite exists, skip " + nn); continue; }
            var d = src.Sprites.ByName(name);
            if (d == null) { L("  MISSING donor sprite " + name + " in " + key); continue; }
            var s = new UndertaleSprite
            {
                Name = S(nn), Width = d.Width, Height = d.Height, MarginLeft = d.MarginLeft, MarginRight = d.MarginRight,
                MarginTop = d.MarginTop, MarginBottom = d.MarginBottom, Transparent = d.Transparent, Smooth = d.Smooth,
                Preload = d.Preload, BBoxMode = d.BBoxMode, SepMasks = d.SepMasks, OriginX = d.OriginX, OriginY = d.OriginY,
                SVersion = d.SVersion, SSpriteType = d.SSpriteType, GMS2PlaybackSpeed = d.GMS2PlaybackSpeed,
                GMS2PlaybackSpeedType = d.GMS2PlaybackSpeedType, IsSpecialType = d.IsSpecialType
            };
            // build 50: an origin shift for a copy (Flowery's battle poses stand where Kris's do)
            if (m["dx"] != null) s.OriginX = d.OriginX + (int)m["dx"];
            if (m["dy"] != null) s.OriginY = d.OriginY + (int)m["dy"];
            foreach (var cm in d.CollisionMasks) s.CollisionMasks.Add(new UndertaleSprite.MaskEntry(cm.Data, cm.Width, cm.Height));
            bool pack = m["pack"] != null && (bool)m["pack"];
            foreach (var te in d.Textures)
            {
                if (te?.Texture == null) { s.Textures.Add(new UndertaleSprite.TextureEntry()); continue; }
                var t = te.Texture;
                if (pack)
                {
                    // DRBR: the frame's own item, its pixels packed after this source's sprites (PackPages)
                    var pitem = new UndertaleTexturePageItem
                    {
                        Name = S("PageItem " + itemCounter++), SourceX = 0, SourceY = 0, SourceWidth = t.SourceWidth, SourceHeight = t.SourceHeight,
                        TargetX = t.TargetX, TargetY = t.TargetY, TargetWidth = t.TargetWidth, TargetHeight = t.TargetHeight,
                        BoundingWidth = t.BoundingWidth, BoundingHeight = t.BoundingHeight, TexturePage = null
                    };
                    Data.TexturePageItems.Add(pitem);
                    s.Textures.Add(new UndertaleSprite.TextureEntry() { Texture = pitem });
                    packQ.Add((pitem, t));
                    continue;
                }
                UndertaleEmbeddedTexture page;
                if (key == "base") page = t.TexturePage;
                else if (!pageMap.TryGetValue((key, t.TexturePage), out page))
                {
                    page = new UndertaleEmbeddedTexture
                    {
                        Name = S("Texture " + pageCounter++), Scaled = t.TexturePage.Scaled, GeneratedMips = t.TexturePage.GeneratedMips,
                        TextureExternal = false, TextureLoaded = true
                    };
                    page.TextureData.Image = t.TexturePage.TextureData.Image;
                    Data.EmbeddedTextures.Add(page);
                    grp?.TexturePages.Add(new UndertaleResourceById<UndertaleEmbeddedTexture, UndertaleChunkTXTR>() { Resource = page });
                    pageMap[(key, t.TexturePage)] = page; copiedPages++;
                }
                var item = new UndertaleTexturePageItem
                {
                    Name = S("PageItem " + itemCounter++), SourceX = t.SourceX, SourceY = t.SourceY, SourceWidth = t.SourceWidth, SourceHeight = t.SourceHeight,
                    TargetX = t.TargetX, TargetY = t.TargetY, TargetWidth = t.TargetWidth, TargetHeight = t.TargetHeight,
                    BoundingWidth = t.BoundingWidth, BoundingHeight = t.BoundingHeight, TexturePage = page
                };
                Data.TexturePageItems.Add(item);
                s.Textures.Add(new UndertaleSprite.TextureEntry() { Texture = item });
            }
            Data.Sprites.Add(s);
            grp?.Sprites.Add(new UndertaleResourceById<UndertaleSprite, UndertaleChunkSPRT>() { Resource = s });
            copiedSprites++;
        }
        PackPages(packQ, key);
        foreach (var m in snds)
        {
            string name = (string)m["name"], nn = (string)m["new"];
            if (Data.Sounds.ByName(nn) != null) { L("  sound exists, skip " + nn); continue; }
            var d = src.Sounds.ByName(name);
            if (d == null) { L("  MISSING donor sound " + name + " in " + key); continue; }
            var s = new UndertaleSound
            {
                Name = S(nn), Flags = d.Flags, Type = d.Type == null ? null : S(d.Type.Content), File = d.File == null ? null : S(d.File.Content),
                Effects = d.Effects, Volume = d.Volume, Preload = d.Preload, Pitch = d.Pitch, AudioLength = d.AudioLength,
                AudioGroup = Data.AudioGroups.Count > 0 ? Data.AudioGroups[0] : null
            };
            if (key != "base" && nn != name && d.File != null) s.File = S(nn + Path.GetExtension(d.File.Content));
            if (d.AudioFile != null)
            {
                var ea = new UndertaleEmbeddedAudio { Name = S("EmbeddedSound " + Data.EmbeddedAudio.Count), Data = d.AudioFile.Data };
                Data.EmbeddedAudio.Add(ea); s.AudioFile = ea;
            }
            Data.Sounds.Add(s); copiedSounds++;
        }
        // DRBR: a boss's own shaders (Flowery's tower), copied whole from its chapter's game file - every chapter runs on the
        // same DELTARUNE.exe (-game chapterN_windows/data.win), so the compiled HLSL is this runner's own; the code checks
        // shader_is_compiled() and draws without them if a shader does not load
        var shds = man["shaders"] == null ? new List<JToken>() : ((JArray)man["shaders"]).Where(m => (string)m["src"] == key).ToList();
        foreach (var m in shds)
        {
            string name = (string)m["name"], nn = (string)m["new"];
            if (Data.Shaders.ByName(nn) != null) { L("  shader exists, skip " + nn); continue; }
            var d = src.Shaders.ByName(name);
            if (d == null) { L("  MISSING donor shader " + name + " in " + key); continue; }
            UndertaleString SS(UndertaleString u) => u == null ? null : S(u.Content);
            var sh = new UndertaleShader
            {
                Name = S(nn), Type = d.Type, GLSL_ES_Vertex = SS(d.GLSL_ES_Vertex), GLSL_ES_Fragment = SS(d.GLSL_ES_Fragment),
                GLSL_Vertex = SS(d.GLSL_Vertex), GLSL_Fragment = SS(d.GLSL_Fragment), HLSL9_Vertex = SS(d.HLSL9_Vertex), HLSL9_Fragment = SS(d.HLSL9_Fragment),
                Version = d.Version
            };
            sh.HLSL11_VertexData = d.HLSL11_VertexData; sh.HLSL11_PixelData = d.HLSL11_PixelData;
            sh.PSSL_VertexData = d.PSSL_VertexData; sh.PSSL_PixelData = d.PSSL_PixelData;
            sh.Cg_PSVita_VertexData = d.Cg_PSVita_VertexData; sh.Cg_PSVita_PixelData = d.Cg_PSVita_PixelData;
            sh.Cg_PS3_VertexData = d.Cg_PS3_VertexData; sh.Cg_PS3_PixelData = d.Cg_PS3_PixelData;
            foreach (var at in d.VertexShaderAttributes)
                sh.VertexShaderAttributes.Add(new UndertaleShader.VertexShaderAttribute { Name = S(at.Name.Content) });
            Data.Shaders.Add(sh);
            L("  shader copied " + name + " -> " + nn);
        }
        if (key != "base") src = null;
        GC.Collect();
    }
    L($"copied sprites={copiedSprites} pages={copiedPages} sounds={copiedSounds}");

    // ---- extra art packed into atlases, each sprite built like its donor (same size, origin, masks):
    //      blue_atlas = Heatwave's blue fire (make_blue_assets.py), hub_atlas = Knight Hub menu buttons and captions (make_hub_ui_assets.py)
    foreach (var atlasName in new[] { "blue_atlas", "hub_atlas", "fl_atlas", "bn_atlas" })
    {
        var atlasJson = Path.Combine(MODS, atlasName + ".json");
        if (!File.Exists(atlasJson)) { L("  no " + atlasName + ".json"); continue; }
        var bj = JObject.Parse(File.ReadAllText(atlasJson));
        var atlasBytes = File.ReadAllBytes(Path.Combine(MODS, atlasName + ".png"));
        UndertaleEmbeddedTexture bpage = null;
        foreach (var bp in ((JObject)bj["sprites"]).Properties())
        {
            string nn = bp.Name; var bm = (JObject)bp.Value;
            if (Data.Sprites.ByName(nn) != null) { L("  atlas sprite exists, skip " + nn); continue; }
            var donor = Data.Sprites.ByName((string)bm["donor"]);
            if (donor == null) { L("  MISSING donor for atlas sprite " + nn); continue; }
            if (bpage == null)
            {
                bpage = new UndertaleEmbeddedTexture { Name = S("Texture " + pageCounter++), Scaled = donor.Textures[0].Texture.TexturePage.Scaled, GeneratedMips = donor.Textures[0].Texture.TexturePage.GeneratedMips, TextureExternal = false, TextureLoaded = true };
                bpage.TextureData.Image = UndertaleModLib.Util.GMImage.FromPng(atlasBytes, true);
                Data.EmbeddedTextures.Add(bpage);
                grp?.TexturePages.Add(new UndertaleResourceById<UndertaleEmbeddedTexture, UndertaleChunkTXTR>() { Resource = bpage });
            }
            var bs = new UndertaleSprite
            {
                Name = S(nn), Width = donor.Width, Height = donor.Height, MarginLeft = donor.MarginLeft, MarginRight = donor.MarginRight,
                MarginTop = donor.MarginTop, MarginBottom = donor.MarginBottom, Transparent = donor.Transparent, Smooth = donor.Smooth,
                Preload = donor.Preload, BBoxMode = donor.BBoxMode, SepMasks = donor.SepMasks, OriginX = donor.OriginX, OriginY = donor.OriginY,
                SVersion = donor.SVersion, SSpriteType = donor.SSpriteType, GMS2PlaybackSpeed = donor.GMS2PlaybackSpeed,
                GMS2PlaybackSpeedType = donor.GMS2PlaybackSpeedType, IsSpecialType = donor.IsSpecialType
            };
            // build 50 (fl_atlas): a sprite of its own size and origin (an empty collision mask of that size)
            if (bm["w"] != null)
            {
                bs.Width = (uint)(int)bm["w"]; bs.Height = (uint)(int)bm["h"]; bs.OriginX = (int)bm["ox"]; bs.OriginY = (int)bm["oy"];
                bs.MarginLeft = 0; bs.MarginTop = 0; bs.MarginRight = (int)bs.Width - 1; bs.MarginBottom = (int)bs.Height - 1; bs.SepMasks = UndertaleSprite.SepMaskType.AxisAlignedRect; bs.BBoxMode = 0;
                bs.CollisionMasks.Add(new UndertaleSprite.MaskEntry(new byte[(((int)bs.Width + 7) / 8) * (int)bs.Height], (int)bs.Width, (int)bs.Height));
            }
            else
            foreach (var cm in donor.CollisionMasks) bs.CollisionMasks.Add(new UndertaleSprite.MaskEntry(cm.Data, cm.Width, cm.Height));
            foreach (var fr in (JArray)bm["frames"])
            {
                ushort fx = (ushort)(int)fr["x"], fy = (ushort)(int)fr["y"], fw = (ushort)(int)fr["w"], fh = (ushort)(int)fr["h"];
                var item = new UndertaleTexturePageItem
                {
                    Name = S("PageItem " + itemCounter++), SourceX = fx, SourceY = fy, SourceWidth = fw, SourceHeight = fh,
                    TargetX = 0, TargetY = 0, TargetWidth = fw, TargetHeight = fh, BoundingWidth = (ushort)bs.Width, BoundingHeight = (ushort)bs.Height, TexturePage = bpage
                };
                Data.TexturePageItems.Add(item);
                bs.Textures.Add(new UndertaleSprite.TextureEntry() { Texture = item });
            }
            Data.Sprites.Add(bs);
            grp?.Sprites.Add(new UndertaleResourceById<UndertaleSprite, UndertaleChunkSPRT>() { Resource = bs });
            L("  atlas sprite added " + nn + " (" + bs.Textures.Count + " frames, " + atlasName + ")");
        }
    }

    // object shells (added objects + prop-conflict clones), then properties
    var objEntries = ((JArray)man["objects"]).Where(m => !((string)m["new"] == (string)m["name"] && (string)m["src"] == "base")).ToList();
    foreach (var m in objEntries)
    {
        string nn = (string)m["new"];
        if (Data.GameObjects.ByName(nn) == null) { Data.GameObjects.Add(new UndertaleGameObject { Name = S(nn) }); createdObjs++; }
    }
    foreach (var key in keys.Concat(new[] { "c5", "c4", "c2", "c1" }).ToList())
    {
        var mine = objEntries.Where(m => (string)m["src"] == key).ToList();
        if (mine.Count == 0) continue;
        var src = LoadMod(key);
        foreach (var m in mine)
        {
            var o = Data.GameObjects.ByName((string)m["new"]);
            var d = src.GameObjects.ByName((string)m["name"]);
            if (d == null) { L("  MISSING donor object " + (string)m["name"] + " in " + key); continue; }
            o.Sprite = d.Sprite == null ? null : Data.Sprites.ByName(Map(key, d.Sprite.Name.Content));
            o.TextureMaskId = d.TextureMaskId == null ? null : Data.Sprites.ByName(Map(key, d.TextureMaskId.Name.Content));
            o.ParentId = d.ParentId == null ? null : Data.GameObjects.ByName(Map(key, d.ParentId.Name.Content));
            if (d.ParentId != null && o.ParentId == null) L("  WARN parent not found for " + o.Name.Content + ": " + d.ParentId.Name.Content);
            o.Visible = d.Visible; o.Managed = d.Managed; o.Solid = d.Solid; o.Depth = d.Depth; o.Persistent = d.Persistent;
            o.UsesPhysics = d.UsesPhysics; o.IsSensor = d.IsSensor; o.CollisionShape = d.CollisionShape; o.Density = d.Density;
            o.Restitution = d.Restitution; o.Group = d.Group; o.LinearDamping = d.LinearDamping; o.AngularDamping = d.AngularDamping;
            o.Friction = d.Friction; o.Awake = d.Awake; o.Kinematic = d.Kinematic;
        }
        if (key != "base") src = null;
        GC.Collect();
    }
    L($"object shells created={createdObjs}");
}

if (STAGE == "all" || STAGE == "code")
{
    var dir = Path.Combine(BUILD, "merged");
    var files = Directory.GetFiles(dir, "*.gml").OrderBy(f => f).ToList();
    var g = new CodeImportGroup(Data) { AutoCreateAssets = true };
    int bad = 0;
    foreach (var f in files)
    {
        try { g.QueueReplace(Path.GetFileNameWithoutExtension(f), File.ReadAllText(f)); }
        catch (Exception e) { bad++; L("QUEUE FAIL " + Path.GetFileName(f) + ": " + e.Message.Split('\n')[0]); }
    }
    try { g.Import(); L($"CODE IMPORT OK ({files.Count - bad}/{files.Count})"); }
    catch (Exception e) { L("CODE IMPORT FAIL: " + e.Message); }
    var ctrlObj = Data.GameObjects.ByName("obj_knight_ctrl");
    if (ctrlObj != null) { ctrlObj.Persistent = true; ctrlObj.Visible = true; L("ctrl object persistent+visible"); }
    foreach (var nm in new[] { "obj_knight_menu", "obj_knight_prompt", "obj_knight_twin", "obj_knight_twin_bullet", "obj_knight_bench", "obj_knight_skinart" })
    {
        var ob = Data.GameObjects.ByName(nm);
        if (ob != null) { ob.Visible = true; }
    }
    // Twin Knight bullets are ordinary battle bullets: children of obj_regularbullet (heart collision, graze, damage)
    var twinB = Data.GameObjects.ByName("obj_knight_twin_bullet");
    var regB = Data.GameObjects.ByName("obj_regularbullet");
    if (twinB != null && regB != null) { twinB.ParentId = regB; twinB.Depth = -10; L("twin bullet parent obj_regularbullet"); }
    else L("TWIN BULLET SETUP FAIL");
    var twinO = Data.GameObjects.ByName("obj_knight_twin");
    if (twinO != null) { twinO.Persistent = false; twinO.Depth = 91; }
    var benchO = Data.GameObjects.ByName("obj_knight_bench");
    if (benchO != null) { benchO.Persistent = false; benchO.Depth = 91; L("bench object set up"); }
    // inert stand-ins for absent party members: children of the hero objects
    foreach (var (gn, pn) in new[] { ("obj_knight_ghost_kris", "obj_herokris"), ("obj_knight_ghost_susie", "obj_herosusie"), ("obj_knight_ghost_ralsei", "obj_heroralsei") })
    {
        var go2 = Data.GameObjects.ByName(gn);
        var par = Data.GameObjects.ByName(pn);
        if (go2 == null || par == null) { L("GHOST SETUP FAIL " + gn + " / " + pn); continue; }
        go2.ParentId = par; go2.Visible = false; go2.Persistent = false; go2.Solid = false;
        L("ghost " + gn + " parent " + pn);
    }
    // build 50: the custom characters' battle hero (Flowery, ...): a child of obj_heroparent like the game's own heroes
    var ccO = Data.GameObjects.ByName("obj_knight_herocc");
    var hpO = Data.GameObjects.ByName("obj_heroparent");
    if (ccO != null && hpO != null) { ccO.ParentId = hpO; ccO.Visible = true; ccO.Persistent = false; ccO.Solid = false; L("custom hero parent obj_heroparent"); }
    else L("CUSTOM HERO SETUP FAIL");
    // build 50: Omega Flowery's drawing (obj_knight_omega: its own Draw - outline, body, the chromatic pass)
    var omO = Data.GameObjects.ByName("obj_knight_omega");
    if (omO != null) { omO.Visible = true; omO.Persistent = false; omO.Solid = false; L("omega object set up"); }
    else L("OMEGA OBJECT SETUP FAIL");
    // build 50: the KF Song Pack's player / lyric display (its Draw GUI needs it visible; never persistent)
    var kfO = Data.GameObjects.ByName("obj_kf_songlyrics");
    if (kfO != null) { kfO.Visible = true; kfO.Persistent = false; kfO.Solid = false; L("kf song object set up"); }
    else L("KF SONG OBJECT SETUP FAIL");
}

if (STAGE == "all" || STAGE == "rooms")
{
    var mergedNames = new HashSet<string>(Directory.GetFiles(Path.Combine(BUILD, "merged"), "*.gml").Select(f => Path.GetFileNameWithoutExtension(f)));
    var snow = Data.Rooms.ByName("room_dw_snow_zone");
    foreach (var gi in snow.GameObjects.Where(i => i.ObjectDefinition != null && i.ObjectDefinition.Name.Content.Contains("sign")))
        L($"  snow zone sign-ish instance: id={gi.InstanceID} obj={gi.ObjectDefinition.Name.Content} at {gi.X},{gi.Y} create={gi.CreationCode?.Name?.Content} pre={gi.PreCreateCode?.Name?.Content}");
    foreach (var code in Data.Code.Where(c => c.Name.Content.StartsWith("gml_RoomCC_") && mergedNames.Contains(c.Name.Content)).ToList())
    {
        // gml_RoomCC_<room>_<instanceId>_<Create|PreCreate>
        var n = code.Name.Content.Substring("gml_RoomCC_".Length);
        int us = n.LastIndexOf('_'); string ev = n.Substring(us + 1); n = n.Substring(0, us);
        int us2 = n.LastIndexOf('_'); string idStr = n.Substring(us2 + 1); string rn = n.Substring(0, us2);
        var room = Data.Rooms.ByName(rn); if (room == null || !uint.TryParse(idStr, out var id)) continue;
        var inst = room.GameObjects.FirstOrDefault(i => i.InstanceID == id);
        if (inst == null) { L("  room instance not found for " + code.Name.Content); continue; }
        if (ev == "Create" && inst.CreationCode != code) { inst.CreationCode = code; L("  linked " + code.Name.Content); }
        if (ev == "PreCreate" && inst.PreCreateCode != code) { inst.PreCreateCode = code; L("  linked " + code.Name.Content); }
    }
    foreach (var code in Data.Code.Where(c => c.Name.Content.StartsWith("gml_Room_") && mergedNames.Contains(c.Name.Content)).ToList())
    {
        var rn = code.Name.Content.Substring("gml_Room_".Length); rn = rn.Substring(0, rn.LastIndexOf('_'));
        var room = Data.Rooms.ByName(rn);
        if (room != null && room.CreationCodeId != code) { room.CreationCodeId = code; L("  linked room code " + code.Name.Content); }
    }
}
File.WriteAllLines(Path.Combine(BUILD, "build_" + STAGE + ".log"), log);
