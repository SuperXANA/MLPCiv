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


# Climates as in the stock CIV4ClimateInfo.xml, which AdvCiv 1.14 does not
# replace: desert percent change, jungle latitude, hill range, peak percent,
# then the snow, tundra, grass, desert bottom and desert top latitude changes,
# ice latitude, random ice latitude. The sixth row is not in the game. It
# stands for a climate that a mod might add, and has gentler hills than
# Temperate so that the script's wearing-down rules are exercised too.
TEMPERATE, TROPICAL, ARID, ROCKY, COLD, GENTLE = range(6)
CLIMATES = (
    ("CLIMATE_TEMPERATE", 0, 5, 5, 25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.95, 0.25),
    ("CLIMATE_TROPICAL", -10, 2, 5, 25, 0.1, 0.1, 0.0, 0.0, 0.0, 0.95, 0.20),
    ("CLIMATE_ARID", 20, 6, 5, 25, 0.0, 0.0, 0.0, -0.1, 0.1, 0.95, 0.20),
    ("CLIMATE_ROCKY", 0, 5, 7, 35, -0.025, -0.05, 0.0, 0.0, -0.05, 0.95, 0.25),
    ("CLIMATE_COLD", -10, 6, 5, 25, -0.1, -0.15, 0.0, 0.0, -0.1, 0.9, 0.5),
    ("CLIMATE_TEST_GENTLE", -5, 4, 3, 15, 0.05, 0.05, 0.0, 0.0, 0.0, 0.97, 0.20),
)
CLIMATE_NAMES = ("Temperate", "Tropical", "Arid", "Rocky", "Cold", "Gentle (test)")


class ClimateInfo:
    def __init__(self, row):
        self.row = row

    def getDesertPercentChange(self): return self.row[1]
    def getJungleLatitude(self): return self.row[2]
    def getHillRange(self): return self.row[3]
    def getPeakPercent(self): return self.row[4]
    def getSnowLatitudeChange(self): return self.row[5]
    def getTundraLatitudeChange(self): return self.row[6]
    def getGrassLatitudeChange(self): return self.row[7]
    def getDesertBottomLatitudeChange(self): return self.row[8]
    def getDesertTopLatitudeChange(self): return self.row[9]
    def getIceLatitude(self): return self.row[10]
    def getRandIceLatitude(self): return self.row[11]


class World:
    def __init__(self, width, height, options, sea, climate=TEMPERATE):
        self.width, self.height = width, height
        self.options, self.sea, self.climate = options, sea, climate
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

    def getClimate(self):
        return self.climate

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
    def __init__(self, width=28, height=32, options=(0, 1), sea=0, seed=1234,
                 climate=TEMPERATE):
        self.integer_divisions = 0
        self.world = World(width, height, options, sea, climate)
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
        return SeaLevelInfo((-8, 0, 6)[sea])  # AdvCiv 1.14's CIV4SeaLevelInfo.xml

    def getClimateInfo(self, index):
        if 0 <= index < len(CLIMATES):
            return ClimateInfo(CLIMATES[index])
        return None  # CyGlobalContext: NULL for an index it does not hold

    def getInfoTypeForString(self, key):
        if key.startswith("CLIMATE_"):
            names = [row[0] for row in CLIMATES]
            if key in names:
                return names.index(key)
            return -1
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


def land_bridge(module):
    """A tweak for generate(): the Known World as it was before the Trottingham
    strait, which is the map that the pinned baseline draws."""
    module._TROTTINGHAM_STRAIT = ()


def nearest_land(plots, width, height, place, land=True, reach=3):
    """The plot of the wanted kind nearest an atlas point, within a few plots:
    a named point may fall in a lake or, for water, on an islet."""
    x0 = min(width - 1, int(place[0] * width))
    y0 = min(height - 1, int((1 - place[1]) * height))
    for unused, x, y in sorted((abs(dx) + abs(dy), x0 + dx, y0 + dy)
                               for dx in range(-reach, reach + 1)
                               for dy in range(-reach, reach + 1)):
        if 0 <= x < width and 0 <= y < height and (plots[y * width + x] != 0) == land:
            return (x, y)
    return None


def cells_for(world_size, options):
    atlas = KNOWN
    if len(options) > 2 and options[2] == EXPANDED:
        atlas = EXPANDED
    return WORLD_SIZES[atlas][world_size]


def generate(path, world_size=0, options=(0, 1), sea=1, seed=1234,
             diagnostics=False, tweak=None, climate=TEMPERATE):
    cells = cells_for(world_size, options)
    env = Environment(cells[0] * 4, cells[1] * 4, options, sea, seed, climate)
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


def on_map(module, place):
    """A place of the picture, moved as the script's sea room moves it."""
    return module._to_map(module._sea_rooms(), place[0], place[1])


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


def geography_problems(world_size, variation, sea, seed, bridges_are_land,
                       climate=TEMPERATE):
    """Generate one Expanded world and list everything wrong with its layout."""
    loaded = []
    def tweak(module):
        module.EXPANDED_BRIDGES_ARE_LAND = bridges_are_land
        loaded.append(module)
    cells = EXPANDED_SIZES[world_size]
    width, height = cells[0] * 4, cells[1] * 4
    result = generate(INSTALLED, world_size, (0, variation, EXPANDED), sea, seed, tweak=tweak,
                      climate=climate)
    plots, features = result[0], result[2]
    problems = []
    spot, water = {}, {}
    for name, place in PLACES.items():
        spot[name] = nearest(plots, width, height, on_map(loaded[0], place), True)
        if spot[name] is None:
            problems.append("no land at " + name)
    for name, place in SEAS.items():
        water[name] = nearest(plots, width, height, on_map(loaded[0], place), False)
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
        """Every Known World definition is untouched, bar the seven that had
        to learn about a second atlas, about climates or about the strait.
        _plot_types and every Known World table are among the untouched. (The
        Known World's results under the Temperate climate are compared with
        the verified baseline in test_known_world_matches_baseline and
        test_strait_changes_only_the_strait.)"""
        baseline = ast.parse(BASELINE.read_bytes())
        installed = ast.parse(INSTALLED.read_bytes())
        wrapped = {"getGridSize", "generatePlotTypes", "generateTerrainTypes", "addFeatures"}
        reworked = wrapped | {"CvMapOptions", "getDescription", "isClimateMap"}
        diagnostics = {"EQUUS_DIAGNOSTICS", "_diagnostic_write", "_diagnostic_counts",
                       "_diagnostic_begin", "_diagnostic_end", "_diagnostic_error",
                       "_diagnostic_stage"}
        expansion = {"ATLAS_WORLD", "KNOWN_WORLD", "EXPANDED_WORLD", "_GRID_SIZES",
                     "EXPANDED_BRIDGES_ARE_LAND", "_expanded", "_coast_rows", "_on_land",
                     "_shore", "_sea_rooms", "_room_pull", "_room_to_atlas",
                     "_to_atlas", "_to_map", "_trace",
                     "_fixed_plots", "_expanded_ridges",
                     "_expanded_crest", "_expanded_plot_types", "_expanded_land_terrain",
                     "_expanded_terrain_types", "_floe_line", "ExpandedFeatureGenerator"}
        climates = {"_STOCK_TEMPERATE", "_KNOWN_ASPECT", "_between", "_climate_numbers",
                    "_Climate", "_grown", "_Biomes", "_known_climate_terrain",
                    "_known_level_ground", "_AROUND", "_way_through", "_uplift",
                    "AtlasFeatureGenerator",
                    "KnownClimateFeatureGenerator"}
        strait = {"_TROTTINGHAM_STRAIT", "_TROTTINGHAM_LANES", "KNOWN_BRIDGE_IS_LAND",
                  "_TROTTINGHAM_BRIDGE", "_GRIFFISH_ISLES", "_known_strait"}
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
        self.assertEqual(added - tables, diagnostics | expansion | climates | strait)
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
        self.assertIn("grid=%dx%d plots=%d sea_level=%d climate=0\n" %
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
        """With the Trottingham strait's table emptied, the Known World is
        still, draw for draw, the map verified in Civ. (What the strait
        changes is pinned down in test_strait_changes_only_the_strait.)"""
        cases = {(size, 0, 1, 1) for size in range(len(SIZES))}
        cases.update((0, wrap, variation, 1)
                     for wrap, variation in itertools.product(range(3), repeat=2))
        cases.update((3, 0, variation, sea)
                     for variation, sea in itertools.product(range(3), repeat=2))
        for size, wrap, variation, sea in sorted(cases):
            with self.subTest(size=size, wrap=wrap, variation=variation, sea=sea):
                options = (wrap, variation, KNOWN)
                baseline = generate(BASELINE, size, (wrap, variation), sea)
                disabled = generate(INSTALLED, size, options, sea, diagnostics=False,
                                    tweak=land_bridge)
                enabled = generate(INSTALLED, size, options, sea, diagnostics=True,
                                   tweak=land_bridge)
                legacy = generate(INSTALLED, size, (wrap, variation), sea, tweak=land_bridge)
                self.assertEqual(baseline[:5], disabled[:5])
                self.assertEqual(baseline[:5], enabled[:5])
                self.assertEqual(baseline[:5], legacy[:5])
                self.assertEqual(disabled[5:], ("", ""))
                self.assertFalse(any("expanded" in call[1] for call in disabled[3]))
                self.check_logs(size, options, sea, enabled)

    def test_strait_changes_only_the_strait(self):
        """The default Known World, with the strait: the script draws exactly
        the baseline's random numbers, and every plot is either what the
        baseline has there (plot type, terrain and feature) or belongs to the
        sets that _known_strait() returns. Those are ocean without a feature,
        or the flat land of the causeway when that is switched on."""
        cases = {(size, 1, 1) for size in range(len(SIZES))}
        cases.update((size, variation, sea) for size in (0, 3, 6)
                     for variation, sea in itertools.product(range(3), repeat=2))
        for bridge_is_land in (False, True):
            loaded = []
            def tweak(module):
                module.KNOWN_BRIDGE_IS_LAND = bridge_is_land
                loaded.append(module)
            for size, variation, sea in sorted(cases):
                with self.subTest(size=size, variation=variation, sea=sea,
                                  bridge_is_land=bridge_is_land):
                    cells = SIZES[size]
                    width, height = cells[0] * 4, cells[1] * 4
                    baseline = generate(BASELINE, size, (0, variation), sea)
                    quiet = generate(INSTALLED, size, (0, variation, KNOWN), sea, tweak=tweak)
                    logged = generate(INSTALLED, size, (0, variation, KNOWN), sea, tweak=tweak,
                                      diagnostics=True)
                    self.assertEqual(quiet[:5], logged[:5])
                    self.assertEqual(quiet[5:], ("", ""))
                    self.check_logs(size, (0, variation, KNOWN), sea, logged)
                    self.assertEqual(quiet[3], baseline[3])  # the complete RNG trace
                    shift = (-.008, 0.0, .006)[sea]
                    water, causeway = loaded[-1]._known_strait(width, height, shift)
                    self.assertTrue(water)
                    self.assertEqual(bool(causeway), bridge_is_land)
                    self.assertFalse(water & causeway)
                    changed = 0
                    for index in range(width * height):
                        spot = (index % width, index // width)
                        now = (quiet[0][index], quiet[1][index], quiet[2][index])
                        if spot in water:
                            self.assertEqual(now, (0, 20, -1), spot)
                        elif spot in causeway:
                            self.assertEqual(now[0], 1, spot)
                        else:
                            self.assertEqual(now, (baseline[0][index], baseline[1][index],
                                                   baseline[2][index]), spot)
                        changed += now[0] != baseline[0][index]
                    self.assertGreater(changed, 3)

    def test_strait_tables_and_sea_level(self):
        """The strait's tables are well formed and lie where the picture has
        the water; its lanes are present whatever the sea level; a higher sea
        never narrows it; the shipped lanes keep off the Griffish Isles'
        core; and an emptied table switches all of it off."""
        module = Environment().load(INSTALLED)
        table = module._TROTTINGHAM_STRAIT
        self.assertLess(table[0][0], 0)
        self.assertTrue(.19 < table[-1][0] < .215)  # it stops at the Griffish Isles' north tip
        for index, (south, west, east) in enumerate(table):
            self.assertTrue(0 < west < east < 1, table[index])
            if index:
                self.assertGreater(south, table[index - 1][0])
        # The banks against the channel as it was traced from the official
        # picture, twice and independently (by eye and by pixel colour): west
        # and east edge of the painted water with its pale rim. A mistyped
        # bank is caught here. (v .14 is left out: a dead-end lobe there makes
        # "the west bank" a matter of choice.)
        def banks(south):
            for (av, aw, ae), (bv, bw, be) in zip(table, table[1:]):
                if av <= south <= bv:
                    t = (south - av) / (bv - av)
                    return aw + (bw - aw) * t, ae + (be - ae) * t
        tracing = ((.075, .542, .777), (.090, .712, .748), (.100, .729, .779),
                   (.110, .760, .809), (.120, .758, .815), (.130, .776, .834),
                   (.150, .823, .851), (.160, .826, .850), (.170, .828, .847),
                   (.176, .830, .840), (.190, .818, .847), (.200, .807, .856))
        for south, west, east in tracing:
            found = banks(south)
            self.assertLess(abs(found[0] - west), .012, (south, found))
            self.assertLess(abs(found[1] - east), .012, (south, found))
        for south, west, east in table:
            if south < .07:  # painted nowhere: the sea north of the picture's horizon
                self.assertTrue(.53 <= west < east <= .79, (south, west, east))
        for path in module._TROTTINGHAM_LANES + (module._TROTTINGHAM_BRIDGE,):
            for (ax, av), (bx, bv) in zip(path, path[1:]):
                self.assertNotEqual((ax, av), (bx, bv))
            for east, south in path:
                self.assertTrue(0 <= east <= 1 and 0 <= south <= 1)
        self.assertEqual(module._TROTTINGHAM_LANES[0][0][1], 0)       # from the top edge ...
        self.assertEqual(module._TROTTINGHAM_LANES[0][-1], (.800, .290))  # ... to open sea
        self.assertIs(module._GRIFFISH_ISLES, module._ISLES[2])
        self.assertIs(module.KNOWN_BRIDGE_IS_LAND, False)
        for size in range(len(SIZES)):
            cells = SIZES[size]
            width, height = cells[0] * 4, cells[1] * 4
            low, normal, high = [module._known_strait(width, height, shift)[0]
                                 for shift in (-.008, 0.0, .006)]
            self.assertTrue(low <= normal <= high, size)
            self.assertLess(len(low), len(high), size)
            # All of it in the north-east, and of a sensible size.
            for water in (low, normal, high):
                for x, y in water:
                    east, south = (x + .5) / width, 1 - (y + .5) / height
                    self.assertTrue(.50 < east < .89 and south < .31, (size, x, y))
                self.assertTrue(.015 < len(water) / float(width * height) < .055, size)
            core = (int(.810 * width), int((1 - .225) * height))
            lanes = set()
            for path in module._TROTTINGHAM_LANES:
                traced = set()
                module._trace(traced, path, width, height, True, ())
                self.assertNotIn(core, traced, size)  # as shipped, no lane needs the safeguard
                lanes |= traced
            for water in (low, normal, high):
                self.assertTrue(lanes <= water, size)
                self.assertNotIn(core, water)
            # The first lane alone is a chain from the top row with no diagonal step.
            first = set()
            module._trace(first, module._TROTTINGHAM_LANES[0], width, height, True, ())
            self.assertNotIn(core, first)
            self.assertTrue(any(y == height - 1 for x, y in first))
            start = [spot for spot in first if spot[1] == height - 1][0]
            seen, queue = {start}, [start]
            while queue:
                x, y = queue.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + dx, y + dy) in first and (x + dx, y + dy) not in seen:
                        seen.add((x + dx, y + dy))
                        queue.append((x + dx, y + dy))
            self.assertEqual(seen, first, size)
        off = Environment().load(INSTALLED)
        off._TROTTINGHAM_STRAIT = ()
        off.KNOWN_BRIDGE_IS_LAND = True
        self.assertEqual(off._known_strait(96, 104, 0.0), (set(), set()))

    def test_strait_edits_that_the_comments_invite(self):
        """Deleting the second lane's two lines from the source, as its
        comment says one may, leaves a script that loads and still parts the
        continents. And the two safeguards for redrawn tables work: a lane
        drawn straight through the Griffish Isles does not sink the isle's
        core, and a table carried south over the isle keeps off its oval."""
        import tempfile
        lines = INSTALLED.read_text(encoding="ascii").split("\n")
        first = [index for index, line in enumerate(lines)
                 if line.startswith("    ((.837,.190),")]
        self.assertEqual(len(first), 1)
        self.assertEqual(lines[first[0] + 1].strip(), "(.800,.290)),")
        self.assertEqual(lines[first[0] + 2], ")")
        edited = lines[:first[0]] + lines[first[0] + 2:]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Equus.py"
            path.write_text("\n".join(edited), encoding="ascii")
            for size, sea in ((0, 0), (3, 0), (5, 1)):
                cells = SIZES[size]
                width, height = cells[0] * 4, cells[1] * 4
                loaded = []
                plots = generate(path, size, (0, 2, KNOWN), sea, 13, tweak=loaded.append)[0]
                self.assertEqual(len(loaded[0]._TROTTINGHAM_LANES), 1)
                west = flood(plots, width, height, nearest_land(plots, width, height, (.40, .32)),
                             (1, 2, 3))
                self.assertNotIn(nearest_land(plots, width, height, (.93, .33)), west)
        for size in range(len(SIZES)):
            cells = SIZES[size]
            width, height = cells[0] * 4, cells[1] * 4
            core = (int(.810 * width), int((1 - .225) * height))
            module = Environment().load(INSTALLED)
            module._TROTTINGHAM_LANES = (((.810, .180), (.810, .270)),)
            traced = set()
            module._trace(traced, module._TROTTINGHAM_LANES[0], width, height, True, ())
            self.assertIn(core, traced)              # the lane does run over the core ...
            self.assertNotIn(core, module._known_strait(width, height, 0.0)[0])  # ... which stays
            module._TROTTINGHAM_LANES = ()
            module._TROTTINGHAM_STRAIT = module._TROTTINGHAM_STRAIT + ((.260, .780, .860),)
            cx, cv, rx, rv = module._GRIFFISH_ISLES
            rx, rv = max(rx, .75 / width), max(rv, .75 / height)
            water = module._known_strait(width, height, 0.0)[0]
            self.assertTrue(any(1 - (y + .5) / height > .215 for x, y in water), size)
            for x, y in water:
                self.assertFalse(module._in_oval((x + .5) / width, 1 - (y + .5) / height,
                                                 cx, cv, rx, rv), (size, x, y))
            def redrawn(module):
                module._TROTTINGHAM_LANES = (((.810, .180), (.810, .270)),)
                module._TROTTINGHAM_STRAIT = module._TROTTINGHAM_STRAIT + ((.260, .780, .860),)
            plots = generate(INSTALLED, size, (0, 1, KNOWN), tweak=redrawn)[0]
            self.assertNotEqual(plots[core[1] * width + core[0]], 0, size)

    def test_known_world_has_three_continents(self):
        """Equestria, Griffonstone and the Dragon lands are three land areas
        at every size, variation and sea level, a ship can sail from the
        Celestial Sea through the strait to the top edge of the map, and
        Trottingham is an island. With the causeway switched on, the first
        two are joined and can be walked between without crossing a peak, no
        ship passes, the two seas do not touch even at a corner, the causeway
        is flat land (under Rocky too) and Trottingham is still an island.
        Before the strait (table emptied) they were one land area."""
        def survey(size, variation, sea, seed, tweak, climate=TEMPERATE):
            cells = SIZES[size]
            width, height = cells[0] * 4, cells[1] * 4
            loaded = []
            def both(module):
                if tweak is not None:
                    tweak(module)
                loaded.append(module)
            plots = generate(INSTALLED, size, (0, variation, KNOWN), sea, seed, tweak=both,
                             climate=climate)[0]
            near = lambda place, land: nearest_land(plots, width, height, place, land)
            equestria, griffonstone, dragons = [near(place, True) for place in
                                                ((.40, .32), (.93, .33), (.93, .62))]
            area = flood(plots, width, height, equestria, (1, 2, 3))
            east = flood(plots, width, height, griffonstone, (1, 2, 3))
            celestial = near((.78, .30), False)
            ships = flood(plots, width, height, celestial, (0,), (), True)
            core = (int(.810 * width), int((1 - .225) * height))
            shift = (-.008, 0.0, .006)[sea]
            causeway_plots = loaded[0]._known_strait(width, height, shift)[1]
            # On foot (no peaks) from Equestria: does the walk reach the far
            # side of the strait, anywhere on Griffonstone's part of the map?
            on_foot = flood(plots, width, height, equestria, (1, 2))
            return {"joined": griffonstone in area,
                    "walkable": any(x >= int(.88 * width) and y >= int(.55 * height)
                                    for x, y in on_foot),
                    "dragons apart": dragons not in area and dragons not in east,
                    "ships reach the top": any((x, height - 1) in ships for x in range(width)),
                    # Water north of the strait's narrows and the Celestial
                    # Sea: one body even by the loosest rule (touching at a
                    # corner), or two.
                    "one sea": near((.70, .03), False) in flood(plots, width, height,
                                                                celestial, (0,)),
                    "causeway is flat": all(plots[y * width + x] == 1
                                            for x, y in causeway_plots),
                    "isle": plots[core[1] * width + core[0]] != 0 and core not in area
                            and core not in east}
        def causeway(module):
            module.KNOWN_BRIDGE_IS_LAND = True
        cases = set(itertools.product(range(len(SIZES)), range(3), range(3), (11,)))
        cases.update(itertools.product(range(len(SIZES)), (2,), (0,), (12, 13, 14)))  # Lively, low sea
        for size, variation, sea, seed in sorted(cases):
            with self.subTest(size=size, variation=variation, sea=sea, seed=seed):
                self.assertEqual(survey(size, variation, sea, seed, None),
                                 {"joined": False, "walkable": False, "dragons apart": True,
                                  "ships reach the top": True, "one sea": True,
                                  "causeway is flat": True, "isle": True})
        # The causeway. Small maps get more seeds: an earlier causeway ended
        # against peaks in about one Duel world in a hundred, and on Tiny
        # maps it landed on the Griffish Isles.
        bridged = set(itertools.product(range(len(SIZES)), (0, 2), (0, 2), (21,)))
        bridged.update(itertools.product((0, 1), range(3), (0, 2),
                                         (203, 212, 9550471, 31, 32, 33, 34, 35)))
        for size, variation, sea, seed in sorted(bridged):
            for climate in (TEMPERATE, ROCKY):
                if climate == ROCKY and seed not in (21, 203, 212):
                    continue
                with self.subTest(size=size, variation=variation, sea=sea, seed=seed,
                                  causeway=True, climate=CLIMATE_NAMES[climate]):
                    self.assertEqual(survey(size, variation, sea, seed, causeway, climate),
                                     {"joined": True, "walkable": True, "dragons apart": True,
                                      "ships reach the top": False, "one sea": False,
                                      "causeway is flat": True, "isle": True})
        for size, variation, sea, seed in sorted(itertools.product(
                range(len(SIZES)), (0, 2), (0, 2), (21,))):
            with self.subTest(size=size, variation=variation, sea=sea, before=True):
                found = survey(size, variation, sea, seed, land_bridge)
                self.assertEqual((found["joined"], found["dragons apart"],
                                  found["ships reach the top"]), (True, True, False))
        for size in (0, 3, 6):  # a Rocky climate does not close the strait
            self.assertFalse(survey(size, 1, 1, 31, None, ROCKY)["joined"])
            self.assertTrue(survey(size, 1, 1, 31, None, ROCKY)["ships reach the top"])

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
        for extra, rigid, fade, line in module._X_SEA_ROOM:
            self.assertTrue(0 <= extra < rigid < fade < .5)
            self.assertLess(extra / (fade - rigid), .5, "the squeeze must stay gentle")
            self.assertLess(extra, module._X_SEA_ROOM_EASE)
            for first, second in zip(line, line[1:]):
                self.assertNotEqual(first, second, "a zero-length segment divides by zero")
            for east, south in line:
                self.assertTrue(0 <= east <= 1 and 0 <= south <= 1, line)
        paths = list(module._X_STRAITS) + list(module._X_LAND_LINKS)
        for causeway, channel in module._X_BRIDGES:
            paths += [causeway, channel]
        for path in paths:
            self.assertGreaterEqual(len(path), 2)
            for east, south in path:
                self.assertTrue(0 <= east <= 1 and 0 <= south <= 1, path)

    def test_sea_room_parts_the_shores(self):
        """_X_SEA_ROOM widens each sea by twice its `extra`, moves the picture
        without folding it, leaves the bridges alone and can be switched off."""
        module = Environment().load(INSTALLED)
        rooms = module._sea_rooms()
        self.assertEqual(len(rooms), len(module._X_SEA_ROOM))
        extra, rigid, fade, line = module._X_SEA_ROOM[0]
        self.assertIs(line, module._X_CELESTIAL_SEA)
        self.assertIs(module._X_SEA_ROOM[1][3], module._X_INLAND_SEA)
        self.assertIn(module._X_CELESTIAL_SEA, module._X_STRAITS)
        self.assertIn(module._X_INLAND_SEA, module._X_STRAITS)
        def line_at(path, south):
            for (ax, av), (bx, bv) in zip(path, path[1:]):
                if av <= south <= bv:
                    return ax + (bx - ax) * (south - av) / (bv - av)
        # Beside a straight stretch of the Celestial Sea.
        centre = line_at(line, .40)
        self.assertIsNone(module._to_atlas(rooms, centre + extra * .5, .40))
        self.assertIsNone(module._to_atlas(rooms, centre - extra * .5, .40))
        east = module._to_atlas(rooms, centre + .05, .40)
        west = module._to_atlas(rooms, centre - .05, .40)
        self.assertAlmostEqual(east[0], centre + .05 - extra, places=3)
        self.assertAlmostEqual(west[0], centre - .05 + extra, places=3)
        self.assertAlmostEqual(east[1], .40, places=2)
        self.assertEqual(module._to_atlas(rooms, .20, .40), (.20, .40))  # out of every reach
        # A point on a line stays in the middle of its new sea.
        for path in (module._X_CELESTIAL_SEA, module._X_INLAND_SEA):
            for x, v in path[1:-1]:
                there = module._to_map(rooms[:2], x, v)
                self.assertLess(abs(there[0] - x) + abs(there[1] - v), extra)
        # Trottingham Bridge, north of the Celestial Sea's line, is drawn where
        # the picture has it, to within a plot of XXL. (The Griffonstone
        # trestle moves east with the shore it stands on.)
        for x, v in module._X_BRIDGES[0][0]:
            there = module._to_map(rooms, x, v)
            self.assertLess(abs(there[0] - x) + abs(there[1] - v) / 1.5, 1 / 148.0, (x, v))
        # The map is the picture stretched, never folded: going east across the
        # map goes east across the picture, and going south goes south.
        for fixed in (.15, .31, .40, .52, .66, .80):
            previous_x = previous_v = None
            for step in range(1, 600):
                moving = step / 600.0
                spot = module._to_atlas(rooms, moving, fixed)
                if spot is not None:
                    if previous_x is not None:
                        self.assertGreater(spot[0], previous_x, (moving, fixed))
                    previous_x = spot[0]
                spot = module._to_atlas(rooms, fixed, moving)
                if spot is not None:
                    if previous_v is not None:
                        self.assertGreater(spot[1], previous_v, (fixed, moving))
                    previous_v = spot[1]
        # _to_map() undoes _to_atlas(), to within a fifth of an XXL plot.
        # Points within a hair of a line are spread across its new sea
        # instead, so those may differ by up to the width of that sea.
        checked = 0
        for row in range(60):
            for col in range(90):
                east, south = (col + .5) / 90, (row + .5) / 60
                spot = module._to_atlas(rooms, east, south)
                if spot is None:
                    continue
                back = module._to_map(rooms, spot[0], spot[1])
                error = abs(back[0] - east) + abs(back[1] - south) / 1.5
                pulls = [module._room_pull(room, spot[0], spot[1] / 1.5) for room in rooms]
                if any(pull is not None and pull[0] < .0045 for pull in pulls):
                    self.assertLess(error, 2.5 * extra)
                else:
                    self.assertLess(error, .0014, (east, south))
                    checked += 1
        self.assertGreater(checked, 4500)
        # Open water gained on a Huge map, in plots, where each sea was tight.
        cells = EXPANDED_SIZES[5]
        width, height = cells[0] * 4, cells[1] * 4
        def run(plots, x, y, dx, dy):
            self.assertEqual(plots[y * width + x], 0, (x, y))
            count = 1
            for sign in (1, -1):
                xx, yy = x + sign * dx, y + sign * dy
                while 0 <= xx < width and 0 <= yy < height and plots[yy * width + xx] == 0:
                    count += 1
                    xx, yy = xx + sign * dx, yy + sign * dy
            return count
        def open_water(plots):
            celestial = [run(plots, int(line_at(module._X_CELESTIAL_SEA, south) * width),
                             int((1 - south) * height), 1, 0)
                         for south in (.26, .33, .41, .45, .49, .53)]
            inland = [run(plots, int(east * width), int((1 - south) * height), 0, 1)
                      for east, south in ((.56, .311), (.60, .303), (.64, .301))]
            channel = [run(plots, int(line_at(module._X_INLAND_SEA[9:], south) * width),
                           int((1 - south) * height), 1, 0)
                       for south in (.43, .47, .51, .54)]
            rims = []
            for y in range(int(.25 * height), int(.75 * height)):
                row = plots[y * width:(y + 1) * width]
                rims.append(min(row.index(1) if 1 in row else width, 12) +
                            min(row[::-1].index(1) if 1 in row else width, 12))
            return [sum(part) / float(len(part)) for part in (celestial, inland, channel, rims)]
        def off(module):
            module._X_SEA_ROOM = tuple((0.0,) + row[1:] for row in module._X_SEA_ROOM)
        roomy = generate(INSTALLED, 5, (0, 1, EXPANDED))[0]
        drawn = generate(INSTALLED, 5, (0, 1, EXPANDED), tweak=off)[0]
        self.assertEqual(drawn, generate(INSTALLED, 5, (0, 1, EXPANDED),
                                         tweak=lambda module: setattr(module, "_X_SEA_ROOM", ()))[0])
        gains = [after - before for after, before in zip(open_water(roomy), open_water(drawn))]
        if "--sea-room" in sys.argv:
            print("open water as drawn / with sea room:", open_water(drawn), open_water(roomy))
        for gain in gains[:3]:
            self.assertTrue(2 * extra * 120 - 1.5 < gain < 2 * extra * 120 + 2.5, gains)
        self.assertTrue(2 < gains[3] < 4.5, gains)  # both rims together
        # At mid-height the land now stands at least two plots clear of each edge.
        for y in range(int(.25 * height), int(.75 * height)):
            self.assertEqual(roomy[y * width:y * width + 2], [0, 0])
            self.assertEqual(roomy[(y + 1) * width - 2:(y + 1) * width], [0, 0])

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

    def test_expanded_geography_in_every_climate(self):
        """No climate closes a pass or a sea lane: a Rocky world's thicker
        ranges and a Cold world's wider pack ice leave the same layout."""
        for climate in range(1, len(CLIMATES)):
            for size, variation, sea, seed in ((0, 1, 1, 5), (2, 2, 0, 11), (3, 1, 1, 99),
                                               (5, 1, 2, 7), (6, 0, 1, 3)):
                for bridges_are_land in (True, False):
                    with self.subTest(climate=CLIMATE_NAMES[climate], size=size, seed=seed,
                                      bridges_are_land=bridges_are_land):
                        self.assertEqual(geography_problems(
                            size, variation, sea, seed, bridges_are_land, climate), [])

    def test_climate_and_sea_level_are_offered(self):
        module = Environment().load(INSTALLED)
        self.assertIs(module.isClimateMap(), True)
        self.assertIs(module.isSeaLevelMap(), True)

    def test_known_world_answers_sea_level_and_climate(self):
        """The Known World too: a low sea bares more land and a high sea
        drowns some, at every size, and each climate repaints it."""
        land = lambda result: sum(1 for plot in result[0] if plot)
        for size in range(len(SIZES)):
            low, normal, high = [generate(INSTALLED, size, (0, 1, KNOWN), sea) for sea in range(3)]
            self.assertGreater(land(low), land(normal), size)
            self.assertGreater(land(normal), land(high), size)
        normal = generate(INSTALLED, 3, (0, 1, KNOWN))
        for climate in range(1, len(CLIMATES)):
            other = generate(INSTALLED, 3, (0, 1, KNOWN), climate=climate)
            self.assertNotEqual(normal[1], other[1], CLIMATE_NAMES[climate])
            self.assertEqual(other[5:], ("", ""))
            # ... and with either sea level, and the diagnostics on.
            for sea in (0, 2):
                logged = generate(INSTALLED, 3, (0, 1, KNOWN), sea, climate=climate,
                                  diagnostics=True)
                quiet = generate(INSTALLED, 3, (0, 1, KNOWN), sea, climate=climate)
                self.assertEqual(logged[:5], quiet[:5])
                self.assertIn("sea_level=%d climate=%d\n" % (sea, climate), logged[5])
                self.assertNotIn("ERROR", logged[5] + logged[6])

    def test_known_world_ocean_stays_whole_in_a_cold_age(self):
        """A Cold climate more than doubles the Known World's pack ice. Ships
        must still round the southern cape: with every ice plot treated as a
        wall, the open ocean is as much of one piece as under Temperate."""
        for size in (0, 3, 6):
            cells = SIZES[size]
            width, height = cells[0] * 4, cells[1] * 4
            share = []
            for climate in (TEMPERATE, COLD):
                plots, unused, features = generate(INSTALLED, size, (0, 1, KNOWN),
                                                   climate=climate, seed=size + 5)[:3]
                ice = set((i % width, i // width) for i, f in enumerate(features) if f == 30)
                unvisited = set((i % width, i // width)
                                for i, kind in enumerate(plots) if kind == 0) - ice
                open_water, largest = len(unvisited), 0
                while unvisited:
                    body = flood(plots, width, height, min(unvisited), (0,), ice, True)
                    unvisited -= body
                    largest = max(largest, len(body))
                share.append(largest / float(open_water))
            self.assertGreater(share[0], .9)
            self.assertGreater(share[1], share[0] - .02, size)

    def test_rocky_climate_closes_no_road(self):
        """Any two land plots that could be walked between before _uplift()
        raised its peaks can still be walked between afterwards, unless one
        of them became a peak itself. Checked on whole maps, both worlds."""
        module = Environment().load(INSTALLED)
        ring = lambda cells: module._way_through(
            [1 if (dx, dy) in cells else 3 for dy in (-1, 0, 1) for dx in (-1, 0, 1)], 3, 3, 1, 1)
        self.assertFalse(ring({(1, 0), (1, 1), (0, 1)}))          # one run
        self.assertTrue(ring({(1, 0), (-1, 0)}))                  # east and west only
        self.assertFalse(ring({(1, 0), (0, 1)}))                  # joined past the corner
        self.assertTrue(ring({(1, 1), (-1, 1)}))                  # two corners
        self.assertFalse(ring(set()))
        for atlas, size, variation, sea, seed in ((EXPANDED, 4, 2, 2, 202), (EXPANDED, 2, 1, 1, 9),
                                                  (KNOWN, 3, 1, 1, 4), (KNOWN, 5, 2, 0, 8)):
            cells = WORLD_SIZES[atlas][size]
            width, height = cells[0] * 4, cells[1] * 4
            options = (0, variation, atlas)
            before = generate(INSTALLED, size, options, sea, seed)[0]
            after = generate(INSTALLED, size, options, sea, seed, climate=ROCKY)[0]
            self.assertGreater(after.count(3), before.count(3))
            def regions(plots):
                label, found = {}, 0
                for index, kind in enumerate(plots):
                    spot = (index % width, index // width)
                    if kind in (1, 2) and spot not in label:
                        for member in flood(plots, width, height, spot, (1, 2)):
                            label[member] = found
                        found += 1
                return label
            old, new = regions(before), regions(after)
            joined = {}
            for spot, region in new.items():
                joined.setdefault(old[spot], set()).add(region)
            self.assertTrue(all(len(parts) == 1 for parts in joined.values()),
                            (atlas, size, seed))

    def test_climate_distances(self):
        """Each stock climate becomes the distances listed above _Climate, and
        only Temperate is calm. An index the game does not hold is Temperate."""
        expected = {  # snow, tundra, sand, jungle, ice, hills, peaks
            TEMPERATE: (0, 0, 0, 0, 0, 0, 0),
            TROPICAL: (-.05, -.05, -.01, .0375, -.005, 0, 0),
            ARID: (0, 0, .04, -.0142, -.005, 0, 0),
            ROCKY: (.0125, .025, -.005, -.00625, 0, 40, 30),
            COLD: (.05, .075, -.02, -.0229, .05, 0, 0)}
        for climate, row in expected.items():
            env = Environment(climate=climate)
            found = env.load(INSTALLED)._Climate()
            self.assertEqual(found.calm, climate == TEMPERATE)
            for name, value in zip(("snow", "tundra", "sand", "jungle", "ice", "hills", "peaks"), row):
                self.assertAlmostEqual(getattr(found, name), value, places=3,
                                       msg=(CLIMATE_NAMES[climate], name))
            self.assertEqual(env.rand.calls, [])
        gentle = Environment(climate=GENTLE).load(INSTALLED)._Climate()
        self.assertTrue(gentle.hills < 0 and gentle.peaks < 0 and not gentle.calm)
        self.assertTrue(Environment(climate=99).load(INSTALLED)._Climate().calm)
        module = Environment().load(INSTALLED)
        ovals = ((.5, .5, .04, .06), (.2, .2, .01, .02))
        self.assertIs(module._grown(ovals, 0.0, 1.5), ovals)
        self.assertEqual(module._grown(ovals, .03, 1.5), ((.5, .5, .06, .09), (.2, .2, .03, .05)))
        shrunk = module._grown(ovals, -.03, 1.5)
        self.assertAlmostEqual(shrunk[0][2], .02)
        self.assertAlmostEqual(shrunk[0][3], .03)
        self.assertEqual(shrunk[1][2:], (.005, .01))  # never below half its painted size

    def test_calm_climate_code_draws_the_painted_atlas(self):
        """The climate code with every distance at zero paints what the
        original code paints. The Known World normally bypasses it under
        Temperate; here it is forced through, and must still match the
        verified baseline."""
        def forced(module):
            land_bridge(module)
            calm = module._Climate
            class Forced(calm):
                def __init__(self):
                    calm.__init__(self)
                    self.calm = False
            module._Climate = Forced
        for size, variation, sea in ((0, 1, 1), (3, 2, 0), (5, 0, 2)):
            baseline = generate(BASELINE, size, (0, variation), sea)
            through = generate(INSTALLED, size, (0, variation, KNOWN), sea, tweak=forced)
            self.assertEqual(baseline[:5], through[:5])

    def test_climates_reshape_both_worlds(self):
        """Cold, Arid, Tropical and Rocky each change what they should, by a
        clear margin, and nothing else: coasts never move with the climate."""
        for atlas in (KNOWN, EXPANDED):
            options = (0, 1, atlas)
            worlds = [generate(INSTALLED, 4, options, climate=climate, seed=31)
                      for climate in range(len(CLIMATES))]
            def count(climate, kinds=None, terrain=None, feature=None):
                plots, terrains, features = worlds[climate][:3]
                total = 0
                for index, kind in enumerate(plots):
                    if kinds is not None and kind not in kinds:
                        continue
                    if terrain is not None and (kind == 0 or terrains[index] not in [
                            TERRAINS["TERRAIN_" + name] for name in terrain]):
                        continue
                    if feature is not None and features[index] != feature:
                        continue
                    total += 1
                return total
            frost = lambda climate: count(climate, terrain=("SNOW", "TUNDRA"))
            sand = lambda climate: count(climate, terrain=("DESERT",))
            jungle = lambda climate: count(climate, feature=31)
            forest = lambda climate: count(climate, feature=32)
            ice = lambda climate: count(climate, feature=30)
            with self.subTest(atlas=atlas):
                self.assertEqual(worlds[TEMPERATE][:5], generate(INSTALLED, 4, options, seed=31)[:5])
                for climate in range(len(CLIMATES)):
                    self.assertEqual([kind == 0 for kind in worlds[climate][0]],
                                     [kind == 0 for kind in worlds[TEMPERATE][0]])
                    if climate not in (ROCKY, GENTLE):
                        self.assertEqual(worlds[climate][0], worlds[TEMPERATE][0])
                self.assertGreater(frost(COLD), 1.3 * frost(TEMPERATE))
                self.assertGreater(ice(COLD), 1.5 * ice(TEMPERATE))
                self.assertLess(jungle(COLD), .8 * jungle(TEMPERATE))
                self.assertLess(sand(COLD), sand(TEMPERATE))
                self.assertLess(frost(TROPICAL), .85 * frost(TEMPERATE))
                self.assertGreater(jungle(TROPICAL), 1.3 * jungle(TEMPERATE))
                self.assertLess(sand(TROPICAL), sand(TEMPERATE))
                self.assertGreater(sand(ARID), 1.5 * sand(TEMPERATE))
                self.assertLess(jungle(ARID), .8 * jungle(TEMPERATE))
                self.assertLess(forest(ARID), .9 * forest(TEMPERATE))
                self.assertEqual(frost(ARID) > 0, True)
                self.assertGreater(count(ROCKY, kinds=(2,)), 1.15 * count(TEMPERATE, kinds=(2,)))
                self.assertGreater(count(ROCKY, kinds=(3,)), 1.15 * count(TEMPERATE, kinds=(3,)))
                self.assertLess(count(GENTLE, kinds=(3,)), .9 * count(TEMPERATE, kinds=(3,)))
                # A climate draws random numbers only to raise or wear down relief.
                extra = lambda climate: [call[1] for call in worlds[climate][3]
                                         if "uplift" in call[1]]
                self.assertEqual([bool(extra(climate)) for climate in range(len(CLIMATES))],
                                 [False, False, False, True, False, True])

    def test_crystal_empire_stays_green_in_a_cold_age(self):
        """The Crystal Heart's valley is grass under every climate, in both worlds."""
        for atlas, place, size in ((KNOWN, (.390, .133), 5), (EXPANDED, (.283, .143), 5)):
            cells = WORLD_SIZES[atlas][size]
            width, height = cells[0] * 4, cells[1] * 4
            for climate in range(len(CLIMATES)):
                plots, terrains = generate(INSTALLED, size, (0, 1, atlas), climate=climate)[:2]
                index = int((1 - place[1]) * height) * width + int(place[0] * width)
                self.assertIn(plots[index], (1, 2), (atlas, climate))
                self.assertEqual(terrains[index], TERRAINS["TERRAIN_GRASS"], (atlas, climate))

    def test_expanded_climate(self):
        """Each named region gets its biome on a Huge map."""
        module = Environment().load(INSTALLED)
        cells = EXPANDED_SIZES[5]
        width, height = cells[0] * 4, cells[1] * 4
        plots, terrains, features = generate(INSTALLED, 5, (0, 1, EXPANDED))[:3]
        def census(table, row):
            east, south, east_radius, south_radius = getattr(module, table)[row]
            found = []
            rooms = module._sea_rooms()
            for y in range(height):
                for x in range(width):
                    spot = module._to_atlas(rooms, (x + .5) / width, 1 - (y + .5) / height)
                    if plots[y * width + x] and spot is not None and module._in_oval(
                            spot[0], spot[1], east, south, east_radius * .7, south_radius * .7):
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
            module = env.load(INSTALLED)
            lanes = module._fixed_plots(width, height, module._sea_rooms())[0]
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
        self.assertEqual(len(lines), 3 * len(SIZES) + 2 * (len(CLIMATES) - 1) + 1)
        def causeway(module):
            module.KNOWN_BRIDGE_IS_LAND = True
        bridges = 0
        for unused, atlas, size, wrap, variation, sea, climate, bridge, value in lines:
            options = (int(wrap), int(variation), int(atlas))
            here = generate(INSTALLED, int(size), options, int(sea), climate=int(climate),
                            tweak=(None, causeway)[int(bridge)])
            self.assertEqual(map_digest(here), value, (atlas, size, climate, bridge))
            bridges += int(bridge)
        self.assertEqual(bridges, len(SIZES) + 1)  # the causeway at every size, and once under Rocky


if __name__ == "__main__":
    unittest.main(verbosity=2)
