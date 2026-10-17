using System;using System.Linq;
EnsureDataLoaded();
foreach(var n in new[]{"obj_knight_ctrl","obj_knight_menu","obj_knight_prompt"}){var o=Data.GameObjects.ByName(n);
 Console.WriteLine(n+" persistent="+o.Persistent+" events:");
 for(int i=0;i<o.Events.Count;i++)foreach(var e in o.Events[i])Console.WriteLine("  type"+i+" sub"+e.EventSubtype+" actions="+e.Actions.Count);}
