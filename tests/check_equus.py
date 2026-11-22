#!/usr/bin/env python3
"""Source-level Equus regression checks; no Civ4 process is launched.

Run from any working directory: python3 tests/check_equus.py
The game script remains Python 2.4 code. This host harness supplies unicode and
xrange aliases and deterministic stand-ins for Civ's extension/utility modules.
These stand-ins deliberately do not claim to reproduce the DLL or its RNG.

Python 2.4 divides two integers with floor division. The harness rewrites each
"/" in the loaded script to keep that meaning and counts integer/integer uses,
so a map can never depend on which Python ran it.
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
KNOWN, EXPANDED = 0, 1  # choices of the "Alternative Universe Expansions" option
SIZES = ((7, 8), (10, 10), (12, 13), (16, 17),
         (19, 20), (24, 26), (30, 31))
EXPANDED_SIZES = ((9, 6), (12, 8), (16, 11), (20, 14),
                  (24, 16), (30, 21), (37, 25))
WORLD_SIZES = (SIZES, EXPANDED_SIZES)
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
        # CIV4FeatureInfos.xml of AdvCiv 1.14: ice on water; jungle on grass and
        # plains; forest on grass, plains and tundra. Nothing on a peak.
        if self.feature != -1 or self.isPeak():
            return False
        if feature == 30:
            return self.isWater()
        if self.isWater():
            return False
        if feature == 31:
            return self.terrain in (10, 11)
        return self.terrain in (10, 11, 13)

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
        if 0 <= index < len(self.options):
            return self.options[index]
        return -1  # CvInitCore: NO_CUSTOM_MAPOPTION for an index it does not hold

    def getSeaLevel(self):
        return self.sea

    def getWorldSize(self):
        cells = (self.width // 4, self.height // 4)
        for sizes in WORLD_SIZES:
            if cells in sizes:
                return sizes.index(cells)
        raise ValueError(cells)

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


class ClassicDivision(ast.NodeTransformer):
    """Give "/" its Python 2.4 meaning inside the script under test."""
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Div):
            call = ast.Call(func=ast.Name(id="__classic_division__", ctx=ast.Load()),
                            args=[node.left, node.right], keywords=[])
            return ast.copy_location(call, node)
        return node

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Div):
            raise AssertionError("write x = x / y, so that the harness can check it")
        return self.generic_visit(node)


class Environment:
    def __init__(self, width=28, height=32, options=(0, 1), sea=0, seed=1234):
        self.integer_divisions = 0
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

    def divide(self, left, right):
        if type(left) is int and type(right) is int:
            self.integer_divisions += 1
            return left // right
        return left / right

    def load(self, path, diagnostics=False):
        old = {name: sys.modules.get(name) for name in
               ("CvPythonExtensions", "CvMapGeneratorUtil")}
        sys.modules["CvPythonExtensions"] = self.extensions
        sys.modules["CvMapGeneratorUtil"] = self.utilities
        module = types.ModuleType("Equus_under_test")
        module.__dict__.update({"unicode": str, "xrange": range,
                                "__classic_division__": self.divide})
        tree = ClassicDivision().visit(ast.parse(path.read_bytes(), str(path)))
        ast.fix_missing_locations(tree)
        try:
            exec(compile(tree, str(path), "exec"), module.__dict__)
        finally:
            for name, value in old.items():
                if value is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = value
        module.EQUUS_DIAGNOSTICS = diagnostics
        return module


def cells_for(world_size, options):
    atlas = KNOWN
    if len(options) > 2 and options[2] == EXPANDED:
        atlas = EXPANDED
    return WORLD_SIZES[atlas][world_size]


def generate(path, world_size=0, options=(0, 1), sea=1, seed=1234,
             diagnostics=False, tweak=None):
    cells = cells_for(world_size, options)
    env = Environment(cells[0] * 4, cells[1] * 4, options, sea, seed)
    module = env.load(path, diagnostics)
    if tweak is not None:
        tweak(module)
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
    assert env.integer_divisions == 0, "integer division in the map script"
    return (plots, terrains, [p.feature for p in env.world.plots],
            env.rand.calls, result, output.getvalue(), errors.getvalue())


def digest(values):
    """FNV-1a over small integers: the same arithmetic runs under Python 2.4."""
    state = 2166136261
    for value in values:
        state = ((state ^ (value & 0xff)) * 16777619) & 0xffffffff
        state = ((state ^ ((value >> 8) & 0xff)) * 16777619) & 0xffffffff
    return state


def map_digest(result):
    plots, terrains, features, calls = result[:4]
    return "%08x" % digest(list(plots) + list(terrains) +
                           [feature + 1 for feature in features] +
                           [call[2] for call in calls])


# ---- Geography of the Expanded world -------------------------------------
# Places as atlas fractions (x east, v south), the same units as the script.
PLACES = {
    "Ponyville": (.235, .33), "Crystal Empire": (.283, .143), "Yakyakistan": (.105, .078),
    "Manehattan": (.385, .215), "Las Pegasus": (.075, .45), "Appleloosa": (.19, .43),
    "Badlands": (.24, .565), "Froud Valley": (.185, .80), "Klugetown": (.36, .855),
    "Changeling Kingdom": (.38, .63), "Vanhoover": (.13, .195),
    "Griffonstone": (.495, .40), "Saddle Arabia": (.565, .41), "Zebrica": (.655, .555),
    "Abyssinia": (.71, .695), "Dragon Lands": (.585, .715),
    "Ponyland": (.56, .20), "Jewel Desert": (.64, .215), "Fields of Forever": (.80, .22),
    "Antleria": (.905, .11), "Sanchez Mountains": (.82, .45), "Horsetrailia": (.845, .63),
    "Lost Lagoon": (.835, .745),
    "Agarica": (.62, .975), "Mount Aris": (.482, .889), "Storm King's Realm": (.134, .959)}
SEAS = {
    "Celestial Sea": (.44, .30), "Great Inland Sea": (.66, .31), "Luna Bay": (.085, .165),
    "Bridle Bay": (.775, .50), "Tergum Sea": (.59, .585), "Crystal Sea": (.45, .77),
    "Sparkling Sea": (.97, .40), "South Luna Ocean": (.03, .75),
    "North Luna Ocean": (.03, .25), "Frozen North": (.47, .055)}
MAINLANDS = (
    ("Equestria", ("Ponyville", "Crystal Empire", "Yakyakistan", "Manehattan", "Las Pegasus",
                   "Appleloosa", "Badlands", "Froud Valley", "Klugetown",
                   "Changeling Kingdom", "Vanhoover")),
    ("Zebrica", ("Griffonstone", "Saddle Arabia", "Zebrica", "Abyssinia", "Dragon Lands")),
    ("Ponyland", ("Ponyland", "Jewel Desert", "Fields of Forever", "Antleria",
                  "Sanchez Mountains", "Horsetrailia", "Lost Lagoon")))
ISLANDS = ("Agarica", "Mount Aris", "Storm King's Realm")
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def nearest(plots, width, height, place, land):
    """The plot at a place, or a neighbour of it, that is land (or water)."""
    x0 = min(width - 1, int(place[0] * width))
    y0 = min(height - 1, int((1.0 - place[1]) * height))
    for unused, x, y in sorted((abs(dx) + abs(dy), x0 + dx, y0 + dy)
                               for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
        if 0 <= x < width and 0 <= y < height and (plots[y * width + x] != 0) == land:
            return (x, y)
    return None


def flood(plots, width, height, start, allowed, blocked=(), shipping=False):
    """Plots reachable from start. Land units may step diagonally; a ship may
    not cut the corner between two land plots (CvGameCoreUtils pathValid)."""
    seen = {start}
    queue = [start]
    while queue:
        x, y = queue.pop()
        for dx, dy in STEPS:
            xx, yy = x + dx, y + dy
            if not (0 <= xx < width and 0 <= yy < height) or (xx, yy) in seen:
                continue
            if plots[yy * width + xx] not in allowed or (xx, yy) in blocked:
                continue
            if (shipping and dx and dy and plots[y * width + xx] != 0 and
                    plots[yy * width + x] != 0):
                continue
            seen.add((xx, yy))
            queue.append((xx, yy))
    return seen


def beside(spot, plots):
    return any((spot[0] + dx, spot[1] + dy) in plots
               for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def geography_problems(world_size, variation, sea, seed, bridges_are_land):
    """Generate one Expanded world and list everything wrong with its layout."""
    def tweak(module):
        module.EXPANDED_BRIDGES_ARE_LAND = bridges_are_land
    cells = EXPANDED_SIZES[world_size]
    width, height = cells[0] * 4, cells[1] * 4
    result = generate(INSTALLED, world_size, (0, variation, EXPANDED), sea, seed, tweak=tweak)
    plots, features = result[0], result[2]
    problems = []
    spot, water = {}, {}
    for name, place in PLACES.items():
        spot[name] = nearest(plots, width, height, place, True)
        if spot[name] is None:
            problems.append("no land at " + name)
    for name, place in SEAS.items():
        water[name] = nearest(plots, width, height, place, False)
        if water[name] is None:
            problems.append("no water at " + name)
    if problems:
        return problems
    area = {}
    for mainland, names in MAINLANDS:
        area[mainland] = flood(plots, width, height, spot[names[0]], (1, 2, 3))
        on_foot = flood(plots, width, height, spot[names[0]], (1, 2))
        for name in names[1:]:
            if spot[name] not in area[mainland]:
                problems.append("%s is cut off from %s" % (name, names[0]))
            elif not beside(spot[name], on_foot):
                problems.append("peaks wall %s off from %s" % (name, names[0]))
    joined = (spot["Ponyland"] in area["Equestria"], spot["Zebrica"] in area["Equestria"],
              spot["Zebrica"] in area["Ponyland"])
    if bridges_are_land:
        if not (joined[0] and joined[2]):
            problems.append("a causeway fails to join its two shores")
        on_foot = flood(plots, width, height, spot["Ponyville"], (1, 2))
        for name in ("Ponyland", "Saddle Arabia", "Horsetrailia"):
            if not beside(spot[name], on_foot):
                problems.append("%s cannot be walked to from Ponyville" % name)
    else:
        if True in joined:
            problems.append("two of the three mainlands touch")
        if world_size > 0:  # on a Duel grid an isle may lean on the nearest shore
            for name in ISLANDS:
                for mainland in area:
                    if spot[name] in area[mainland]:
                        problems.append("%s has merged with %s" % (name, mainland))
    # One ocean for ships, even with every pack-ice plot treated as a wall.
    ice = set((i % width, i // width) for i, feature in enumerate(features) if feature == 30)
    ocean = set()
    unvisited = set((i % width, i // width) for i, kind in enumerate(plots)
                    if kind == 0) - ice
    while unvisited:
        body = flood(plots, width, height, min(unvisited), (0,), ice, True)
        unvisited -= body
        if len(body) > len(ocean):
            ocean = body
    for name in SEAS:
        if name == "Frozen North":
            continue  # a causeway makes it an inland sea, and it is icy besides
        if not beside(water[name], ocean):
            problems.append("ships cannot reach the " + name)
    return problems


class EquusChecks(unittest.TestCase):
    def test_pinned_baseline_fixture(self):
        content = BASELINE.read_bytes()
        blob = b"blob " + str(len(content)).encode("ascii") + b"\0" + content
        self.assertEqual(hashlib.sha1(blob).hexdigest(),
                         "395fa96ba5193b9483bc24cdfac8687fe4f9766d")

    def test_known_world_source_is_preserved(self):
        """Every Known World definition is untouched, bar the six that had to
        learn about a second atlas. (Their Known World results are compared
        with the verified baseline in test_known_world_matches_baseline.)"""
        baseline = ast.parse(BASELINE.read_bytes())
        installed = ast.parse(INSTALLED.read_bytes())
        wrapped = {"getGridSize", "generatePlotTypes", "generateTerrainTypes", "addFeatures"}
        reworked = wrapped | {"CvMapOptions", "getDescription"}
        diagnostics = {"EQUUS_DIAGNOSTICS", "_diagnostic_write", "_diagnostic_counts",
                       "_diagnostic_begin", "_diagnostic_end", "_diagnostic_error",
                       "_diagnostic_stage"}
        expansion = {"ATLAS_WORLD", "KNOWN_WORLD", "EXPANDED_WORLD", "_GRID_SIZES",
                     "EXPANDED_BRIDGES_ARE_LAND", "_expanded", "_coast_rows", "_on_land",
                     "_shore", "_trace", "_fixed_plots", "_expanded_ridges",
                     "_expanded_crest", "_expanded_plot_types", "_expanded_land_terrain",
                     "_expanded_terrain_types", "_floe_line", "ExpandedFeatureGenerator"}
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
            if name not in reworked:
                self.assertEqual(ast.dump(original), ast.dump(node), name)
        added = set(current) - {key(node) for node in baseline.body}
        tables = {name for name in added if name.startswith("_X_")}
        self.assertEqual(added - tables, diagnostics | expansion)
        self.assertGreater(len(tables), 20)

    def test_install_layout(self):
        self.assertTrue(INSTALLED.is_file())
        self.assertFalse((ROOT / "Equus.py").exists(),
                         "Keep one deployable Equus.py under PrivateMaps")

    def test_grid_sizes_and_load_sentinel(self):
        for atlas, sizes in enumerate(WORLD_SIZES):
            module = Environment(options=(0, 1, atlas)).load(INSTALLED)
            for index, cells in enumerate(sizes):
                self.assertEqual(module.getGridSize([index]), cells)
            self.assertEqual(module.getGridSize([-1]), [])
            self.assertEqual(module.getGridSize([99]), sizes[-1])
        # A game whose options hold no third entry is a Known World game.
        self.assertEqual(Environment(options=(0, 1)).load(INSTALLED).getGridSize([5]), (24, 26))
        # The Expanded Huge map is exactly AdvCiv 1.14's own Huge: 120 x 84 plots.
        self.assertEqual(EXPANDED_SIZES[5], (30, 21))
        for cells in EXPANDED_SIZES:
            self.assertTrue(1.4 < cells[0] / cells[1] < 1.55, cells)  # the picture is 1.5 : 1

    def test_options(self):
        for wrap, variation, atlas in itertools.product(range(3), range(3), range(2)):
            env = Environment(options=(wrap, variation, atlas))
            module = env.load(INSTALLED)
            self.assertEqual(module.getNumCustomMapOptions(), 3)
            self.assertEqual(module.getWrapX(), wrap != 0)
            self.assertEqual(module.getWrapY(), wrap == 2)
            self.assertEqual(module._variation(), (0.5, 1.0, 1.5)[variation])
            self.assertEqual(module._expanded(), atlas == EXPANDED)
            for index, choices in enumerate((3, 3, 2)):
                self.assertEqual(module.getNumCustomMapOptionValues([index]), choices)
                self.assertEqual(module.getCustomMapOptionDefault([index]), (0, 1, 0)[index])
                self.assertFalse(module.isRandomCustomMapOption([index]))
                self.assertTrue(module.getCustomMapOptionName([index]))
                for choice in range(choices):
                    self.assertTrue(module.getCustomMapOptionDescAt([index, choice]))
        module = Environment().load(INSTALLED)
        self.assertEqual((module.WORLD_WRAP, module.ATLAS_VARIATION, module.ATLAS_WORLD), (0, 1, 2))
        self.assertEqual(module.getCustomMapOptionName([2]), "Alternative Universe Expansions")
        self.assertEqual(module.getCustomMapOptionDescAt([2, module.KNOWN_WORLD]),
                         'Equestria "Known World"')
        self.assertEqual(module.getCustomMapOptionDescAt([2, module.EXPANDED_WORLD]),
                         'Equestria "Expanded"')
        for invalid in (-1, 3, 999):
            module = Environment(options=(invalid, invalid, invalid)).load(INSTALLED)
            self.assertEqual([module._option(index) for index in range(3)], [0, 1, 0])
            self.assertFalse(module._expanded())

    def check_logs(self, size, options, sea, enabled):
        """Diagnostics describe a finished run exactly and report no trouble."""
        self.assertEqual(enabled[6], "")
        self.assertNotIn("WARN", enabled[5])
        self.assertNotIn("ERROR", enabled[5])
        for stage in ("getGridSize", "generatePlotTypes",
                      "generateTerrainTypes", "addFeatures"):
            self.assertIn(stage + " BEGIN", enabled[5])
            self.assertIn(stage + " END", enabled[5])
        cells = cells_for(size, options)
        width, height = cells[0] * 4, cells[1] * 4
        self.assertIn("grid=%dx%d plots=%d sea_level=%d" %
                      (width, height, width * height, sea), enabled[5])
        for index, choice in enumerate(options):
            self.assertIn("option[%d] raw=%d effective=%d" % (index, choice, choice), enabled[5])
        for label, value in (("ocean", 0), ("land", 1), ("hills", 2), ("peak", 3)):
            self.assertIn("plot %s=%d" % (label, enabled[0].count(value)), enabled[5])
        for key, value in TERRAINS.items():
            self.assertIn("terrain %s id=%d count=%d" %
                          (key[len("TERRAIN_"):], value, enabled[1].count(value)), enabled[5])
        for label, values in (("terrain_ids", enabled[1]), ("feature_ids", enabled[2])):
            counts = ", ".join("%s:%d" % (value, values.count(value))
                               for value in sorted(set(values)))
            self.assertIn(label + "={" + counts + "}", enabled[5])
        self.assertEqual(len(enabled[0]), width * height)
        self.assertEqual(len(enabled[1]), width * height)
        self.assertTrue(set(enabled[0]).issubset({0, 1, 2, 3}))
        self.assertTrue(set(enabled[1]).issubset(set(TERRAINS.values()) | {20}))
        self.assertIn(0, enabled[0])
        self.assertTrue(any(p != 0 for p in enabled[0]))
        for plot_type, terrain_type in zip(enabled[0], enabled[1]):
            if plot_type == 0:
                self.assertEqual(terrain_type, 20)
        self.assertEqual(enabled[4], 0)

    def test_known_world_matches_baseline(self):
        """The default world is still, draw for draw, the map verified in Civ."""
        cases = {(size, 0, 1, 1) for size in range(len(SIZES))}
        cases.update((0, wrap, variation, 1)
                     for wrap, variation in itertools.product(range(3), repeat=2))
        cases.update((3, 0, variation, sea)
                     for variation, sea in itertools.product(range(3), repeat=2))
        for size, wrap, variation, sea in sorted(cases):
            with self.subTest(size=size, wrap=wrap, variation=variation, sea=sea):
                options = (wrap, variation, KNOWN)
                baseline = generate(BASELINE, size, (wrap, variation), sea)
                disabled = generate(INSTALLED, size, options, sea, diagnostics=False)
                enabled = generate(INSTALLED, size, options, sea, diagnostics=True)
                legacy = generate(INSTALLED, size, (wrap, variation), sea)
                self.assertEqual(baseline[:5], disabled[:5])
                self.assertEqual(baseline[:5], enabled[:5])
                self.assertEqual(baseline[:5], legacy[:5])
                self.assertEqual(disabled[5:], ("", ""))
                self.assertFalse(any("expanded" in call[1] for call in disabled[3]))
                self.check_logs(size, options, sea, enabled)

    def test_expanded_world_generation(self):
        cases = {(size, 0, 1, 1) for size in range(len(EXPANDED_SIZES))}
        cases.update((0, wrap, variation, 1)
                     for wrap, variation in itertools.product(range(3), repeat=2))
        cases.update((3, 0, variation, sea)
                     for variation, sea in itertools.product(range(3), repeat=2))
        for size, wrap, variation, sea in sorted(cases):
            with self.subTest(size=size, wrap=wrap, variation=variation, sea=sea):
                options = (wrap, variation, EXPANDED)
                disabled = generate(INSTALLED, size, options, sea, diagnostics=False)
                enabled = generate(INSTALLED, size, options, sea, diagnostics=True)
                self.assertEqual(disabled[:5], enabled[:5])
                self.assertEqual(disabled[5:], ("", ""))
                self.check_logs(size, options, sea, enabled)
                # Its draws are its own: none of the Known World's labels.
                labels = {call[1] for call in disabled[3]} - {"stub forest", "stub jungle"}
                self.assertTrue(labels)
                self.assertTrue(all("expanded" in label for label in labels), labels)
                land = sum(1 for plot in disabled[0] if plot) / float(len(disabled[0]))
                self.assertTrue(.45 < land < .72, land)  # the picture is three-fifths land
                self.assertEqual(set(disabled[2]), {-1, 30, 31, 32})

    def test_seed_changes_map_without_logging_changes(self):
        for atlas in (KNOWN, EXPANDED):
            options = (0, 1, atlas)
            first = generate(INSTALLED, options=options, seed=17, diagnostics=True)
            repeat = generate(INSTALLED, options=options, seed=17, diagnostics=False)
            second = generate(INSTALLED, options=options, seed=18, diagnostics=True)
            self.assertEqual(first[:5], repeat[:5])
            self.assertNotEqual(first[0], second[0])

    def test_expanded_variation_and_sea_level_change_the_map(self):
        base = generate(INSTALLED, 3, (0, 1, EXPANDED), 1)
        land = lambda result: sum(1 for plot in result[0] if plot)
        self.assertNotEqual(base[0], generate(INSTALLED, 3, (0, 0, EXPANDED), 1)[0])
        self.assertNotEqual(base[0], generate(INSTALLED, 3, (0, 2, EXPANDED), 1)[0])
        low = generate(INSTALLED, 3, (0, 1, EXPANDED), 0)
        high = generate(INSTALLED, 3, (0, 1, EXPANDED), 2)
        self.assertGreater(land(low), land(base))
        self.assertGreater(land(base), land(high))

    def test_expanded_tables_are_well_formed(self):
        module = Environment().load(INSTALLED)
        self.assertGreater(len(module._X_SHORES), 30)
        for shore in module._X_SHORES:
            self.assertGreaterEqual(len(shore), 2)
            self.assertTrue(any(west < east for south, west, east in shore))
            for index, (south, west, east) in enumerate(shore):
                # west == east is a cape that narrows to a point
                self.assertTrue(-.1 <= south <= 1.1 and 0 <= west <= east <= 1, shore[index])
                if index:
                    self.assertGreater(south, shore[index - 1][0], shore[index])
        for table in ("_X_ISLES", "_X_LAKES", "_X_BASINS", "_X_PASSES", "_X_HAVENS",
                      "_X_SNOWFIELDS", "_X_TUNDRA", "_X_DRY_BASINS", "_X_STEPPES",
                      "_X_GRASSY_LOWLANDS", "_X_WET_WOODS", "_X_WOODLANDS"):
            for east, south, east_radius, south_radius in getattr(module, table):
                self.assertTrue(0 <= east <= 1 and 0 <= south <= 1, table)
                self.assertTrue(0 < east_radius < .2 and 0 < south_radius < .2, table)
        for radius, strength, path in module._X_RANGES:
            self.assertTrue(0 < radius < .05 and 0 < strength <= 1)
            for first, second in zip(path, path[1:]):
                self.assertNotEqual(first, second, "a zero-length ridge divides by zero")
        paths = list(module._X_STRAITS) + list(module._X_LAND_LINKS)
        for causeway, channel in module._X_BRIDGES:
            paths += [causeway, channel]
        for path in paths:
            self.assertGreaterEqual(len(path), 2)
            for east, south in path:
                self.assertTrue(0 <= east <= 1 and 0 <= south <= 1, path)

    def test_expanded_geography(self):
        """Seas divide and necks join alike from Duel to XXL, at every variation
        and sea level, with the bridges as causeways and as straits."""
        cases = set(itertools.product(range(len(EXPANDED_SIZES)), (1,), (1,), (1234, 7)))
        cases.update(itertools.product((0, 1, 3, 5), range(3), range(3), (99,)))
        for size, variation, sea, seed in sorted(cases):
            for bridges_are_land in (True, False):
                with self.subTest(size=size, variation=variation, sea=sea, seed=seed,
                                  bridges_are_land=bridges_are_land):
                    self.assertEqual(
                        geography_problems(size, variation, sea, seed, bridges_are_land), [])

    def test_expanded_climate(self):
        """Each named region gets its biome on a Huge map."""
        module = Environment().load(INSTALLED)
        cells = EXPANDED_SIZES[5]
        width, height = cells[0] * 4, cells[1] * 4
        plots, terrains, features = generate(INSTALLED, 5, (0, 1, EXPANDED))[:3]
        def census(table, row):
            east, south, east_radius, south_radius = getattr(module, table)[row]
            found = []
            for y in range(height):
                for x in range(width):
                    if plots[y * width + x] and module._in_oval(
                            (x + .5) / width, 1 - (y + .5) / height,
                            east, south, east_radius * .7, south_radius * .7):
                        found.append((terrains[y * width + x], features[y * width + x]))
            self.assertGreater(len(found), 5, (table, row))
            return found
        def share(found, terrain=None, feature=None):
            hits = [1 for t, f in found if (terrain is None or t == TERRAINS["TERRAIN_" + terrain])
                    and (feature is None or f == feature)]
            return len(hits) / float(len(found))
        self.assertGreater(share(census("_X_DRY_BASINS", 6), "DESERT"), .7)   # Saddle Arabia
        self.assertGreater(share(census("_X_DRY_BASINS", 5), "DESERT"), .7)   # Bone Dry Desert
        self.assertGreater(share(census("_X_DRY_BASINS", 13), "DESERT"), .7)  # Breezewood
        self.assertGreater(share(census("_X_SNOWFIELDS", 5), "SNOW"), .7)     # Antleria
        self.assertGreater(share(census("_X_GRASSY_LOWLANDS", 1), "GRASS"), .9)  # Fields of Forever
        self.assertGreater(share(census("_X_WET_WOODS", 3), "GRASS"), .9)     # Zebrica's jungle
        self.assertGreater(share(census("_X_WET_WOODS", 3), feature=31), .3)
        self.assertGreater(share(census("_X_WET_WOODS", 1), feature=31), .3)  # Amarezonia
        self.assertEqual(share(census("_X_DRY_BASINS", 6), feature=31), 0)
        polar = [terrains[i] for i in range(width * 2) if plots[i]]         # Agarica's shore
        self.assertTrue(polar and set(polar) <= {TERRAINS["TERRAIN_SNOW"], TERRAINS["TERRAIN_TUNDRA"]})

    def test_pack_ice_keeps_to_the_poles_and_off_the_lanes(self):
        for size in (0, 3, 6):
            cells = EXPANDED_SIZES[size]
            width, height = cells[0] * 4, cells[1] * 4
            env = Environment(width, height, (0, 1, EXPANDED))
            lanes = env.load(INSTALLED)._fixed_plots(width, height)[0]
            plots, terrains, features = generate(INSTALLED, size, (0, 1, EXPANDED))[:3]
            ice = [(i % width, i // width) for i, feature in enumerate(features) if feature == 30]
            self.assertTrue(ice)
            for x, y in ice:
                south = 1 - (y + .5) / height
                self.assertTrue(south < .04 or south > .84, south)
                self.assertNotIn((x, y), lanes)
                self.assertEqual(plots[y * width + x], 0)

    def test_load_sentinel_diagnostics(self):
        env = Environment()
        module = env.load(INSTALLED, True)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(module.getGridSize([-1]), [])
        self.assertIn("load sentinel; keep saved dimensions", output.getvalue())
        self.assertEqual(env.rand.calls, [])

    def test_diagnostic_size_mismatch_is_reported_without_rewriting_result(self):
        for options, dependency in (((0, 1, KNOWN), "_plot_types"),
                                    ((0, 1, EXPANDED), "_expanded_plot_types")):
            env = Environment(options=options)
            module = env.load(INSTALLED, True)
            result = [PlotTypes.PLOT_LAND]
            setattr(module, dependency, lambda *args: result)
            errors = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
                self.assertIs(module.generatePlotTypes(), result)
            self.assertIn("ERROR unexpected output-array size", errors.getvalue())
            self.assertEqual(env.rand.calls, [])

    def test_generation_errors_propagate(self):
        class SentinelError(Exception):
            pass
        stages = ((KNOWN, "generatePlotTypes", "_plot_types"),
                  (KNOWN, "generateTerrainTypes", "_land_terrain"),
                  (KNOWN, "addFeatures", "EquusFeatureGenerator"),
                  (EXPANDED, "generatePlotTypes", "_expanded_plot_types"),
                  (EXPANDED, "generateTerrainTypes", "_expanded_land_terrain"),
                  (EXPANDED, "addFeatures", "ExpandedFeatureGenerator"))
        for diagnostics in (False, True):
            for atlas, callback, dependency in stages:
                with self.subTest(diagnostics=diagnostics, atlas=atlas, callback=callback):
                    env = Environment(options=(0, 1, atlas))
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
        for options, cells in (((0, 1, KNOWN), SIZES[0]), ((0, 1, EXPANDED), EXPANDED_SIZES[0])):
            expected = generate(INSTALLED, options=options, diagnostics=False)
            env = Environment(cells[0] * 4, cells[1] * 4, options, sea=1)
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
                     ast.YieldFrom, ast.Match, ast.AnnAssign, ast.IfExp,
                     ast.MatMult)
        later_builtins = {"any", "all", "next", "bin", "format", "bytearray", "bytes", "print"}
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
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, later_builtins, "needs Python 2.5 or later")
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("min", "max", "sorted"):
                self.assertFalse(node.keywords, "min/max key= needs Python 2.5")
        self.assertNotIn("from __future__ import", source)

    def test_python24_draws_the_same_maps(self):
        """With EQUUS_PYTHON24 set to a CPython 2.4 binary, its maps must match
        this harness plot for plot: integer division, rounding, set ordering
        and the rest cannot have crept into either world."""
        import os
        import subprocess
        interpreter = os.environ.get("EQUUS_PYTHON24")
        if not interpreter:
            self.skipTest("set EQUUS_PYTHON24=/path/to/python2.4 to compare interpreters")
        report = subprocess.run([interpreter, str(ROOT / "tests" / "check_python24.py"), "--digests"],
                                capture_output=True, text=True, check=True).stdout
        lines = [line.split() for line in report.splitlines() if line.startswith("digest ")]
        self.assertEqual(len(lines), 2 * len(SIZES))
        for unused, atlas, size, wrap, variation, sea, value in lines:
            options = (int(wrap), int(variation), int(atlas))
            here = generate(INSTALLED, int(size), options, int(sea))
            self.assertEqual(map_digest(here), value, (atlas, size))


if __name__ == "__main__":
    unittest.main(verbosity=2)
