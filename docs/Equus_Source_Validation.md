# Equus source validation

Offline results for the two-world script with climates, recorded November 28,
2026. Earlier results (November 2) and gameplay evidence (November 8) describe
the Known World only revision. The two earlier two-world revisions were each
generated in the game by the playtester:
[`0ccf816`](https://github.com/SuperXANA/MLPCiv/commit/0ccf8161a782cef84f34ce18dd528e7947a2f50b)
before sea room existed, and
[`ad619b3`](https://github.com/SuperXANA/MLPCiv/commit/ad619b3d957f24d69f68f0f6a578af1a9286a389)
with the Celestial Sea widened. This revision has not been.

## Source and scope

`PrivateMaps/Equus.py` holds two atlases, chosen with the third map option,
**Alternative Universe Expansions**:

* **Equestria "Known World"** (default) is the regional atlas of
  [`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83).
  Its tables, helpers, terrain rules and feature generator are untouched.
  Seven top-level definitions changed: `CvMapOptions` (one more row),
  `getDescription`, `getGridSize` (the size table now depends on the world),
  `isClimateMap` (now `True`) and the three generation callbacks. Each
  callback gained one `if _expanded():` branch and one climate branch that is
  not taken under Temperate, so a Temperate Known World runs the original
  code.
* **Equestria "Expanded"** is new: 46 shore tables (769 triples), 20 isles,
  5 lakes, 47 ranges, 15 passes, 76 named biome ovals, 6 sea lanes and 8 land
  links, traced from the "Equestria... and Beyond" world picture, with their
  own plot, terrain and feature code. Coasts were measured from the picture's
  pixels and then simplified to within about a third of a Huge plot; ranges
  and biomes were placed by eye against the picture. One departure from the
  picture is deliberate: `_X_SEA_ROOM` moves the shores of the Celestial Sea,
  and of the Great Inland Sea with the channel that runs on from it, apart by
  `.015` of the map's width each, and pushes the land in from the western and
  eastern rims by `.013`, after in-game runs found those waters too narrow
  for ships.
* **Climates** are new in both worlds. `_Climate` turns the chosen climate's
  XML numbers, less the Temperate entry's, into distances; `_Biomes` and
  `_grown` move the rim of each biome oval by them; the frost-line constants
  in the terrain rules shift by them; `_uplift` raises land beside existing
  hills and peaks for Rocky, and `_way_through` stops it closing a road. The Known World has its own copy of the terrain
  rules with those shifts (`_known_climate_terrain`) and its own feature
  generator (`KnownClimateFeatureGenerator`), used only when the climate is
  not Temperate.

The pinned test fixture is byte-identical to that commit's original script:
Git blob SHA `395fa96ba5193b9483bc24cdfac8687fe4f9766d`.
The installed script's Git blob SHA is
`91a3759434eaf58cdd4a3003719448535f3ed3e0`.

Facts about the engine were read from the
[SuperXANA/AdvCiv](https://github.com/SuperXANA/AdvCiv) fork at
`5970334b64a875b5cdb370c94fc9a98db4eacda6`: `CvMap::reset` asks the script for
its grid and its wrap in the same call, with custom options already readable,
and multiplies a script's cells by four; `CIV4WorldInfo.xml` puts Huge at
120 x 84 plots; `CIV4SeaLevelInfo.xml` gives Low, Medium and High sea level
changes of -8, 0 and +6; `CIV4FeatureInfos.xml` allows forest on grass, plains
and tundra, jungle on grass and plains, and ice on water;
`CvMapGeneratorUtil.FeatureGenerator` calls the three per-plot methods that
both generators override. For climates: `CvMapGenerator::generateRandomMap`
(advc.194) resets the climate to the standard one unless the script's
`isClimateMap()` returns true; `CyMap.getClimate()`, `CyGlobalContext.getClimateInfo()`
(which returns nothing for an index out of range) and every `CvClimateInfo`
getter the script calls are exported to Python. The fork has no
`CIV4ClimateInfo.xml`, so the game loads the stock one. The harnesses use the
values of the original game's file
([f1rpo/Civ4CE](https://github.com/f1rpo/Civ4CE/blob/main/Civ4/Assets/XML/GameInfo/CIV4ClimateInfo.xml));
whether Beyond the Sword's copy differs was not checked, and the script reads
whatever the game has loaded.

## Results

| Check | Result | Evidence and scope |
| --- | --- | --- |
| Host suite, Python 3.13.18 | PASS — 29 tests | `python3 tests/check_equus.py` (28 without a 2.4 interpreter; the last is skipped) |
| Known World preservation | PASS | Every original top-level definition has the same AST except the seven named above; all other additions are the diagnostics, the climate code, or belong to the Expanded world |
| Known World output/RNG equivalence, Temperate | PASS in test doubles — 23 configurations | Exact plot arrays, terrain arrays, feature states, callback return and complete RNG argument/result traces match the pinned original, with diagnostics off and on, with the third option present and absent. All seven sizes, all nine wrap/variation pairs on Duel, all nine sea-level/variation pairs on Standard. It draws none of the Expanded world's random numbers |
| Climate code against the original, Known World | PASS — 3 configurations | With the Temperate bypass removed by the test, `_known_climate_terrain` and `KnownClimateFeatureGenerator` at zero distances give the pinned original's arrays and RNG trace |
| Known World sea level and climate | PASS | Low, normal and high sea give strictly more to less land at all seven sizes; every other climate changes the terrain, with either sea level and with diagnostics on or off; with all pack ice treated as impassable, the open ocean is as connected under Cold as under Temperate |
| Climate distances | PASS | The five stock climates give the distances tabulated above `_Climate`; only Temperate is calm; reading the climate draws no random number; an index the game does not hold is Temperate; ovals never shrink below half size |
| Rocky closes no road | PASS — 4 whole maps | In both worlds, every pair of land plots that could be walked between under Temperate can still be walked between under Rocky with the same seed, unless one of them itself became a peak. `_uplift` never raises a hill that is the only way between two of its neighbours |
| Climates, both worlds | PASS on Large | Against Temperate with the same seed: Cold has over 1.3 times the snow and tundra, over 1.5 times the pack ice, less jungle and desert; Tropical has less frost and desert and over 1.3 times the jungle; Arid has over 1.5 times the desert, less jungle and forest; Rocky has over 1.15 times the hills and the peaks. Coasts are identical under every climate, relief is identical except under Rocky, and only Rocky draws extra random numbers. The Crystal Empire's valley is grass under every climate |
| Expanded generation | PASS in test doubles — 23 configurations | Array sizes and value domains, untouched water terrain, diagnostics off/on identical, only its own RNG labels, land share between 45% and 72% |
| Expanded geography | PASS — 100 worlds | Fifty size/variation/sea-level/seed configurations, each with the bridges as causeways and as straits. Twenty-six named places are land and ten named seas are water; each mainland is one piece and can be crossed on foot without meeting a wall of peaks; causeways join their shores, or as straits leave three separate mainlands; Agarica, Mount Aris and the Storm King's Realm stay islands above Duel size; ships can reach every named sea but the Frozen North even with all pack ice treated as impassable |
| Expanded geography, other climates | PASS — 50 worlds | The same checks for Tropical, Arid, Rocky, Cold and a test climate with gentler relief, on five sizes, both bridge settings: Rocky's thicker ranges close no pass and Cold's wider ice closes no lane |
| Expanded biomes | PASS on Huge | Saddle Arabia, the Bone Dry Desert and Breezewood are desert; Antleria is snow; the Fields of Forever are grass; Zebrica and Amarezonia carry jungle; no jungle in Saddle Arabia; the southern rim is snow or tundra |
| Pack ice | PASS | Under Temperate, ice only on water, only within 4% of the top edge or beyond 84% south, never on a sea lane |
| Sea level and variation | PASS | Low, normal and high sea give strictly more to less land; Subtle and Lively differ from Standard |
| Sea room | PASS | On Huge, averaged over the sampled crossings, open water grows from 6.7 to 11.7 plots across the Celestial Sea beside Griffonstone, from 3.0 to 6.3 across the Great Inland Sea, and from 5.5 to 8.3 across the channel between Zebrica and Horsetrailia; at mid-height the land stands at least two plots clear of both map edges. The move never folds the picture (east stays east and south stays south on every sampled line), `_to_map` reverses `_to_atlas` to within a fifth of an XXL plot, zero extras and an empty table give the same map, and Trottingham Bridge stays where the picture has it |
| Table sanity | PASS | Shore latitudes strictly increase, west never exceeds east, ovals have positive radii, no ridge or sea-room segment has zero length (it would divide by zero) |
| Dimensions/options | PASS | Both size tables, save-load sentinel, larger world-index fallback, three options with their labels and defaults, invalid stored-choice fallback to the Known World, `isClimateMap()` and `isSeaLevelMap()` true |
| Diagnostics, errors and logging | PASS in captured streams/test doubles | Both worlds: exact summaries, no warning/error output on normal runs, injected errors keep their exception object, broken output sinks leave generation unchanged |
| Python 2.4.6 execution | PASS — 72 pipelines | `python2.4 tests/check_python24.py` parses, imports and runs the script on a CPython 2.4.6 built from source: Known World baseline/legacy/off/on and Expanded off/on at all seven sizes, then each of the five other climates in both worlds |
| Python 2.4 against Python 3 | PASS — 24 maps | `EQUUS_PYTHON24=... python3 tests/check_equus.py`: a checksum over each map's plots, terrain, features and RNG results is identical under both interpreters, for both worlds at all seven sizes and for both worlds under each other climate. The host harness also gives `/` its Python 2.4 meaning and counts integer/integer divisions in the script: none occur |
| Python 2.4 speed | Measured | An XXL Expanded world took about 1.2 s of CPU for its three passes, up from 0.4 s before sea room could follow a bent line; the Known World XXL about 0.3 s (0.36 s under Rocky) |
| Wider geography sweep | PASS — 2,016 worlds | Run once on this revision, not part of the suite: all seven sizes, three variations, three sea levels and both bridge settings, with six seeds under Temperate (756 worlds) and two seeds under each of the five other climates (1,260). An earlier pass of this sweep found one Rocky world in which a thickened range closed an unmarked gap between Ponyville and Trottingham Bridge; `_way_through` was added in answer and the sweep was run again from the start |
| Civilization IV generation | **NOT RUN for this revision** | See the [runtime evidence](Equus_Runtime_Verification.md): the playtester generated and auto-played the Expanded world of `ad619b3`. Neither world of this revision, and no climate but Temperate, has been generated in the game |

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
* About 53% of the map is land at normal sea level, where a Fractal map has
  roughly 30%. Low sea level raises that. A given world size therefore holds
  well over the usual territory.
* Sea room is a fraction of the map's width, so it adds nearly two plots a
  side on Huge but about half a plot on Duel, where the sea lanes still do
  most of the work. Inside a sharp bend of a line the land is squeezed harder
  than elsewhere (to about a tenth of its drawn area in the worst few plots of
  a Huge map).
* A climate moves edges by fixed distances, so its effect is strongest where
  painted regions are small and close together: under Arid the Known World's
  three deserts merge into one, and about a quarter of its land (a third of
  the Expanded world's) is desert. Deserts cost food; expect fewer good city
  sites. Under Cold about a third of the land is snow or tundra.
* The harness cannot show what the game's own passes make of a climate:
  rivers, flood plains and oases, resources, starting positions and
  normalization are the DLL's and may also read the climate.
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
worlds and the Expanded geography checklist. Generation of both worlds, the
Climate setting, native diagnostic log collection, starting-position review,
size and option coverage, and save/reload all remain **NOT RUN** for this
revision.
