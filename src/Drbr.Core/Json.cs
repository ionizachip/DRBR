// DRBR - a small JSON reader / writer (no dependencies: the launcher runs on the .NET Framework 4.8 every Windows 10/11
// already has, and the tests run on .NET on Linux). Objects are Dictionary<string, object> (key order kept), arrays are
// List<object>, numbers are double (or long when integral), plus string / bool / null.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Drbr
{
    public sealed class JsonObject : Dictionary<string, object>
    {
        public readonly List<string> Order = new List<string>();

        public new object this[string key]
        {
            get { object v; return TryGetValue(key, out v) ? v : null; }
            set { if (!ContainsKey(key)) Order.Add(key); base[key] = value; }
        }

        public new void Add(string key, object value) { this[key] = value; }

        public string Str(string key, string def = null)
        {
            object v = this[key];
            if (v == null) return def;
            if (v is string) return (string)v;
            if (v is bool) return ((bool)v) ? "true" : "false";
            if (v is double) return ((double)v).ToString("R", CultureInfo.InvariantCulture);
            return Convert.ToString(v, CultureInfo.InvariantCulture);
        }

        public long Long(string key, long def = 0)
        {
            object v = this[key];
            if (v is long) return (long)v;
            if (v is double) return (long)(double)v;
            if (v is int) return (int)v;
            long r;
            if (v is string && long.TryParse((string)v, NumberStyles.Integer, CultureInfo.InvariantCulture, out r)) return r;
            return def;
        }

        public bool Bool(string key, bool def = false)
        {
            object v = this[key];
            if (v is bool) return (bool)v;
            if (v is string) return ((string)v).Equals("true", StringComparison.OrdinalIgnoreCase);
            return def;
        }

        public JsonObject Obj(string key) { return this[key] as JsonObject; }
        public List<object> Arr(string key) { return this[key] as List<object> ?? new List<object>(); }
    }

    public static class Json
    {
        public static object Parse(string text)
        {
            int i = 0;
            object v = Value(text, ref i);
            Ws(text, ref i);
            if (i != text.Length) throw new FormatException("JSON: unexpected text at " + i);
            return v;
        }

        public static JsonObject ParseObject(string text)
        {
            JsonObject o = Parse(text) as JsonObject;
            if (o == null) throw new FormatException("JSON: an object was expected");
            return o;
        }

        static void Ws(string s, ref int i)
        {
            while (i < s.Length && (s[i] == ' ' || s[i] == '\t' || s[i] == '\r' || s[i] == '\n' || s[i] == '﻿')) i++;
        }

        static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            if (i >= s.Length) throw new FormatException("JSON: unexpected end");
            char c = s[i];
            if (c == '{') return Obj(s, ref i);
            if (c == '[') return Arr(s, ref i);
            if (c == '"') return Str(s, ref i);
            if (c == 't' && Has(s, i, "true")) { i += 4; return true; }
            if (c == 'f' && Has(s, i, "false")) { i += 5; return false; }
            if (c == 'n' && Has(s, i, "null")) { i += 4; return null; }
            return Num(s, ref i);
        }

        static bool Has(string s, int i, string w) { return string.CompareOrdinal(s, i, w, 0, w.Length) == 0; }

        static JsonObject Obj(string s, ref int i)
        {
            JsonObject o = new JsonObject();
            i++;
            Ws(s, ref i);
            if (i < s.Length && s[i] == '}') { i++; return o; }
            while (true)
            {
                Ws(s, ref i);
                if (i >= s.Length || s[i] != '"') throw new FormatException("JSON: a key was expected at " + i);
                string k = Str(s, ref i);
                Ws(s, ref i);
                if (i >= s.Length || s[i] != ':') throw new FormatException("JSON: ':' was expected at " + i);
                i++;
                o[k] = Value(s, ref i);
                Ws(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == '}') { i++; return o; }
                throw new FormatException("JSON: ',' or '}' was expected at " + i);
            }
        }

        static List<object> Arr(string s, ref int i)
        {
            List<object> a = new List<object>();
            i++;
            Ws(s, ref i);
            if (i < s.Length && s[i] == ']') { i++; return a; }
            while (true)
            {
                a.Add(Value(s, ref i));
                Ws(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == ']') { i++; return a; }
                throw new FormatException("JSON: ',' or ']' was expected at " + i);
            }
        }

        static string Str(string s, ref int i)
        {
            StringBuilder b = new StringBuilder();
            i++;
            while (i < s.Length)
            {
                char c = s[i++];
                if (c == '"') return b.ToString();
                if (c != '\\') { b.Append(c); continue; }
                if (i >= s.Length) break;
                char e = s[i++];
                switch (e)
                {
                    case '"': b.Append('"'); break;
                    case '\\': b.Append('\\'); break;
                    case '/': b.Append('/'); break;
                    case 'b': b.Append('\b'); break;
                    case 'f': b.Append('\f'); break;
                    case 'n': b.Append('\n'); break;
                    case 'r': b.Append('\r'); break;
                    case 't': b.Append('\t'); break;
                    case 'u':
                        if (i + 4 > s.Length) throw new FormatException("JSON: bad \\u escape");
                        b.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                        i += 4;
                        break;
                    default: throw new FormatException("JSON: bad escape \\" + e);
                }
            }
            throw new FormatException("JSON: unterminated string");
        }

        static object Num(string s, ref int i)
        {
            int st = i;
            if (i < s.Length && (s[i] == '-' || s[i] == '+')) i++;
            while (i < s.Length && (char.IsDigit(s[i]) || s[i] == '.' || s[i] == 'e' || s[i] == 'E' || s[i] == '-' || s[i] == '+')) i++;
            string t = s.Substring(st, i - st);
            if (t.Length == 0) throw new FormatException("JSON: unexpected character '" + s[st] + "' at " + st);
            long l;
            if (t.IndexOfAny(new[] { '.', 'e', 'E' }) < 0 && long.TryParse(t, NumberStyles.Integer, CultureInfo.InvariantCulture, out l)) return l;
            return double.Parse(t, NumberStyles.Float, CultureInfo.InvariantCulture);
        }

        // ---------------------------------------------------------------- writing (stable, readable)
        public static string Write(object v, bool pretty = true)
        {
            StringBuilder b = new StringBuilder();
            W(b, v, pretty, 0);
            if (pretty) b.Append('\n');
            return b.ToString();
        }

        static void Ind(StringBuilder b, bool pretty, int n)
        {
            if (!pretty) return;
            b.Append('\n');
            b.Append(' ', n * 2);
        }

        static void W(StringBuilder b, object v, bool pretty, int n)
        {
            if (v == null) { b.Append("null"); return; }
            if (v is string) { Esc(b, (string)v); return; }
            if (v is bool) { b.Append(((bool)v) ? "true" : "false"); return; }
            if (v is int || v is long) { b.Append(Convert.ToString(v, CultureInfo.InvariantCulture)); return; }
            if (v is double || v is float)
            {
                double d = Convert.ToDouble(v, CultureInfo.InvariantCulture);
                if (Math.Abs(d - Math.Round(d)) < 1e-9 && Math.Abs(d) < 9e15) b.Append(((long)Math.Round(d)).ToString(CultureInfo.InvariantCulture));
                else b.Append(d.ToString("R", CultureInfo.InvariantCulture));
                return;
            }
            JsonObject jo = v as JsonObject;
            if (jo != null)
            {
                b.Append('{');
                int k = 0;
                foreach (string key in jo.Order)
                {
                    if (!jo.ContainsKey(key)) continue;
                    if (k++ > 0) b.Append(',');
                    Ind(b, pretty, n + 1);
                    Esc(b, key);
                    b.Append(pretty ? ": " : ":");
                    W(b, jo[key], pretty, n + 1);
                }
                if (k > 0) Ind(b, pretty, n);
                b.Append('}');
                return;
            }
            System.Collections.IDictionary dict = v as System.Collections.IDictionary;
            if (dict != null)
            {
                b.Append('{');
                int k = 0;
                foreach (System.Collections.DictionaryEntry e in dict)
                {
                    if (k++ > 0) b.Append(',');
                    Ind(b, pretty, n + 1);
                    Esc(b, Convert.ToString(e.Key, CultureInfo.InvariantCulture));
                    b.Append(pretty ? ": " : ":");
                    W(b, e.Value, pretty, n + 1);
                }
                if (k > 0) Ind(b, pretty, n);
                b.Append('}');
                return;
            }
            System.Collections.IEnumerable en = v as System.Collections.IEnumerable;
            if (en != null)
            {
                b.Append('[');
                int k = 0;
                foreach (object x in en)
                {
                    if (k++ > 0) b.Append(',');
                    Ind(b, pretty, n + 1);
                    W(b, x, pretty, n + 1);
                }
                if (k > 0) Ind(b, pretty, n);
                b.Append(']');
                return;
            }
            Esc(b, Convert.ToString(v, CultureInfo.InvariantCulture));
        }

        static void Esc(StringBuilder b, string s)
        {
            b.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': b.Append("\\\""); break;
                    case '\\': b.Append("\\\\"); break;
                    case '\n': b.Append("\\n"); break;
                    case '\r': b.Append("\\r"); break;
                    case '\t': b.Append("\\t"); break;
                    default:
                        if (c < 0x20) b.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                        else b.Append(c);
                        break;
                }
            }
            b.Append('"');
        }
    }
}
