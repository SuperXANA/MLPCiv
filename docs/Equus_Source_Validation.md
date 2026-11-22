# Equus source validation

Offline results for the two-world script with sea room, recorded November 22,
2026. Earlier results (November 2) and gameplay evidence (November 8) describe
the Known World only revision; the first two-world revision
([`0ccf816`](https://github.com/SuperXANA/MLPCiv/commit/0ccf8161a782cef84f34ce18dd528e7947a2f50b))
was generated in the game once, before sea room existed.

## Source and scope

`PrivateMaps/Equus.py` holds two atlases, chosen with the third map option,
**Alternative Universe Expansions**:

* **Equestria "Known World"** (default) is the regional atlas of
  [`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83).
  Its tables, helpers, terrain rules and feature generator are untouched. Six
  top-level definitions changed so that a second atlas could exist beside it:
  `CvMapOptions` (one more row), `getDescription`, `getGridSize` (the size
  table now depends on the world) and the three generation callbacks (each
  gained one `if _expanded():` branch).
* **Equestria "Expanded"** is new: 46 shore tables (769 triples), 20 isles,
  5 lakes, 47 ranges, 15 passes, 76 named biome ovals, 6 sea lanes and 8 land
  links, traced from the "Equestria... and Beyond" world picture, with their
  own plot, terrain and feature code. Coasts were measured from the picture's
  pixels and then simplified to within about a third of a Huge plot; ranges
  and biomes were placed by eye against the picture. One departure from the
  picture is deliberate: `_X_SEA_ROOM` moves the Celestial Sea's two shores
  apart by `.015` of the map's width each, after the first in-game run found
  that sea too narrow for ships.

The pinned test fixture is byte-identical to that commit's original script:
Git blob SHA `395fa96ba5193b9483bc24cdfac8687fe4f9766d`.
The installed script's Git blob SHA is
`59f9f53bcf21684585310370be575744029dfc99`.

Facts about the engine were read from the
[SuperXANA/AdvCiv](https://github.com/SuperXANA/AdvCiv) fork at
`5970334b64a875b5cdb370c94fc9a98db4eacda6`: `CvMap::reset` asks the script for
its grid and its wrap in the same call, with custom options already readable,
and multiplies a script's cells by four; `CIV4WorldInfo.xml` puts Huge at
120 x 84 plots; `CIV4FeatureInfos.xml` allows forest on grass, plains and
tundra, jungle on grass and plains, and ice on water;
`CvMapGeneratorUtil.FeatureGenerator` calls the three per-plot methods that
both generators override.

## Results

| Check | Result | Evidence and scope |
| --- | --- | --- |
| Host suite, Python 3.13.18 | PASS — 20 tests | `python3 tests/check_equus.py` (19 without a 2.4 interpreter; the twentieth is skipped) |
| Known World preservation | PASS | Every original top-level definition has the same AST except the six named above; all other additions are the diagnostics or belong to the Expanded world |
| Known World output/RNG equivalence | PASS in test doubles — 23 configurations | Exact plot arrays, terrain arrays, feature states, callback return and complete RNG argument/result traces match the pinned original, with diagnostics off and on, with the third option present and absent. All seven sizes, all nine wrap/variation pairs on Duel, all nine sea-level/variation pairs on Standard. It draws none of the Expanded world's random numbers |
| Expanded generation | PASS in test doubles — 23 configurations | The same matrix: array sizes and value domains, untouched water terrain, diagnostics off/on identical, only its own RNG labels, land share between 45% and 72% |
| Expanded geography | PASS — 100 worlds | Fifty size/variation/sea-level/seed configurations, each with the bridges as causeways and as straits. Twenty-six named places are land and ten named seas are water; each mainland is one piece and can be crossed on foot without meeting a wall of peaks; causeways join their shores, or as straits leave three separate mainlands; Agarica, Mount Aris and the Storm King's Realm stay islands above Duel size; ships can reach every named sea but the Frozen North even with all pack ice treated as impassable |
| Expanded climate | PASS on Huge | Saddle Arabia, the Bone Dry Desert and Breezewood are desert; Antleria is snow; the Fields of Forever are grass; Zebrica and Amarezonia carry jungle; no jungle in Saddle Arabia; the southern rim is snow or tundra |
| Pack ice | PASS | Ice only on water, only within 4% of the top edge or beyond 84% south, never on a sea lane |
| Sea level and variation | PASS | Low, normal and high sea give strictly more to less land; Subtle and Lively differ from Standard |
| Sea room | PASS | On Huge, open water across the Celestial Sea lane at six latitudes beside Griffonstone averages 4.3 plots more than with `extra` set to 0 (8, 5, 3, 5, 7, 12 plots become 14, 9, 7, 10, 10, 16); the move never folds the picture and reverses exactly; an `extra` of 0 and an empty table give the same map; nothing moves north of latitude .165, so Trottingham Bridge is untouched |
| Table sanity | PASS | Shore latitudes strictly increase, west never exceeds east, ovals have positive radii, no ridge segment has zero length (it would divide by zero) |
| Dimensions/options | PASS | Both size tables, save-load sentinel, larger world-index fallback, three options with their labels and defaults, invalid stored-choice fallback to the Known World |
| Diagnostics, errors and logging | PASS in captured streams/test doubles | As before, now for both worlds: exact summaries, no warning/error output on normal runs, injected errors keep their exception object, broken output sinks leave generation unchanged |
| Python 2.4.6 execution | PASS — 42 pipelines | `python2.4 tests/check_python24.py` parses, imports and runs the script on a CPython 2.4.6 built from source: Known World baseline/legacy/off/on and Expanded off/on at all seven sizes |
| Python 2.4 against Python 3 | PASS — 14 maps | `EQUUS_PYTHON24=... python3 tests/check_equus.py`: a checksum over each map's plots, terrain, features and RNG results is identical under both interpreters, for both worlds at all seven sizes. The host harness also gives `/` its Python 2.4 meaning and counts integer/integer divisions in the script: none occur |
| Python 2.4 speed | Measured | An XXL Expanded world took about 0.4 s of CPU for its three passes; the Known World XXL about 0.25 s |
| Wider geography sweep | PASS — 2,016 worlds | Run once during development, not part of the suite: all seven sizes, three variations, three sea levels, sixteen seeds, both bridge settings |
| Civilization IV generation | **NOT RUN for this revision** | The [November 8 screenshot](https://github.com/SuperXANA/MLPCiv/blob/fa4ef9cf62814c3ef8151d99924c87aac9b89b18/docs/equus.png) shows the Known World only revision. The playtester generated the Expanded world of `0ccf816` once on November 22 ([runtime evidence](Equus_Runtime_Verification.md)). Neither world of this revision, with sea room, has been generated in the game |

Both harnesses supply deterministic test doubles for `CvPythonExtensions` and
`CvMapGeneratorUtil.FeatureGenerator`. Their RNG is a small repeatable stand-in,
not Civ's RNG, and their forest and jungle "fractals" are a simple pattern, so
tree cover in a harness map only shows where trees may grow. These checks
establish the script's own logic and its Python language compatibility for the
tested inputs, not full engine compatibility. The Python 3 harness has
host-only dependencies from its standard library; only `PrivateMaps/Equus.py`
is installed into the game.

The standalone 2.4.6 result does not verify the game's exact embedded Python
patch level or Windows extension bindings. The script uses Python 2.4 syntax
and existing built-ins; its diagnostic imports are limited to `sys` and
`traceback` when enabled. The Expanded world calls nothing in the extension
API that the Known World, already seen running in the game, does not call.

## Known limits of the Expanded world

* Trees, rivers, lakes added by the DLL, resources, starting positions and
  normalization are the game's own and are unseen here.
* About 57% of the map is land at normal sea level, where a Fractal map has
  roughly 30%. Low sea level raises that to about two-thirds. A given world size
  therefore holds about twice the usual territory.
* Sea room is a fraction of the map's width, so it adds nearly two plots a
  side on Huge but about half a plot on Duel, where the sea lanes still do
  most of the work. It widens seas that run north-south only.
* With the default causeways the Frozen North is an inland sea, and all three
  mainlands form a single land area. Set `EXPANDED_BRIDGES_ARE_LAND = False`
  for three mainlands that need boats.
* On a Duel grid small islands may lean against the nearest shore, and islets
  that sit in a sea lane are dropped in favour of the lane.
* Place names in the table comments were read from a 1,500-pixel picture.
  Several small ones are best guesses.

## Runtime follow-up

See [Equus runtime verification](Equus_Runtime_Verification.md) for the
in-game procedure, the November 22 evidence, the expected dimensions of both
worlds and the Expanded geography checklist. Generation of both worlds, native
diagnostic log collection, starting-position review, size and option coverage,
and save/reload all remain **NOT RUN** for this revision.
