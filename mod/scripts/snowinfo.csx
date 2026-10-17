using System;
using System.Linq;
EnsureDataLoaded();
var room = Data.Rooms.ByName("room_dw_snow_zone");
Console.WriteLine("room " + room.Name.Content + " instances=" + room.GameObjects.Count + " layers=" + room.Layers.Count);
foreach (var gi in room.GameObjects.Where(i => i.InstanceID == 109969 || (i.ObjectDefinition?.Name?.Content ?? "").Contains("sign") || (i.ObjectDefinition?.Name?.Content ?? "").Contains("PTB02")))
    Console.WriteLine($"INST id={gi.InstanceID} obj={gi.ObjectDefinition?.Name?.Content} x={gi.X} y={gi.Y} sx={gi.ScaleX} sy={gi.ScaleY} create={gi.CreationCode?.Name?.Content} pre={gi.PreCreateCode?.Name?.Content}");
foreach (var l in room.Layers)
{
    if (l.InstancesData != null && l.InstancesData.Instances.Any(i => i.InstanceID == 109969 || (i.ObjectDefinition?.Name?.Content ?? "").Contains("PTB02")))
        Console.WriteLine("LAYER " + l.LayerName.Content + " depth=" + l.LayerDepth + " n=" + l.InstancesData.Instances.Count);
}
Console.WriteLine("max inst id " + room.GameObjects.Max(i => i.InstanceID));
