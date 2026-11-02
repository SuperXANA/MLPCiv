#!/usr/bin/env python3
"""Source-level Equus regression checks; no Civ4 process is launched.

Run from any working directory: python3 tests/check_equus.py
The game script remains Python 2.4 code. This host harness supplies unicode and
xrange aliases and deterministic stand-ins for Civ's extension/utility modules.
These stand-ins deliberately do not claim to reproduce the DLL or its RNG.
"""

import ast
import copy
import contextlib
import hashlib
import io
import itertools
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALLED = ROOT / "PrivateMaps" / "Equus.py"
BASELINE = ROOT / "tests" / "fixtures" / "Equus_02add351.py"
SIZES = ((7, 8), (10, 10), (12, 13), (16, 17),
         (19, 20), (24, 26), (30, 31))
TERRAINS = {"TERRAIN_GRASS": 10, "TERRAIN_PLAINS": 11,
            "TERRAIN_DESERT": 12, "TERRAIN_TUNDRA": 13,
            "TERRAIN_SNOW": 14}


class PlotTypes:
    PLOT_OCEAN = 0
    PLOT_LAND = 1
    PLOT_HILLS = 2
    PLOT_PEAK = 3


class MapRand:
    """Small reproducible RNG whose complete argument/result trace is retained."""
    def __init__(self, seed):
        self.state = seed
        self.calls = []

    def get(self, upper, label):
        self.state = (1103515245 * self.state + 12345) & 0x7fffffff
        result = self.state % upper
        self.calls.append((upper, label, result))
        return result


class Plot:
    def __init__(self, plot_type=0):
        self.plot_type = plot_type
        self.terrain = 20
        self.feature = -1

    def isWater(self):
        return self.plot_type == PlotTypes.PLOT_OCEAN

    def isPeak(self):
        return self.plot_type == PlotTypes.PLOT_PEAK

    def isLake(self):
        return False

    def getTerrainType(self):
        return self.terrain

    def getPlotType(self):
        return self.plot_type

    def getFeatureType(self):
        return self.feature

    def canHaveFeature(self, feature):
        if self.feature != -1 or self.isPeak():
            return False
        return self.isWater() if feature == 30 else not self.isWater()

    def setFeatureType(self, feature, variety):
        self.feature = feature


class World:
    def __init__(self, width, height, options, sea):
        self.width, self.height = width, height
        self.options, self.sea = options, sea
        self.plots = [Plot() for unused in range(width * height)]

    def getGridWidth(self):
        return self.width

    def getGridHeight(self):
        return self.height

    def getCustomMapOption(self, index):
        return self.options[index]

    def getSeaLevel(self):
        return self.sea

    def getWorldSize(self):
        return SIZES.index((self.width // 4, self.height // 4))

    def plot(self, x, y):
        return self.plots[y * self.width + x]

    def plotByIndex(self, index):
        return self.plots[index]

    def numPlots(self):
        return len(self.plots)


class SeaLevelInfo:
    def __init__(self, change):
        self.change = change

    def getSeaLevelChange(self):
        return self.change


class Fractal:
    def __init__(self, salt):
        self.salt = salt

    def getHeightFromPercent(self, percent):
        return int(255 * percent / 100)

    def getHeight(self, x, y):
        return (x * 131 + y * 73 + self.salt) % 256


class Environment:
    def __init__(self, width=28, height=32, options=(0, 1), sea=0, seed=1234):
        self.world = World(width, height, options, sea)
        self.rand = MapRand(seed)
        self.extensions = types.ModuleType("CvPythonExtensions")
        self.extensions.PlotTypes = PlotTypes
        self.extensions.CyMap = lambda: self.world
        self.extensions.CyGlobalContext = lambda: self
        self.extensions.CyTranslator = lambda: self
        self.utilities = types.ModuleType("CvMapGeneratorUtil")
        environment = self

        class FeatureGenerator:
            def __init__(self):
                self.iGridW = environment.world.width
                self.iGridH = environment.world.height
                self.mapRand = environment.rand
                self.featureIce = 30
                self.featureJungle = 31
                self.featureForest = 32
                self.forests = Fractal(self.mapRand.get(256, "stub forest"))
                self.jungles = Fractal(self.mapRand.get(256, "stub jungle"))

            def addFeatures(self):
                for y in range(self.iGridH):
                    for x in range(self.iGridW):
                        plot = environment.world.plot(x, y)
                        latitude = self.getLatitudeAtPlot(x, y)
                        self.addIceAtPlot(plot, x, y, latitude)
                        self.addJunglesAtPlot(plot, x, y, latitude)
                        self.addForestsAtPlot(plot, x, y, latitude)

        self.utilities.FeatureGenerator = FeatureGenerator

    def getGame(self):
        return self

    def getMapRand(self):
        return self.rand

    def getSeaLevelInfo(self, sea):
        return SeaLevelInfo((-10, 0, 10)[sea])

    def getInfoTypeForString(self, key):
        return TERRAINS[key]

    def getText(self, label, args):
        return "translated:" + label

    def load(self, path, diagnostics=False):
        old = {name: sys.modules.get(name) for name in
               ("CvPythonExtensions", "CvMapGeneratorUtil")}
        sys.modules["CvPythonExtensions"] = self.extensions
        sys.modules["CvMapGeneratorUtil"] = self.utilities
        module = types.ModuleType("Equus_under_test")
        module.__dict__.update({"unicode": str, "xrange": range})
        try:
            exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        finally:
            for name, value in old.items():
                if value is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = value
        module.EQUUS_DIAGNOSTICS = diagnostics
        return module


def generate(path, world_size=0, options=(0, 1), sea=1, seed=1234,
             diagnostics=False):
    cells = SIZES[world_size]
    env = Environment(cells[0] * 4, cells[1] * 4, options, sea, seed)
    module = env.load(path, diagnostics)
    output, errors = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        assert module.getGridSize([world_size]) == cells
        plots = module.generatePlotTypes()
        for index, value in enumerate(plots):
            env.world.plots[index].plot_type = value
        terrains = module.generateTerrainTypes()
        for index, value in enumerate(terrains):
            env.world.plots[index].terrain = value
        result = module.addFeatures()
    return (plots, terrains, [p.feature for p in env.world.plots],
            env.rand.calls, result, output.getvalue(), errors.getvalue())


class EquusChecks(unittest.TestCase):
    def test_pinned_baseline_fixture(self):
        content = BASELINE.read_bytes()
        blob = b"blob " + str(len(content)).encode("ascii") + b"\0" + content
        self.assertEqual(hashlib.sha1(blob).hexdigest(),
                         "395fa96ba5193b9483bc24cdfac8687fe4f9766d")

    def test_original_core_ast_is_preserved(self):
        baseline = ast.parse(BASELINE.read_bytes())
        installed = ast.parse(INSTALLED.read_bytes())
        wrapped = {"getGridSize", "generatePlotTypes", "generateTerrainTypes", "addFeatures"}
        additions = {"EQUUS_DIAGNOSTICS", "_diagnostic_write", "_diagnostic_counts",
                     "_diagnostic_begin", "_diagnostic_end", "_diagnostic_error",
                     "_diagnostic_stage"}
        def key(node):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                return node.name
            if isinstance(node, ast.Assign):
                return ",".join(target.id for target in node.targets)
            return ast.dump(node)
        current = {key(node): node for node in installed.body}
        for original in baseline.body:
            name = key(original)
            self.assertIn(name, current)
            node = copy.deepcopy(current[name])
            if name in wrapped:
                self.assertEqual([ast.dump(value) for value in node.decorator_list],
                                 [ast.dump(ast.Name(id="_diagnostic_stage", ctx=ast.Load()))])
                node.decorator_list = []
            self.assertEqual(ast.dump(original), ast.dump(node), name)
        self.assertEqual(set(current) - {key(node) for node in baseline.body}, additions)

    def test_install_layout(self):
        self.assertTrue(INSTALLED.is_file())
        self.assertFalse((ROOT / "Equus.py").exists(),
                         "Keep one deployable Equus.py under PrivateMaps")

    def test_grid_sizes_and_load_sentinel(self):
        module = Environment().load(INSTALLED)
        for index, cells in enumerate(SIZES):
            self.assertEqual(module.getGridSize([index]), cells)
            self.assertGreater(cells[0] * 4, 0)
            self.assertGreater(cells[1] * 4, 0)
        self.assertEqual(module.getGridSize([-1]), [])
        self.assertEqual(module.getGridSize([99]), SIZES[-1])

    def test_options(self):
        for wrap, variation in itertools.product(range(3), repeat=2):
            env = Environment(options=(wrap, variation))
            module = env.load(INSTALLED)
            self.assertEqual(module.getNumCustomMapOptions(), 2)
            self.assertEqual(module.getWrapX(), wrap != 0)
            self.assertEqual(module.getWrapY(), wrap == 2)
            self.assertEqual(module._variation(), (0.5, 1.0, 1.5)[variation])
            for index in range(2):
                self.assertEqual(module.getNumCustomMapOptionValues([index]), 3)
                self.assertEqual(module.getCustomMapOptionDefault([index]), (0, 1)[index])
                self.assertFalse(module.isRandomCustomMapOption([index]))
                self.assertTrue(module.getCustomMapOptionName([index]))
                for choice in range(3):
                    self.assertTrue(module.getCustomMapOptionDescAt([index, choice]))
        for invalid in (-1, 3, 999):
            module = Environment(options=(invalid, invalid)).load(INSTALLED)
            self.assertEqual(module._option(0), 0)
            self.assertEqual(module._option(1), 1)

    def test_arrays_rng_and_logging_are_observational(self):
        cases = {(size, 0, 1, 1) for size in range(len(SIZES))}
        cases.update((0, wrap, variation, 1)
                     for wrap, variation in itertools.product(range(3), repeat=2))
        cases.update((3, 0, variation, sea)
                     for variation, sea in itertools.product(range(3), repeat=2))
        for size, wrap, variation, sea in sorted(cases):
            with self.subTest(size=size, wrap=wrap, variation=variation, sea=sea):
                args = dict(world_size=size, options=(wrap, variation), sea=sea)
                baseline = generate(BASELINE, **args)
                disabled = generate(INSTALLED, diagnostics=False, **args)
                enabled = generate(INSTALLED, diagnostics=True, **args)
                self.assertEqual(baseline[:5], disabled[:5])
                self.assertEqual(baseline[:5], enabled[:5])
                self.assertEqual(disabled[5:], ("", ""))
                self.assertEqual(enabled[6], "")
                self.assertNotIn("WARN", enabled[5])
                self.assertNotIn("ERROR", enabled[5])
                for stage in ("getGridSize", "generatePlotTypes",
                              "generateTerrainTypes", "addFeatures"):
                    self.assertIn(stage + " BEGIN", enabled[5])
                    self.assertIn(stage + " END", enabled[5])
                width, height = (value * 4 for value in SIZES[size])
                self.assertIn("grid=%dx%d plots=%d sea_level=%d" %
                              (width, height, width * height, sea), enabled[5])
                self.assertIn("option[0] raw=%d effective=%d" % (wrap, wrap), enabled[5])
                self.assertIn("option[1] raw=%d effective=%d" % (variation, variation), enabled[5])
                for label, value in (("ocean", 0), ("land", 1),
                                     ("hills", 2), ("peak", 3)):
                    self.assertIn("plot %s=%d" % (label, enabled[0].count(value)), enabled[5])
                for key, value in TERRAINS.items():
                    self.assertIn("terrain %s id=%d count=%d" %
                                  (key[len("TERRAIN_"):], value, enabled[1].count(value)), enabled[5])
                for label, values in (("terrain_ids", enabled[1]),
                                      ("feature_ids", enabled[2])):
                    counts = ", ".join("%s:%d" % (value, values.count(value))
                                       for value in sorted(set(values)))
                    self.assertIn(label + "={" + counts + "}", enabled[5])
                expected = SIZES[size][0] * SIZES[size][1] * 16
                self.assertEqual(len(enabled[0]), expected)
                self.assertEqual(len(enabled[1]), expected)
                self.assertTrue(set(enabled[0]).issubset({0, 1, 2, 3}))
                self.assertTrue(set(enabled[1]).issubset(set(TERRAINS.values()) | {20}))
                self.assertIn(0, enabled[0])
                self.assertTrue(any(p != 0 for p in enabled[0]))
                for plot_type, terrain_type in zip(enabled[0], enabled[1]):
                    if plot_type == 0:
                        self.assertEqual(terrain_type, 20)
                self.assertEqual(enabled[4], 0)

    def test_seed_changes_map_without_logging_changes(self):
        first = generate(INSTALLED, seed=17, diagnostics=True)
        repeat = generate(INSTALLED, seed=17, diagnostics=False)
        second = generate(INSTALLED, seed=18, diagnostics=True)
        self.assertEqual(first[:5], repeat[:5])
        self.assertNotEqual(first[0], second[0])

    def test_load_sentinel_diagnostics(self):
        env = Environment()
        module = env.load(INSTALLED, True)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(module.getGridSize([-1]), [])
        self.assertIn("load sentinel; keep saved dimensions", output.getvalue())
        self.assertEqual(env.rand.calls, [])

    def test_diagnostic_size_mismatch_is_reported_without_rewriting_result(self):
        env = Environment()
        module = env.load(INSTALLED, True)
        result = [PlotTypes.PLOT_LAND]
        module._plot_types = lambda *args: result
        errors = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            self.assertIs(module.generatePlotTypes(), result)
        self.assertIn("ERROR unexpected output-array size", errors.getvalue())
        self.assertEqual(env.rand.calls, [])

    def test_generation_errors_propagate(self):
        class SentinelError(Exception):
            pass
        for diagnostics in (False, True):
            for callback, dependency in (("generatePlotTypes", "_plot_types"),
                                         ("generateTerrainTypes", "_land_terrain"),
                                         ("addFeatures", "EquusFeatureGenerator")):
                with self.subTest(diagnostics=diagnostics, callback=callback):
                    env = Environment()
                    env.world.plots[0].plot_type = PlotTypes.PLOT_LAND
                    module = env.load(INSTALLED, diagnostics)
                    sentinel = SentinelError("equus test injected failure")
                    def fail(*args):
                        raise sentinel
                    setattr(module, dependency, fail)
                    output, errors = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                        with self.assertRaises(SentinelError) as caught:
                            getattr(module, callback)()
                    self.assertIs(caught.exception, sentinel)
                    if diagnostics:
                        combined = output.getvalue() + errors.getvalue()
                        self.assertIn("equus test injected failure", combined)
                        self.assertIn("Traceback", combined)
                    else:
                        self.assertEqual(output.getvalue() + errors.getvalue(), "")

    def test_logging_sink_failure_does_not_change_generation(self):
        class BrokenSink:
            def write(self, value):
                raise IOError("log destination unavailable")
            def flush(self):
                raise IOError("log destination unavailable")
        expected = generate(INSTALLED, diagnostics=False)
        env = Environment(sea=1)
        module = env.load(INSTALLED, True)
        with contextlib.redirect_stdout(BrokenSink()), contextlib.redirect_stderr(BrokenSink()):
            plots = module.generatePlotTypes()
            for index, value in enumerate(plots):
                env.world.plots[index].plot_type = value
            terrains = module.generateTerrainTypes()
            for index, value in enumerate(terrains):
                env.world.plots[index].terrain = value
            result = module.addFeatures()
        actual = (plots, terrains, [p.feature for p in env.world.plots], env.rand.calls, result)
        self.assertEqual(actual, expected[:5])

    def test_python24_source_guard(self):
        # A focused guard, not a replacement for CPython 2.4 compilation.
        source = INSTALLED.read_text(encoding="ascii")
        tree = ast.parse(source)
        forbidden = (ast.Set, ast.SetComp, ast.DictComp, ast.JoinedStr,
                     ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith,
                     ast.Await, ast.NamedExpr, ast.With, ast.Nonlocal,
                     ast.YieldFrom, ast.Match, ast.AnnAssign)
        for node in ast.walk(tree):
            self.assertNotIsInstance(node, forbidden)
            if isinstance(node, ast.ExceptHandler):
                self.assertIsNone(node.name, "Use bare except or except Type: for Python 2.4")
            if isinstance(node, ast.FunctionDef):
                self.assertFalse(node.returns or node.args.kwonlyargs)
                self.assertFalse(any(arg.annotation for arg in node.args.args))
            if isinstance(node, ast.Try):
                self.assertFalse(node.handlers and node.finalbody,
                                 "Combined try/except/finally needs Python 2.5")
        self.assertNotIn("from __future__ import", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
