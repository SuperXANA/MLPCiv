# Equus installation and runtime verification

Prepared November 2, 2026; revised November 22, 2026 for the second atlas.
This integration preserves the regional atlas in
[`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83)
as Equestria "Known World", and adds Equestria "Expanded", traced from the
"Equestria... and Beyond" world picture. One map option chooses between them.
`PrivateMaps/Equus.py` is the installed script. The integration branch is an
overlay for an existing MLP Civilization is Magic installation, not a complete
mod distribution.

## Install

1. Close Civilization IV: Beyond the Sword before changing Python files.
2. Find the actual mod directory used by the Windows game, such as
   `Beyond the Sword/Mods/MLP Civilization is Magic`. Confirm it contains the
   mod's existing `Assets` and `PrivateMaps` directories.
3. Copy this branch's **`PrivateMaps/Equus.py`** to
   **`<mod>/PrivateMaps/Equus.py`**. Copy that file only; preserve the other maps
   and the existing installed mod. Do not replace the installation with this
   sparse development branch. If Equus is already present, keep its backup
   outside the game's map search directories.
4. Restart BtS, load MLP Civilization is Magic, and open Single Player → Custom
   Game. Select **Equus** in the map list. The expected map options are
   World Wrap (Flat/Cylinder/Toroid), Atlas variation
   (Subtle/Standard/Lively) and Alternative Universe Expansions
   (Equestria "Known World"/Equestria "Expanded"); their defaults are Flat,
   Standard and Equestria "Known World". The game counts a script's options
   when it starts, so a third option appears only after BtS is restarted.

The original `PyEquusMapCreation` branch and the source
`PyEquusMapCreation-ChatGPT` branch are separate from this integration. There is
one canonical installed Equus script on the integration branch; the old root
`Equus.py` location is removed there to avoid maintaining competing copies.

If Equus is absent from Custom Game, first check the loaded mod, the exact
`PrivateMaps/Equus.py` path, and that the filename is not `Equus.py.txt` or
inside an extra archive directory. Restart the game after correcting it. Check
the Python error log for an import or syntax failure before treating map
selection as verified. Preserve unrelated maps during troubleshooting.

## Enable diagnostics

Diagnostics are **off by default**. With BtS closed, change this single setting
near the top of the installed `PrivateMaps/Equus.py`:

```python
EQUUS_DIAGNOSTICS = True
```

In the **Windows account/profile running BtS**, open its active
`CivilizationIV.ini` and set:

```ini
LoggingEnabled = 1
```

For an interactive debugging session, `HidePythonExceptions = 0` also makes
Python failures visible in the game. It is not the switch that enables Equus
diagnostics. Restart BtS after changing the INI or script.

Equus uses the game's existing Python output/error streams. Normal diagnostic
records have an `[Equus]` prefix; generation exceptions retain their traceback
and are re-raised to the game rather than converted into a successful result.
The expected files are:

| File | What to inspect |
| --- | --- |
| `PythonDbg.log` | Equus stage entries/completions, chosen options, actual grid dimensions, plot and terrain summaries, and feature summary |
| `PythonErr.log` | Significant map-generation failures and their traceback; the game's normal exception reporting may repeat the same failure |

The usual BtS profile location is
`%USERPROFILE%/Documents/My Games/Beyond the Sword/Logs/`. The actual Documents
folder may be redirected, and the game may use a different profile/INI path.
Locate the logs that change when **this Windows game session** runs. The Linux
controller's home directory is not the Windows game's log location. Confirm
the native output routing on the first run instead of assuming a missing file
means that generation never ran.

The logging route follows AdvCiv's existing
[`CvUtil.RedirectDebug` and `CvUtil.RedirectError`](https://github.com/f1rpo/AdvCiv/blob/1951051b59405b7c39e9b0e6ab877eff597e0bd2/Assets/Python/CvUtil.py#L126),
which send Python stream writes to `CyPythonMgr`'s debug and error channels.
The stream setup and actual file output still need verification in the target
installation.

The script does not create a new log file, choose a custom directory, set an
RNG seed, or consume random values for diagnostics. No extra map option is
added, so existing option indices retain their meanings. Logging is best
effort: an output failure must not change a generated map or replace its
original exception. Set `EQUUS_DIAGNOSTICS = False` and restart BtS to disable
these extra records; ordinary game exception reporting remains available.

Counts describe each script stage at the time it finishes. Plot and terrain
arrays precede subsequent DLL processing and map normalization; the feature
summary follows Equus's feature pass. They are not a promise that every count
will equal the final playable map after all game callbacks run.

## November 8, 2026 gameplay evidence

This evidence was recorded with the Known World only revision of the script.
In the two-world revisions the Known World produces the same plot, terrain and
feature arrays and the same random-number trace as that script in the offline
harnesses ([source validation](Equus_Source_Validation.md)), but the Known
World of those revisions has not itself been generated in Civilization IV:
every row below is NOT RUN for it. The Expanded world's evidence follows the
table.

| Runtime check | Status | Evidence and scope |
| --- | --- | --- |
| Basic in-game generation | **PASS (one documented run)** | The [screenshot](https://github.com/SuperXANA/MLPCiv/blob/fa4ef9cf62814c3ef8151d99924c87aac9b89b18/docs/equus.png) shows the Civ IV map at turn 0 (4000 BC), with a selected unit, terrain, coastline, and minimap. The [gameplay commit](https://github.com/SuperXANA/MLPCiv/commit/fa4ef9cf62814c3ef8151d99924c87aac9b89b18) identifies it as a successful Equus test. |
| First attempt and visible errors | **REPORTED** | The playtester reported that the first random game generated successfully and displayed no error messages. |
| Custom Game discovery and selection | **NOT RUN** | A separate menu check has yet to be documented. |
| Comprehensive geography and starting positions | **NOT RUN** | The screenshot captures one local view and a minimap. The atlas checklist below still needs a full review. |
| Map sizes, wrap, variation, and sea level | **NOT RUN** | The settings and seed for the pictured run were unrecorded. |
| Diagnostic callbacks and native log collection | **NOT RUN** | The installed script hash, DLL identity, diagnostic setting, and Windows Python logs were unrecorded. |
| Same-seed diagnostics on/off comparison | **NOT RUN** | The offline equivalence results are recorded in [source validation](Equus_Source_Validation.md). |
| Save/reload and subsequent turn | **NOT RUN** | A save, reload, and turn advance still need to be captured. |

## November 22, 2026 gameplay evidence: Equestria "Expanded"

Reported by the playtester for commit
[`0ccf816`](https://github.com/SuperXANA/MLPCiv/commit/0ccf8161a782cef84f34ce18dd528e7947a2f50b),
the first two-world revision, on a Windows test machine running the mod.

| Runtime check | Status | Evidence and scope |
| --- | --- | --- |
| Expanded world, basic generation | **PASS (one reported run)** | The playtester reported that the Expanded configuration built successfully, and supplied a screenshot of turn 0 (4000 BC) with a selected unit, terrain, rivers, a sixteen-player scoreboard and the whole-world minimap. The screenshot is not stored in this repository. World size, wrap, variation, sea level and seed were not recorded |
| Geography | **ONE FINDING** | The sea down the middle of the map was "extremely compacted". Measured in the offline harness for that commit, open water beside Griffonstone on a Huge map was three to seven plots across. The playtester asked for one or two more plots on each side |
| AI auto-play | **STARTED, NO RESULT RECORDED** | The playtester started AI auto-play on the map. No outcome has been reported |
| Everything else in the table above | **NOT RUN** | Third-option discovery in Custom Game is implied by the run but was not separately described |

The next revision answers the finding with `_X_SEA_ROOM`, which parts the
Celestial Sea's shores by `.015` of the map's width on each side: nearly two
plots a side on Huge, and about four more plots of open water in the harness.
**That revision has not been generated in Civilization IV yet.** When it is,
compare the minimap with `docs/equus_expanded_preview.png`, check that
Bermuldy and Trotaway Islands now stand in open water with a clear lane east
of them, and that Trottingham Bridge and the Griffonstone trestle still join
their shores.

## Runtime procedure for automated verification

This procedure must be run in Civilization IV. Standalone Python checks cannot
verify discovery in Custom Game, the embedded extension API, XML IDs, the
game's feature generator, starting positions, or saving/loading.

Before each run, record the integration commit, installed script hash, mod and
DLL build identity, world-size selection, wrap, variation, sea level, player
count, and seed if the test setup exposes it. Record whether diagnostics are
enabled. Archive the logs before another launch can replace them. For scripted collection over SSH, copy the Windows
game profile's logs to a per-run directory on the controller after generation.
Keep successful and failed runs with their settings and screenshots.

1. **Discovery and a first generation.** Select Equus in Custom Game. Start a
   fresh Standard game with Flat wrap, Standard variation, and normal sea
   level, once for each world. Confirm that the game reaches a playable first
   turn. Check the logs
   for entry and successful completion of the plot, terrain, and feature
   callbacks, matching dimensions and array sizes, and no Equus traceback.
   An entry without a completion identifies the stage to investigate. A menu
   listing alone is not a successful-generation result.
2. **Geography, Known World.** Use WorldBuilder or a fully revealed diagnostic
   view and keep an overview screenshot. Check the northern snow belt and
   Crystal basin;
   central Equestria and the Ponyville valley between the Unicorn and Foal
   ranges; the Crystal Mountain passes; western desert/Badlands belts;
   Everfree and wetter southern/eastern woods; eastern Griffonstone and Dragon
   Coast; their separating strait; southern Storm Realm; and offshore Mount
   Aris and small islands. Check that the atlas is not vertically reversed,
   that the southern sea ice and cooler Basalt Beach region are plausible,
   and that major land/water divisions survive the chosen resolution. Tiny
   details can be abstracted on small maps. Inspect starting positions and
   connections for practical playability as well as visual resemblance.

   **Geography, Expanded.** Compare an overview with the world picture and
   with `docs/equus_expanded_preview.png` (a harness rendering; the game's own
   fractals will place forests and jungles differently). Three mainlands:
   Equestria in the west, from the snowy Yak Range and Mt. Everhoof through
   the Appaloosan Mountains, San Palomino, Amarezonia's jungle and the
   Badlands to Froud Valley and the Bone Dry Desert; Ponyland, the Jewel
   Desert, Mt. Vehoovius, the open Fields of Forever, icy Antleria and, past
   the Sanchez Mountains and an isthmus, Horsetrailia with its outback; and
   Griffonstone, Saddle Arabia's desert, Zebrica's jungle, Abyssinia and the
   volcanic Dragon Lands. Between them the Celestial Sea, the Great Inland Sea
   with its Oranma strait, Bridle Bay and the Asparus Sea. Offshore: Mount
   Aris, Black Skull Island, the Storm King's Realm, the Galloppingos, the
   Monkey Dancing Islands. Frozen at both ends: pack ice along the top edge;
   Agarica, the Mysterious South and the Great Iceberg Barrier along the
   bottom, with an ice-free lane north of the barrier. Check both bridges: by
   default Trottingham Bridge (Equestria to Ponyland, far north) and the
   Griffonstone trestle (Ponyland to Griffonstone) are one-plot causeways that
   land units can cross; with `EXPANDED_BRIDGES_ARE_LAND = False` each is a
   strait. With causeways the Frozen North becomes an inland sea. The
   Celestial Sea is deliberately wider than the picture draws it
   (`_X_SEA_ROOM`), so Equestria's east and Griffonstone sit a plot or two
   farther apart than in the picture. Expect a little under
   three-fifths of the map to be land, roughly twice a Fractal map's share:
   the picture leaves little room for ocean, so a given size holds more
   territory than usual.
3. **Map sizes.** Generate a fresh game at each available size with default
   options, for each world. The script returns cells; the AdvCiv map path
   scales each axis by four when a script sets its own grid (`CvMap::reset`,
   advc.137). Compare the logged **actual** dimensions with these tables.
   Where the installed XML has different labels, match the world-size index.

   Equestria "Known World" (portrait, unchanged):

   | Index | Script label | Cells | Expected plots | Array entries |
   | --- | --- | --- | --- | ---: |
   | 0 | Duel | 7 × 8 | 28 × 32 | 896 |
   | 1 | Tiny | 10 × 10 | 40 × 40 | 1,600 |
   | 2 | Small | 12 × 13 | 48 × 52 | 2,496 |
   | 3 | Standard | 16 × 17 | 64 × 68 | 4,352 |
   | 4 | Large | 19 × 20 | 76 × 80 | 6,080 |
   | 5 | Huge | 24 × 26 | 96 × 104 | 9,984 |
   | 6 | XXL | 30 × 31 | 120 × 124 | 14,880 |

   Equestria "Expanded" (landscape; the picture is 1.5 : 1). The last column
   is what AdvCiv 1.14's `CIV4WorldInfo.xml` gives the same size on a script
   without a grid of its own, for comparison:

   | Index | Script label | Cells | Expected plots | Array entries | XML plots |
   | --- | --- | --- | --- | ---: | --- |
   | 0 | Duel | 9 × 6 | 36 × 24 | 864 | 36 × 26 |
   | 1 | Tiny | 12 × 8 | 48 × 32 | 1,536 | 46 × 34 |
   | 2 | Small | 16 × 11 | 64 × 44 | 2,816 | 60 × 44 |
   | 3 | Standard | 20 × 14 | 80 × 56 | 4,480 | 78 × 56 |
   | 4 | Large | 24 × 16 | 96 × 64 | 6,144 | 94 × 68 |
   | 5 | Huge | 30 × 21 | 120 × 84 | 10,080 | 120 × 84 |
   | 6 | XXL | 37 × 25 | 148 × 100 | 14,800 | 146 × 102 |

4. **Options and sea level.** At least on Duel, Standard, and the largest
   available size, try Subtle/Standard/Lively variation and Low/Normal/High sea
   level in fresh games. Exercise Flat, Cylinder, and Toroid wrap; inspect the
   corresponding map edges and confirm the intended X/Y wrapping. Cover all
   nine wrap/variation pairs on Standard if time permits. Expect familiar
   regional structure with seeded coastline, relief, and biome variation.
   Confirm the selected values in the logs. Changing game settings can change
   the RNG sequence; screenshots across unrelated seeds are a plausibility
   check, not an exact reproducibility test.
5. **Diagnostics comparison.** If the runtime harness can reproduce the same
   initial map RNG state and settings, compare a run with diagnostics off to
   one with diagnostics on. Maps should match. Do not reset or draw from the
   RNG just to print a seed. If the harness cannot reproduce the initial state,
   record this runtime comparison as pending; the source-level equivalence
   checks remain useful but do not substitute for the real game.
6. **Fresh-game save and reload.** From a newly generated Equus game, play or
   autoplay several turns, save under a new test filename, exit to desktop,
   restart the same installed mod/DLL/script, and load that save. Confirm the
   world dimensions, map/terrain/features, current turn, cities, and units are
   preserved; advance another turn and save again. Loading must use the
   dimensions stored in the save (`getGridSize([-1])` returns `[]`), not generate
   a replacement world. Inspect the new session's error log. Repeat on a small
   and a large map. This verifies saves created by these tests; no prior
   feature-branch save history is assumed.

Use this evidence record for each run:

| Item | Record |
| --- | --- |
| Commit / installed script hash / DLL identity | |
| World (Known World / Expanded) and, for Expanded, the bridge setting | |
| Size / actual width × height / options / sea level / seed if available | |
| Equus listed and selected | PASS / FAIL / NOT RUN |
| Generation reached playable turn | PASS / FAIL / NOT RUN |
| Diagnostics setting / native log collection / callback completion | Setting and PASS / FAIL / NOT RUN |
| Size and option checks for this configuration | PASS / FAIL / NOT RUN |
| Same-seed diagnostics comparison | PASS / FAIL / NOT RUN |
| Geographic overview and starting-position review | PASS / FAIL / NOT RUN |
| Log archive and screenshot filenames | |
| Fresh-game save/reload and subsequent turn | PASS / FAIL / NOT RUN |
| Error details / last completed stage | |

## Offline validation

[Equus source validation](Equus_Source_Validation.md) records the standalone
Python results. The harnesses use deterministic Civ API test doubles to check
dimensions, array sizes, options, output equivalence, and RNG call order.
