#!/usr/bin/env python
"""Compile/import/generation smoke test for an actual CPython 2.4 interpreter.

Run: /path/to/python2.4 tests/check_python24.py
Civ extension objects, fractals, legality rules and feature utility are stubs.
This checks interpreter compatibility and observational instrumentation, not
the DLL, actual feature utility implementation, map selection or save loading.

Both atlases are generated: the Known World under the Temperate climate is
compared with the pinned baseline, the Expanded world with itself (diagnostics
off and on), and then both worlds once under every other climate.
With --digests the script instead prints one checksum per generated map, for
tests/check_equus.py to compare with its own Python 3 run of the same script.
"""
import os
import sys
import types
from StringIO import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN, EXPANDED = 0, 1  # choices of the "Alternative Universe Expansions" option
WORLD_SIZES = (((7, 8), (10, 10), (12, 13), (16, 17), (19, 20), (24, 26), (30, 31)),
               ((9, 6), (12, 8), (16, 11), (20, 14), (24, 16), (30, 21), (37, 25)))
TERRAINS = ['GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW']
# As in tests/check_equus.py: the stock CIV4ClimateInfo.xml, and one test row.
CLIMATES = (
    ("CLIMATE_TEMPERATE", 0, 5, 5, 25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.95, 0.25),
    ("CLIMATE_TROPICAL", -10, 2, 5, 25, 0.1, 0.1, 0.0, 0.0, 0.0, 0.95, 0.20),
    ("CLIMATE_ARID", 20, 6, 5, 25, 0.0, 0.0, 0.0, -0.1, 0.1, 0.95, 0.20),
    ("CLIMATE_ROCKY", 0, 5, 7, 35, -0.025, -0.05, 0.0, 0.0, -0.05, 0.95, 0.25),
    ("CLIMATE_COLD", -10, 6, 5, 25, -0.1, -0.15, 0.0, 0.0, -0.1, 0.9, 0.5),
    ("CLIMATE_TEST_GENTLE", -5, 4, 3, 15, 0.05, 0.05, 0.0, 0.0, 0.0, 0.97, 0.20),
)


class ClimateInfo:
    def __init__(self, row): self.row = row
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


class PlotTypes:
    PLOT_OCEAN, PLOT_LAND, PLOT_HILLS, PLOT_PEAK = range(4)


class Plot:
    def __init__(self):
        self.kind, self.terrain, self.feature = 0, 20, -1
    def isWater(self): return self.kind == 0
    def isPeak(self): return self.kind == 3
    def isLake(self): return False
    def getTerrainType(self): return self.terrain
    def getFeatureType(self): return self.feature
    def canHaveFeature(self, feature):
        # As in tests/check_equus.py: AdvCiv 1.14's terrains for each feature.
        if self.feature != -1 or self.isPeak(): return False
        if feature == 30: return self.isWater()
        if self.isWater(): return False
        if feature == 31: return self.terrain in (10, 11)
        return self.terrain in (10, 11, 13)
    def setFeatureType(self, feature, variety): self.feature = feature


class Fractal:
    def __init__(self, salt): self.salt = salt
    def getHeightFromPercent(self, percent): return int(255 * percent / 100)
    def getHeight(self, x, y): return (x * 131 + y * 73 + self.salt) % 256


class Environment:
    def __init__(self, size, options=(0, 1, KNOWN), sea=1, climate=0):
        self.climate = climate
        atlas = KNOWN
        if len(options) > 2: atlas = options[2]
        self.width, self.height = [value * 4 for value in WORLD_SIZES[atlas][size]]
        self.options, self.sea = options, sea
        self.plots = [Plot() for unused in xrange(self.width * self.height)]
        self.state, self.calls = 1234, []
    def getGridWidth(self): return self.width
    def getGridHeight(self): return self.height
    def getCustomMapOption(self, index):
        if 0 <= index < len(self.options): return self.options[index]
        return -1  # CvInitCore: NO_CUSTOM_MAPOPTION for an index it does not hold
    def getSeaLevel(self): return self.sea
    def plot(self, x, y): return self.plots[y * self.width + x]
    def getGame(self): return self
    def getMapRand(self): return self
    def getSeaLevelInfo(self, sea): return self
    def getSeaLevelChange(self): return (-8, 0, 6)[self.sea]  # AdvCiv 1.14 XML
    def getClimate(self): return self.climate
    def getClimateInfo(self, index):
        if 0 <= index < len(CLIMATES): return ClimateInfo(CLIMATES[index])
        return None
    def getInfoTypeForString(self, key):
        if key.startswith('CLIMATE_'):
            names = [row[0] for row in CLIMATES]
            if key in names: return names.index(key)
            return -1
        return 10 + TERRAINS.index(key[len('TERRAIN_'):])
    def getText(self, label, args): return unicode(label)
    def get(self, upper, label):
        self.state = (1103515245 * self.state + 12345) & 0x7fffffff
        result = self.state % upper
        self.calls.append((upper, label, result))
        return result
    def load(self, path, diagnostics):
        environment = self
        extension = types.ModuleType('CvPythonExtensions')
        extension.CyGlobalContext = lambda: environment
        extension.CyTranslator = lambda: environment
        extension.CyMap = lambda: environment
        extension.PlotTypes = PlotTypes
        utility = types.ModuleType('CvMapGeneratorUtil')
        class FeatureGenerator:
            def __init__(self):
                self.iGridW, self.iGridH = environment.width, environment.height
                self.mapRand = environment
                self.featureIce, self.featureJungle, self.featureForest = 30, 31, 32
                self.forests = Fractal(environment.get(256, 'stub forest'))
                self.jungles = Fractal(environment.get(256, 'stub jungle'))
            def addFeatures(self):
                for y in xrange(self.iGridH):
                    for x in xrange(self.iGridW):
                        plot = environment.plot(x, y)
                        latitude = self.getLatitudeAtPlot(x, y)
                        self.addIceAtPlot(plot, x, y, latitude)
                        self.addJunglesAtPlot(plot, x, y, latitude)
                        self.addForestsAtPlot(plot, x, y, latitude)
        utility.FeatureGenerator = FeatureGenerator
        sys.modules['CvPythonExtensions'] = extension
        sys.modules['CvMapGeneratorUtil'] = utility
        module = types.ModuleType('equus_python24_check')
        # execfile performs real Python 2.4 parsing, compilation and execution.
        execfile(path, module.__dict__)
        module.EQUUS_DIAGNOSTICS = diagnostics
        return module


def run(path, size, diagnostics, atlas=None, climate=0, strait=True, bridge=False):
    # atlas None: a game stored before the third option existed (two options).
    # strait False: empty the Known World's Trottingham strait table, which
    # gives the land bridge of the pinned baseline.
    # bridge True: lay the Known World's causeway across the strait.
    options = (size % 3, size % 3)
    if atlas is not None: options = options + (atlas,)
    environment = Environment(size, options, size % 3, climate)
    module = environment.load(path, diagnostics)
    if not strait: module._TROTTINGHAM_STRAIT = ()
    if bridge: module.KNOWN_BRIDGE_IS_LAND = True
    sizes = WORLD_SIZES[atlas or KNOWN]
    output, errors = StringIO(), StringIO()
    oldout, olderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output, errors
    try:
        assert module.getGridSize([size]) == sizes[size]
        assert module.getGridSize([-1]) == []
        plots = module.generatePlotTypes()
        assert len(plots) == environment.width * environment.height
        for index, value in enumerate(plots): environment.plots[index].kind = value
        terrains = module.generateTerrainTypes()
        assert len(terrains) == len(plots)
        for index, value in enumerate(terrains): environment.plots[index].terrain = value
        assert module.addFeatures() == 0
    finally:
        sys.stdout, sys.stderr = oldout, olderr
    return (plots, terrains, [plot.feature for plot in environment.plots],
            environment.calls), output.getvalue() + errors.getvalue()


def digest(values):
    # FNV-1a over small integers; tests/check_equus.py computes the same.
    state = 2166136261
    for value in values:
        state = ((state ^ (value & 0xff)) * 16777619) & 0xffffffff
        state = ((state ^ ((value >> 8) & 0xff)) * 16777619) & 0xffffffff
    return state


def map_digest(result):
    plots, terrains, features, calls = result
    return '%08x' % digest(list(plots) + list(terrains) +
                           [feature + 1 for feature in features] +
                           [call[2] for call in calls])


def check_logs(logs):
    for stage in ('getGridSize', 'generatePlotTypes', 'generateTerrainTypes', 'addFeatures'):
        assert stage + ' BEGIN' in logs and stage + ' END' in logs
    assert 'WARN' not in logs and 'ERROR' not in logs, logs


def main():
    assert sys.version_info[:2] == (2, 4), 'Use CPython 2.4 for this check'
    baseline = os.path.join(ROOT, 'tests', 'fixtures', 'Equus_02add351.py')
    installed = os.path.join(ROOT, 'PrivateMaps', 'Equus.py')
    digests = '--digests' in sys.argv[1:]
    for size in xrange(len(WORLD_SIZES[KNOWN])):
        expected, unused = run(baseline, size, False)
        legacy, unused = run(installed, size, False, strait=False)
        bridged, unused = run(installed, size, False, KNOWN, strait=False)
        logged, unused = run(installed, size, True, KNOWN, strait=False)
        assert expected == legacy == bridged == logged, 'Output or RNG trace changed'
        # The default map: the same random draws, and plots that differ from the
        # baseline only by becoming ocean (the Trottingham strait).
        disabled, quiet = run(installed, size, False, KNOWN)
        enabled, logs = run(installed, size, True, KNOWN)
        assert disabled == enabled, 'Diagnostics changed the Known World'
        assert quiet == '', 'Disabled logger wrote output'
        check_logs(logs)
        assert disabled[3] == expected[3], 'The strait changed the RNG trace'
        opened = 0
        for index in xrange(len(expected[0])):
            if disabled[0][index] != expected[0][index]:
                opened += 1
                assert disabled[0][index] == PlotTypes.PLOT_OCEAN and disabled[2][index] == -1
            elif disabled[0][index] != PlotTypes.PLOT_OCEAN:
                # land that the strait left alone keeps its terrain and feature
                assert disabled[1][index] == expected[1][index], 'Terrain changed'
                assert disabled[2][index] == expected[2][index], 'Feature changed'
        assert opened > 3, 'No strait'
        # The causeway: the same draws again, and flat land across the strait.
        crossed, quiet = run(installed, size, False, KNOWN, bridge=True)
        logged, logs = run(installed, size, True, KNOWN, bridge=True)
        assert crossed == logged, 'Diagnostics changed the causeway'
        check_logs(logs)
        assert crossed[3] == expected[3], 'The causeway changed the RNG trace'
        laid = [index for index in xrange(len(expected[0]))
                if crossed[0][index] != disabled[0][index]]
        assert laid, 'No causeway'
        for index in laid:
            assert crossed[0][index] == PlotTypes.PLOT_LAND
        if digests:
            print('digest %d %d %d %d %d 0 0 %s' % (KNOWN, size, size % 3, size % 3, size % 3,
                                                   map_digest(disabled)))
            print('digest %d %d %d %d %d 0 1 %s' % (KNOWN, size, size % 3, size % 3, size % 3,
                                                   map_digest(crossed)))
    for size in xrange(len(WORLD_SIZES[EXPANDED])):
        disabled, quiet = run(installed, size, False, EXPANDED)
        enabled, logs = run(installed, size, True, EXPANDED)
        assert disabled == enabled, 'Diagnostics changed the Expanded world'
        assert quiet == '', 'Disabled logger wrote output'
        check_logs(logs)
        plots, terrains, features, calls = disabled
        land = len([plot for plot in plots if plot]) / float(len(plots))
        assert 0.45 < land < 0.72, land
        assert PlotTypes.PLOT_PEAK in plots and PlotTypes.PLOT_HILLS in plots
        assert 30 in features and 31 in features and 32 in features
        for upper, label, result in calls:
            assert 'expanded' in label or label.startswith('stub '), label
        if digests:
            print('digest %d %d %d %d %d 0 0 %s' % (EXPANDED, size, size % 3, size % 3, size % 3,
                                                   map_digest(disabled)))
    # Every other climate, once in each world, on a different size each time.
    for climate in xrange(1, len(CLIMATES)):
        for atlas in (KNOWN, EXPANDED):
            size = (climate + atlas) % len(WORLD_SIZES[atlas])
            temperate, unused = run(installed, size, False, atlas)
            disabled, quiet = run(installed, size, False, atlas, climate)
            enabled, logs = run(installed, size, True, atlas, climate)
            assert disabled == enabled, 'Diagnostics changed a climate'
            assert quiet == '', 'Disabled logger wrote output'
            check_logs(logs)
            assert disabled[1] != temperate[1], 'A climate left the terrain as it was'
            if digests:
                print('digest %d %d %d %d %d %d 0 %s' % (atlas, size, size % 3, size % 3,
                                                         size % 3, climate, map_digest(disabled)))
    # The causeway under the Rocky climate, whose relief pass must leave it flat.
    rocky, unused = run(installed, 2, False, KNOWN, 3, bridge=True)
    plain, unused = run(installed, 2, False, KNOWN, 3)
    assert rocky[0] != plain[0], 'No causeway under Rocky'
    if digests:
        print('digest %d 2 2 2 2 3 1 %s' % (KNOWN, map_digest(rocky)))
    if not digests:
        print('CPython %s: Known World 7 sizes x baseline, three with the strait table emptied, '
              'strait off/on, causeway off/on; Expanded 7 sizes x off/on; 5 other climates x '
              '2 worlds x temperate/off/on; the causeway under Rocky: 102 generation passes '
              'OK (Civ stubs).' % sys.version.split()[0])


if __name__ == '__main__':
    main()
