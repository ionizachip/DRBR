# gmlsim - run decompiled GameMaker (GML 2.3+) code without the game

Pure Python 3 (no dependencies). A hand-written lexer + recursive-descent parser compiles GML to Python
closures; a `Sim` object provides instances, events, rooms, alarms, input, files/INI and a plug-in builtin
registry. The point is **faithful errors**: reading an unset variable, a dead instance id, an unmocked API, a
wrong-typed operand, an out-of-range array index ... all raise `GMError` with a GameMaker-style message, the
code entry name, line number, event and GML call stack.

```
cd /home/claude/gmlsim
python3 -m gmlsim.selftest            # 576 assertions, <1 s   (add -v for timings, --real for corpus parse)
python3 -m gmlsim.parsecheck DIR...   # parse + compile every .gml in DIR (reports failures)
python3 examples/scr_damage_demo.py   # real scr_damage across several script files, mocked globals
```
(`python3 -I` ignores the working directory and `PYTHONPATH`; run from the repo dir or put it on `PYTHONPATH`.)

## Layout

| file | role |
|---|---|
| `lexer.py`, `parser.py` | tokenizer / parser -> tuple AST (`#macro`, `enum`, `$"template"`, `[| ? # @ $` accessors, `try/catch/finally`, `static`, `constructor`/inheritance, `with`, `switch`, `new`, `??`, `div/mod/and/or/xor/not`, `#RRGGBB`, `$FF`, `0xFF`, `<>`, `:=` ...) |
| `compiler.py` | AST -> closures; statement closures return `None`/BREAK/CONTINUE/RETURN codes (no exceptions for control flow); per-statement line annotation of errors; global compile cache keyed by `(entry, source)` |
| `rt.py` | frames, field access (`get_field`/`set_field`), array copy-on-write, calls, constructors |
| `ops.py` | operator semantics (type errors, epsilon `==`, truthiness, div/mod, int64 bit ops) |
| `values.py` | `GMArray` (COW), `GMStruct`, `GMInstance`, `GMFunc`, `GMMethod`, formatting (`string()`) |
| `sim.py` | `Sim`: loader, objects/parents, instances, event dispatch, alarms, rooms, stepping, snapshots |
| `fs.py` | sandbox directory (real files) + write-fault injection (`Fault`) |
| `lib_core.py` `lib_engine.py` `lib_io.py` `lib_input.py` `lib_mocks.py` `lib_extra.py` | builtin libraries (math, string, array, struct, ds_*, json, instance/event/room, ini/file/ossafe/date, keyboard, recording draw/audio/surface/layer/... mocks) |
| `selftest.py`, `parsecheck.py` | tests / corpus parse tool |
| `testdata/` | tiny UTMT-named sample files used by the self-test |

## Writing a test

```python
from gmlsim import Sim, GMError

sim = Sim(seed=1)                                   # sandbox dir auto-created lazily, removed at exit
sim.load_dir("/path/CodeEntries")                   # gml_Object_<obj>_<Event>_<n>.gml, gml_GlobalScript_<name>.gml,
                                                    # gml_RoomCC_*, gml_Room_*_Create; merged-style names also accepted
                                                    # kinds=("scripts",) / match="regex" to load a subset
sim.define_object("obj_player", parent="obj_actor", persistent=False)   # parents / persistence
sim.define_globals(hp=[0, 90, 110], chapter=1)                           # python lists/dicts -> GML arrays/structs
sim.define_event("obj_player", "Step", 0, "x += 1;")                    # inline GML as an event
sim.define_script("scr_double", "function scr_double(a) { return a * 2; }")

pid = sim.create("obj_player", 10, 20, hp=3)        # runs PreCreate + Create; returns instance id (>= 100000)
sim.press("Z", frame=2); sim.hold("right", 3, start=1)   # scripted input by absolute frame
sim.step(10)                                        # Begin Step -> Alarms -> Key events -> Step -> End Step
                                                    # -> (room change) -> Draw Begin/Draw/Draw End/GUI...
assert sim.get(pid, "x") == 20
assert sim.eval("scr_double(21)") == 42             # raw GML value; sim.py(v) converts arrays/structs to list/dict
sim.run("global.flag = true; with (obj_player) hp -= 1;")           # run statements (self_obj=pid to choose self)
snap = sim.snapshot(); ...; sim.restore(snap)       # deep copy of all state incl. files, RNG, statics, ds_*

try:
    sim.step()
except GMError as e:                                # e.message, e.kind, e.entry, e.line, e.event, e.frame, e.stack
    print(e)
```

Rooms: `sim.define_room("room_a", instances=[("obj_player", 10, 20, {"hp": 3})], creation_code="...")`,
`sim.start("room_a")`, then `room_goto(room_b)` in GML (or `sim.goto_room("room_b")`) takes effect at the step
boundary. Instance spec tuples are `(obj, x, y, vars_dict, roomcc_number)`; if `RoomCC_<room>_<n>_PreCreate`
was loaded it runs before Create.

Global script top-level (non-function) statements do not run at load; call `sim.run_global_inits()`.

### Mocking

```python
sim.mock("snd_play", lambda s, *a: 1)                    # fn(sim, *args) -> GML value
sim.mock("whoami", lambda s, f, *a: f.self.id, frame=True)  # fn(sim, frame, *args); frame.self / frame.other
sim.mock("get_score", 12)                                # non-callable => constant result
sim.mock("x", fn, record=True)                           # also logs calls
sim.mock_value("some_builtin_var", 5)                    # builtin *variable* (e.g. `os_type`); may be callable(sim)
sim.define_const("MY_CONST", 3); sim.define_asset("spr_x")
sim.calls("draw_text")   # -> [Call(frame, name, args)]   (all draw_*/audio/surface/layer/... stubs record into sim.log)
sim.record_calls = False # silence logging for perf runs
```
A `sim.mock(name)` overrides loaded scripts of the same name; loading a script named like a *default* builtin
(e.g. `ossafe_ini_open`, `instance_create`) replaces that builtin with the real script. Anything unknown raises
`GMError("undefined function X")` (with a did-you-mean hint) so unmocked APIs show up immediately.
Python exceptions raised inside a builtin because of bad args (TypeError etc.) are reported as
`GMError("name(): TypeError: ...", kind="builtin_args")`.

### Files / INI / fault injection

`ini_*`, `file_*`, `file_text_*`, `directory_*`, `ossafe_*` operate on **real files** under `sim.sandbox`
(path escapes with `..` raise `sandbox`). `ini_open` loads/parses the file, `ini_close` writes the whole file
(strings `key="v"`, reals `key=1.000000`). Every write goes through `sim.fs.write`, so faults apply to
`ini_close`, `file_text_close`, `file_copy`:

```python
from gmlsim import Fault
sim.inject_write_fault(Fault.interrupt(12), "save.ini")  # first 12 bytes written, then SimCrash (process killed)
sim.inject_write_fault(Fault.truncate(10)) | Fault.zero() | Fault.corrupt(seed, nbytes) | Fault.garbage(b"..")
| Fault.fail() (IOError -> GMError, file untouched) | Fault.custom(lambda path, data: new_bytes)
```
Faults are one-shot by default (`once=False` to keep), match by relative-path substring or callable.
`SimCrash` is not a `GMError`, so GML `try/catch` cannot swallow it. `sim.fs.write_log` lists every write.

## Semantics implemented (all covered by `selftest.py`)

* Values: reals (Python int/float), strings, bools, `undefined`, arrays, structs, instance ids (ints >= 100000),
  object indices (small ints), methods. `noone=-4 all=-3 self=-1 other=-2 global=-5`.
* **Arrays are copy-on-write values**: assignment / argument passing / return / storing into arrays or structs
  share storage, and the first `a[i] = v` through any holder copies. Nested `a[i][j] = v`, legacy `a[i,j]`,
  growth past the end pads with `0`, auto-creation of unset array variables.
* Variable resolution: `var` locals (textual order, like GML) -> `static` -> instance (`self`) variables ->
  macros/enums/objects/assets/scripts/builtins -> builtin variables. `global.x`, `globalvar`.
* `with(obj | id | all | struct | noone)` over a snapshot of instances, sets `self`/`other`, objects include
  children; `break/continue/return` inside `with`; destroyed instances are skipped.
* Event dispatch with parent chain, `event_inherited`, `event_user(n)` (= `Other_(10+n)`), `event_perform`,
  Create/PreCreate/Destroy/CleanUp/Alarm n/Step 0,1,2/Draw 0,64,72-75/KeyPress/Keyboard/KeyRelease/Other.
* Alarms (`alarm[n]`, decrement per step, fire at 0, reset to -1), persistence, Room End / CleanUp /
  Room Start ordering, `room_goto*`, `room_restart`.
* Functions: default args (applied for missing or `undefined`), `argument[i]`/`argument0`/`argument_count`,
  methods bound to `self`, struct-literal methods, constructors (`new`, `: Parent(args) constructor`, `static`),
  `instanceof`, recursion with a depth limit (`sim.max_depth`, default 400), `script_execute(_ext)`.
* `try/catch/finally/throw` (internal errors are catchable; `e` is a struct with `message`, `longMessage`,
  `script`, `line`, `stacktrace`, `kind`).

### Error semantics (all raise `GMError`; `e.kind` in brackets)

| situation | message |
|---|---|
| unset instance/self var [`var_not_set`] | `Variable obj_name.var not set before reading it` (`struct.var` for struct self) |
| unset global [`global_not_set`] | `global variable name 'x' index (100123) not set before reading it` |
| unset/uninitialised local [`local_not_set`] | `local variable 'x' not set before reading it` |
| `obj.v` / `id.v` / `noone.v` with no live instance [`no_instance`] | `Unable to find instance for object index N` (also for destroyed ids and writes) |
| unknown function/script [`undefined_function`] | `undefined function name (did you mean ...?)` |
| calling a non-function [`not_callable`] | `Unable to call X: it is not a function/method` |
| array index out of range / negative, read or negative write [`array_oob`] | `Array index out of range: index [5] not in [0..3)` |
| indexing a non-array [`type`] | `Variable is not an array (it is number)` |
| `"a" + 1`, `"a" * 2`, `-"a"`, `undefined + 1`, `"a" < 1` [`type`] | `Unable to add string "a" and number ...` / `Unable to convert ... to a number` / `Unable to compare ...` |
| `if ("str")` / `if (undefined)` [`type`] | `Unable to convert ... to a boolean` |
| `/ 0`, `div 0`, `mod 0` [`div0`] | `Division by zero` (`sim.set_div_zero("inf")` for IEEE results) |
| field of undefined/string [`type`] | `Unable to read field 'x' of undefined` |
| bad `ds_*` handle / index [`ds`, `ds_oob`], bad file handle [`file`], ini without `ini_open` [`ini`] | descriptive |
| unknown object / room [`no_object`, `no_room`] | `Unable to find object X` / `Room X is not defined in the sim` |
| runaway recursion / loops [`stack`, `loop_limit`] | `Stack overflow ...` / `Infinite loop suspected` (`gmlsim.compiler.LOOP_LIMIT`, 2,000,000) |
| `show_error(msg, true)` [`show_error`], uncaught `throw` [`throw`] | the message |

Each error carries `entry` (e.g. `gml_Object_obj_x_Step_0`), `line`, `event` (`obj_x.Step_0`), `frame`
(sim frame number, from `Sim.step`) and `stack` (GML function names, innermost first).

### Builtins

math (`floor ceil round(banker's) abs min max clamp sign sqrt power lerp ...`, trig, `lengthdir_*`,
`point_*`, colour helpers), seedable RNG (`random irandom *_range choose random_set_seed randomize`), strings
(`string string_length string_copy string_char_at string_pos string_replace(_all) string_delete string_insert
string_upper/lower string_format string_digits string_count string_hash_to_newline ord chr real ...`), arrays
(`array_* incl. push pop delete insert copy sort contains get_index find_index foreach map filter reduce`),
`variable_struct_* / variable_instance_* / variable_global_*`, `ds_list/map/grid/priority`, `json_*`, `instance_*`,
`object_*`, `event_*`, `alarm_*`, `room_*`, `script_execute`, `method`, `is_*`, `typeof`, ini/file/ossafe/date/
`get_timer`/`current_time`, keyboard (scripted), and ~480 recording stubs (of ~850 builtins) for draw/gpu/shader/surface/audio/
layer/camera/view/window/path/mp_grid/vertex/video/platform SDK APIs (see `lib_mocks.py`, `lib_extra.py`).
`DEFAULT_BUILTINS` in `registry.py` is the plug-in registry: add your own with `@builtin("name", frame=False)`.

## Known deviations from real GameMaker

* **Division by zero** raises by default (my best understanding of the runtime); use `set_div_zero("inf")`.
* `string(true)` is `"true"`; `string(real)` prints at most 2 decimals (trailing zeros trimmed).
* Relational `<` on two strings is allowed (lexicographic); mixed string/number raises. `==` between
  unequal types is `false` (no error). Real `==` uses a fixed 1e-5 epsilon (`math_set_epsilon` unsupported).
* `array_push/pop/insert/delete/copy/resize/sort` mutate the shared storage **in place** (they do not trigger
  copy-on-write for aliases), while indexed writes `a[i] = v` are true COW. Unsure what the real runtime does for
  aliases here. Each pass of an array into a function/variable marks it "shared" so the next indexed write copies
  once (observably identical to refcounted COW, but O(n) for big arrays in hot loops).
* Instance ids are plain integers (`typeof(id)` is `"number"`, not `"ref"`). Variable *names* of unset reads use
  the object name; real GM appends `(id, -2147483648)`-style suffixes and a "FATAL ERROR in action number ..."
  banner, which are not reproduced.
* No physics/automatic motion (`speed/hspeed/gravity` are plain variables), no sprite animation / Animation End,
  no collision/mouse/gesture events (call `sim.run_event(inst, "Collision", "obj_x")` yourself); `place_meeting`
  & co. are recording stubs returning false/noone. Instance iteration order is creation order; Draw order is
  depth-descending then creation order. Room change happens after End Step, before Draw. Room persistence flags
  and views/layers are not modelled; `instance_create` of unknown objects raises.
* `var` scoping is textual (a name becomes local after its `var` statement). GML has no closures and neither
  does the sim (anonymous functions do not see the creator's locals; they are bound to the creator's `self`).
* Constructors may be called without `new` (behaves like a plain function, as in GM); `static` variables live per
  function; struct statics are visible via the constructor chain only for reads.
* Assignment `=` is only a statement (`if (a = b)` as comparison is not supported); `begin/end` aliases are not.
* `ini_*` file format: strings quoted, reals `%f`; `ini_read_real` of a non-numeric value returns the default.
  `ds_map` iteration is insertion order (GM's is hash order). `random*` values differ from GM's generator.
* Top-level statements of global scripts are deferred to `run_global_inits()`; macros are re-evaluated per use.
* Numeric model: Python int/float; `+ - *` on ints are arbitrary precision (no 64-bit wrap) except bit ops
  (int64). `string_length`/`ord` operate on Unicode code points.
* `try/catch` catches `GMError` only; `SimCrash` (fault injection) and Python bugs are not catchable from GML.
* Snapshots deep-copy sim state (instances, globals, ds_*, statics, rng, input queue, pending room, sandbox
  files); they do **not** restore Python-side state captured by your own mock closures.
