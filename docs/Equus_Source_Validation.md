# Equus source validation

Offline results for the two-world script with climates and the Known World's
Trottingham strait, recorded November 28, 2026. Earlier results (November 2) and gameplay evidence (November 8) describe
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
  Its tables, helpers (`_plot_types` among them), terrain rules and feature
  generator are untouched. Seven top-level definitions changed: `CvMapOptions`
  (one more row), `getDescription`, `getGridSize` (the size table now depends
  on the world), `isClimateMap` (now `True`) and the three generation
  callbacks. Each callback gained one `if _expanded():` branch and one climate
  branch that is not taken under Temperate.
* **The Trottingham strait** is new in the Known World. The original shore
  tables overlap across the whole top of the map, which joined Equestria and
  Griffonstone; the official map has a strait there. `generatePlotTypes` now
  turns the plots of `_known_strait()` into ocean after `_plot_types` has
  returned: a table of water banks (`_TROTTINGHAM_STRAIT`), two sea lanes
  (`_TROTTINGHAM_LANES`) and, if `KNOWN_BRIDGE_IS_LAND` is set, a causeway.
  It draws no random number. The banks were traced from the picture twice,
  independently, by eye on enlargements and by pixel colour; the two agreed
  to about .003 of the picture's width. The picture shows the sea along its
  horizon (7% of the way down) from x .54 to .78; north of that it paints
  only a thin rim of far snow peaks and icebergs, and then sky. The table
  leaves the rim out and carries the sea on to the top edge, as a bay that
  narrows to x .60 to .75 there. That outline north of the horizon is
  invented; the picture gives none. A window of sea that the picture also
  shows farther east along the horizon, behind Bug Bear Territory (x .86 to
  .90), is left as land. The second sea lane, which makes the Griffish Isles
  an island, is not the painted channel west of the isle (x .797 to .811),
  which is too close to the isle to survive on a small grid: it runs just
  west of it, through about four plots of the painted Trottingham headland
  on a Huge map.
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
`3ea64813d0ec2c132d355004c09aaeb158ef311e`.

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
| Host suite, Python 3.13.18 | PASS — 33 tests | `python3 tests/check_equus.py` (32 without a 2.4 interpreter; the last is skipped) |
| Known World preservation | PASS | Every original top-level definition has the same AST except the seven named above, `_plot_types` and every Known World table included; all other additions are the diagnostics, the climate code, the strait, or belong to the Expanded world |
| Known World output/RNG equivalence, strait table emptied, Temperate | PASS in test doubles — 23 configurations | With `_TROTTINGHAM_STRAIT` emptied: exact plot arrays, terrain arrays, feature states, callback return and complete RNG argument/result traces match the pinned original, with diagnostics off and on, with the third option present and absent. All seven sizes, all nine wrap/variation pairs on Duel, all nine sea-level/variation pairs on Standard. It draws none of the Expanded world's random numbers |
| The strait changes only the strait, Temperate | PASS in test doubles — 31 configurations, each with and without the causeway | The default Known World draws exactly the pinned original's random numbers; every plot either has the original's plot type, terrain and feature, or belongs to the sets returned by `_known_strait()`, which are ocean without a feature (or the causeway's flat land). All seven sizes; all nine variation/sea-level pairs on Duel, Standard and XXL |
| Three continents | PASS — 84 worlds, 176 more with the causeway, 28 with the table emptied, 3 under Rocky | With land units allowed to step diagonally: Equestria, Griffonstone and the Dragon lands are three land areas; a ship that cannot cut corners sails from the Celestial Sea through the strait to the top row; the Griffish Isles' core plot is land and belongs to neither mainland. All seven sizes, three variations and three sea levels, with extra seeds for Lively at low sea, where an earlier design failed. With the causeway (all sizes, and many seeds on Duel and Tiny, where an earlier causeway failed; 52 of them under Rocky): joined, walkable without crossing a peak, no ship passes, the seas north and south of it do not touch even at a corner, every causeway plot is flat land, and the Griffish Isles are still an island. With the table emptied: one land area, as before. Under Rocky the strait stays open |
| Strait tables and sea level | PASS | Tables well formed; the banks lie within .012 of the picture's width of the channel as it was traced from the picture, at twelve latitudes; every strait plot lies in the north-east (x .50 to .89, north of v .31) and the strait is 1.5% to 5.5% of the map; at every size the lanes are water at all three sea levels, a higher sea never removes a strait plot, the first lane is an unbroken chain without a diagonal step from the top row, no lane crosses the Griffish Isles' core, and an emptied table returns nothing even with the causeway switched on |
| Edits that the comments invite | PASS | Deleting the second lane's two lines from the source text leaves a script that loads and still parts the continents (three sizes); a lane drawn straight over the Griffish Isles does not sink the isle's core, and a table carried south over the isle keeps off its oval (all seven sizes) |
| Climate code against the original, Known World | PASS — 3 configurations | With the strait table emptied and the Temperate bypass removed by the test, `_known_climate_terrain` and `KnownClimateFeatureGenerator` at zero distances give the pinned original's arrays and RNG trace |
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
| Python 2.4.6 execution | PASS — 102 pipelines | `python2.4 tests/check_python24.py` parses, imports and runs the script on a CPython 2.4.6 built from source. Known World at all seven sizes: the baseline; three runs with the strait table emptied, equal to it; the strait, diagnostics off and on, with the baseline's random draws, the baseline's terrain and features on every plot it leaves as land, and ocean where it differs; the causeway, off and on. Expanded off/on at all seven sizes; each of the five other climates in both worlds; and the causeway under Rocky |
| Python 2.4 against Python 3 | PASS — 32 maps | `EQUUS_PYTHON24=... python3 tests/check_equus.py`: a checksum over each map's plots, terrain, features and RNG results is identical under both interpreters, for both worlds at all seven sizes, the Known World's causeway at all seven sizes and once under Rocky, and both worlds under each other climate. The host harness also gives `/` its Python 2.4 meaning and counts integer/integer divisions in the script: none occur |
| Python 2.4 speed | Measured | An XXL Expanded world took about 1.2 s of CPU for its three passes, up from 0.4 s before sea room could follow a bent line; the Known World XXL about 0.3 s (0.36 s under Rocky) |
| Wider geography sweep, Expanded | PASS — 2,016 worlds | Run once on the previous revision, not part of the suite; this revision leaves the Expanded world's output unchanged (128 configurations compared). All seven sizes, three variations, three sea levels and both bridge settings, with six seeds under Temperate (756 worlds) and two seeds under each of the five other climates (1,260). An earlier pass of this sweep found one Rocky world in which a thickened range closed an unmarked gap between Ponyville and Trottingham Bridge; `_way_through` was added in answer and the sweep was run again from the start |
| Wider geography sweep, Known World | PASS — 1,008 worlds, and 1,476 with the causeway | Run once on this revision, not part of the suite. Strait: all seven sizes, three variations and three sea levels with twelve seeds (756 worlds), 126 with the causeway and 126 under Rocky: three land areas, a ship reaches the top row, the Griffish Isles are an island. Causeway: Duel and Tiny with sixty seeds each, the other sizes with six, and the seeds that defeated an earlier causeway, under Rocky too: joined, walkable, no ship passes, the two seas do not touch at a corner, the isle is still an island |
| Independent review | DONE | Before the code was written, the strait was traced from the picture twice by separate reviewers and the plan was attacked by two more, who found that a strait ending at the bay head left the continents joined in about one world in ten and that its table drowned the Griffish Isles; the design was changed. Afterwards four reviewers (code and Python 2.4, fidelity to the picture, topology, documents and tests) examined the change and a sceptic re-checked each finding. Their own sweeps of the default map, over 5,500 worlds, found no joined continents and no closed strait. They found, and this revision fixes: a causeway that ended against peaks in about one Duel world in a hundred and landed on the Griffish Isles on Tiny maps; a comment inviting an edit that left a syntax error; a false remark that the cut-off sea would be a lake; stale counts and a stale script hash in this document; two assertions that could not fail; and five deliberately broken versions of the script that the tests did not notice. Nine such broken versions were then run against the new tests: eight are caught, and the ninth (tracing the causeway with diagonal steps) draws the same plots, because the causeway is a straight line |
| Civilization IV generation | **NOT RUN for this revision** | See the [runtime evidence](Equus_Runtime_Verification.md): the playtester generated and auto-played the Expanded world of `ad619b3`. Neither world of this revision, no climate but Temperate, and no Known World with the strait has been generated in the game |

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

## Known limits of the Known World's strait

* "The same map outside the strait" is a statement about what the script
  returns: plot types and terrain, and the script's own random draws. In the
  game, rivers, lakes, forests and jungles, resources, huts and starting
  positions are placed afterwards by passes that draw from the same random
  stream according to where land and water are, so for a given seed they will
  differ across the whole map from a game generated before this change. None
  of that is visible to the harness.
* The identity holds under Temperate, and under Tropical, Arid and Cold as far
  as relief goes. Under Rocky the relief pass runs after the strait is cut,
  so that it judges the finished coast; its draws differ from those of a
  Rocky map made before the strait existed, and with them the hills and
  peaks, and the terrain and forests that are drawn afterwards, everywhere.
* The banks are the same in every game. Every other coast is tested at
  positions moved by the Atlas variation noise, which is private to
  `_plot_types`; drawing more noise for the strait would have changed the
  random stream for everything after it.
* The strait is narrow: one plot at the bridge at low and normal sea level
  at every size (two or three plots on Large, Huge and XXL at high sea), and
  only the one-plot lane at low sea level. Most of its shore is peak, tundra
  or snow. At low and normal sea one ship can block it.
* On large maps a lane sometimes leaves a scrap of the old shore standing as
  an islet of one or two plots beside the Griffish Isles: in about one world
  in ten at Huge and XXL and a few in a hundred at Large, and in none seen
  at Standard or smaller. The picture paints an islet of its own there.
* Griffonstone becomes a continent of its own with about 12% of the land (65
  plots at Duel, 759 at Huge in one sampled world), reachable only by ship.
  Whether the game starts a civilization there, and how good that start is,
  is the DLL's decision and is untested.
* With `KNOWN_BRIDGE_IS_LAND = True` the water north of the causeway is
  closed to ships from the Celestial Sea. It is still a sea, not a lake: 24
  to 26 plots on a Duel map and over 200 on Huge (the stock game calls water
  a lake at 9 plots or fewer). Cities on it can build ships that cannot
  leave it. The causeway crosses a little north of the painted bridge
  (v .168 for .176), because on a Tiny map the painted line lands on the
  Griffish Isles, and it starts inside the massif at the end of the Crystal
  Mountains, flattening a few peaks there, so that its western end cannot be
  walled in.
* Under the Cylinder and Toroid wraps Equestria and Griffonstone still touch
  across the east/west seam. Three continents is a property of Flat wrap.

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
