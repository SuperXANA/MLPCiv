# Equus installation and runtime verification

Prepared November 2, 2026. This integration preserves the regional atlas in
[`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83).
The [installation integration](https://github.com/SuperXANA/MLPCiv/tree/fa4ef9cf62814c3ef8151d99924c87aac9b89b18) supplies
`PrivateMaps/Equus.py` as an overlay for an existing MLP Civilization is Magic
installation. The creation branch retains the original root-level `Equus.py`.
The install and diagnostic instructions below apply to the integration script.

## Install

1. Close Civilization IV: Beyond the Sword before changing Python files.
2. Find the actual mod directory used by the Windows game, such as
   `Beyond the Sword/Mods/MLP Civilization is Magic`. Confirm it contains the
   mod's existing `Assets` and `PrivateMaps` directories.
3. Copy the installation branch's **`PrivateMaps/Equus.py`** to
   **`<mod>/PrivateMaps/Equus.py`**. Copy that file only; preserve the other maps
   and the existing installed mod. Do not replace the installation with this
   sparse development branch. If Equus is already present, keep its backup
   outside the game's map search directories.
4. Restart BtS, load MLP Civilization is Magic, and open Single Player → Custom
   Game. Select **Equus** in the map list. The expected map options remain
   World Wrap (Flat/Cylinder/Toroid) and Atlas variation
   (Subtle/Standard/Lively); their defaults are Flat and Standard.

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

## Runtime procedure for automated verification

This procedure must be run in Civilization IV. Standalone Python checks cannot
verify discovery in Custom Game, the embedded extension API, XML IDs, the
game's feature generator, starting positions, or saving/loading.

Before each run, record the integration commit, installed script hash, mod and
DLL build identity, world-size selection, wrap, variation, sea level, player
count, and seed if the test setup exposes it. Record whether diagnostics are enabled. Archive the logs before another
launch can replace them. For scripted collection over SSH, copy the Windows
game profile's logs to a per-run directory on the controller after generation.
Keep successful and failed runs with their settings and screenshots.

1. **Discovery and a first generation.** Select Equus in Custom Game. Start a
   fresh Standard game with Flat wrap, Standard variation, and normal sea
   level. Confirm that the game reaches a playable first turn. Check the logs
   for entry and successful completion of the plot, terrain, and feature
   callbacks, matching dimensions and array sizes, and no Equus traceback.
   An entry without a completion identifies the stage to investigate. A menu
   listing alone is not a successful-generation result.
2. **Geography.** Use WorldBuilder or a fully revealed diagnostic view and keep
   an overview screenshot. Check the northern snow belt and Crystal basin;
   central Equestria and the Ponyville valley between the Unicorn and Foal
   ranges; the Crystal Mountain passes; western desert/Badlands belts;
   Everfree and wetter southern/eastern woods; eastern Griffonstone and Dragon
   Coast; their separating strait; southern Storm Realm; and offshore Mount
   Aris and small islands. Check that the atlas is not vertically reversed,
   that the southern sea ice and cooler Basalt Beach region are plausible,
   and that major land/water divisions survive the chosen resolution. Tiny
   details can be abstracted on small maps. Inspect starting positions and
   connections for practical playability as well as visual resemblance.
3. **Map sizes.** Generate a fresh game at each available size with default
   options. The script returns cells; the AdvCiv map path scales each axis by
   four. Compare the logged **actual** dimensions with this table. Where the
   installed XML has different labels, match the world-size index.

   | Index | Script label | Cells | Expected plots | Array entries |
   | --- | --- | --- | --- | ---: |
   | 0 | Duel | 7 × 8 | 28 × 32 | 896 |
   | 1 | Tiny | 10 × 10 | 40 × 40 | 1,600 |
   | 2 | Small | 12 × 13 | 48 × 52 | 2,496 |
   | 3 | Standard | 16 × 17 | 64 × 68 | 4,352 |
   | 4 | Large | 19 × 20 | 76 × 80 | 6,080 |
   | 5 | Huge | 24 × 26 | 96 × 104 | 9,984 |
   | 6 | XXL | 30 × 31 | 120 × 124 | 14,880 |

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
