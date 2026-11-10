# Equus source validation

Offline results recorded November 2, 2026. Gameplay evidence recorded November 8, 2026.

## Source and scope

The [installation integration](https://github.com/SuperXANA/MLPCiv/tree/fa4ef9cf62814c3ef8151d99924c87aac9b89b18) is based on
[`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83)
from `PyEquusMapCreation-ChatGPT`. It moves the deployable script from the
repository root to `PrivateMaps/Equus.py`, adds optional diagnostics, and
supplies focused checks and installation/runtime documentation. Both existing
development branches retain their source. The installation branch is a sparse overlay;
it does not contain or replace the six maps in `master/PrivateMaps`.

The pinned test fixture is byte-identical to that commit's original script:
Git blob SHA `395fa96ba5193b9483bc24cdfac8687fe4f9766d`.
The installed instrumented script's Git blob SHA is
`1c84dcdb986c818ac483a1a1d250a6727a31200a`.

## Results

| Check | Result | Evidence and scope |
| --- | --- | --- |
| Host suite, Python 3.12.14 | PASS — 12 tests | `python3 tests/check_equus.py` |
| Baseline preservation | PASS | Every original top-level definition, constant and import has the same AST; only the four callback decorators are excluded from this comparison |
| Host generation matrix | PASS — 23 configurations, 69 pipelines | Original/off/on comparisons across all seven sizes, all nine wrap/variation pairs on Duel, and all nine sea-level/variation pairs on Standard, with two overlaps |
| Output/RNG equivalence | PASS in test doubles | Exact plot arrays, terrain arrays, feature states, callback return and complete RNG argument/result traces match the pinned original |
| Dimensions/options | PASS | Seven expected grids, save-load sentinel, larger world-index fallback, valid option values/defaults and invalid stored-choice fallback |
| Diagnostics | PASS in captured streams | Stage boundaries, actual grid, sea level, raw/effective options, exact plot/terrain counts and feature histograms; normal enabled runs have no warning/error output |
| Error and logging behavior | PASS in test doubles | Injected generation errors retain their exception object and produce enabled tracebacks; disabled logging is silent; broken output sinks leave generation unchanged; output-size mismatch is reported without rewriting the result |
| Python 2.4.6 execution | PASS — seven sizes, 21 pipelines | `python2.4 tests/check_python24.py` actually parses/imports/runs the baseline, off and on versions, including features and RNG trace comparisons |
| Independent source review | PASS | No geography edits, extra RNG draws, map writes by diagnostics, or post-2.4 script dependencies found |
| Civilization IV basic generation | **PASS (one documented run)** | The [in-game screenshot](https://github.com/SuperXANA/MLPCiv/blob/fa4ef9cf62814c3ef8151d99924c87aac9b89b18/docs/equus.png) in the [November 8 gameplay commit](https://github.com/SuperXANA/MLPCiv/commit/fa4ef9cf62814c3ef8151d99924c87aac9b89b18) shows the generated map at turn 0 |

Both harnesses supply deterministic test doubles for `CvPythonExtensions` and
`CvMapGeneratorUtil.FeatureGenerator`. Their RNG is a small repeatable stand-in,
not Civ's RNG. These checks establish instrumentation equivalence and Python
language compatibility for the tested inputs, not full engine compatibility.
The Python 3 harness has host-only dependencies from its standard library;
only `PrivateMaps/Equus.py` is installed into the game.

The standalone 2.4.6 result does not verify the game's exact embedded Python
patch level or Windows extension bindings. The script uses Python 2.4 syntax
and existing built-ins/standard-library modules; its diagnostic imports are
limited to `sys` and `traceback` when enabled.

## Runtime follow-up

The playtest report describes a successful first attempt with no error
messages displayed. See [Equus runtime verification](Equus_Runtime_Verification.md)
for the evidence and remaining checks. Native diagnostic log collection,
comprehensive geography and starting-position review, size and option
coverage, and save/reload remain **NOT RUN**. The offline results above apply
to the pinned integration and its fixture.
