# Equus map installation and diagnostics

This is a small overlay for an existing **MLP Civilization is Magic / AdvCiv
1.14** installation. Copy `PrivateMaps/Equus.py` to the loaded mod's
`PrivateMaps` directory. Preserve the rest of the mod and its other map scripts.

The regional atlas, two map options, RNG calls, and generation bodies come from
[`02add3513c2e5a96d3093fbd1a3b0f9696212f83`](https://github.com/SuperXANA/MLPCiv/commit/02add3513c2e5a96d3093fbd1a3b0f9696212f83).
The root-level deployment copy is moved to the game's expected path on this
integration branch. Neither original development branch is changed.

Optional diagnostics are disabled by default. Set `EQUUS_DIAGNOSTICS = True`
in the installed script and `LoggingEnabled = 1` in the active Windows BtS
profile's `CivilizationIV.ini`, then restart the game. Look for `[Equus]`
records in `PythonDbg.log` and errors/tracebacks in `PythonErr.log` under that
profile's `Logs` directory. Diagnostics report stage boundaries, options, grid
dimensions, array sizes, plot/terrain counts, and feature counts through the
native Python streams. They draw no random numbers and never replace a
generation exception with a successful result.

See [installation and runtime verification](docs/Equus_Runtime_Verification.md)
for the complete procedure, expected dimensions, log locations, geographic
checks, and fresh-game save/reload tests. See
[source validation](docs/Equus_Source_Validation.md) for measured checks and
their limits. **Civilization IV execution of this map remains unverified.**

Run the focused checks from this branch's root:

```sh
python3 tests/check_equus.py
/path/to/python2.4 tests/check_python24.py
```

The first command uses Python 3 host test doubles. The second must be run with
an actual Python 2.4 interpreter; the game script itself requires no Python 3
tools or third-party dependencies. `tests/fixtures/Equus_02add351.py` is the
pinned, uninstrumented source for equivalence checks, not an installable map.
