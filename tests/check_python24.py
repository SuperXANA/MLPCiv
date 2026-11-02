#!/usr/bin/env python
"""Compile/import/generation smoke test for an actual CPython 2.4 interpreter.

Run: /path/to/python2.4 tests/check_python24.py
Civ extension objects, fractals, legality rules and feature utility are stubs.
This checks interpreter compatibility and observational instrumentation, not
the DLL, actual feature utility implementation, map selection or save loading.
"""
import os
import sys
import types
from StringIO import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = ((7, 8), (10, 10), (12, 13), (16, 17),
         (19, 20), (24, 26), (30, 31))
TERRAINS = ['GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW']


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
        if self.feature != -1 or self.isPeak(): return False
        if feature == 30: return self.isWater()
        return not self.isWater()
    def setFeatureType(self, feature, variety): self.feature = feature


class Fractal:
    def __init__(self, salt): self.salt = salt
    def getHeightFromPercent(self, percent): return int(255 * percent / 100)
    def getHeight(self, x, y): return (x * 131 + y * 73 + self.salt) % 256


class Environment:
    def __init__(self, size, options=(0, 1), sea=1):
        self.width, self.height = [value * 4 for value in SIZES[size]]
        self.options, self.sea = options, sea
        self.plots = [Plot() for unused in xrange(self.width * self.height)]
        self.state, self.calls = 1234, []
    def getGridWidth(self): return self.width
    def getGridHeight(self): return self.height
    def getCustomMapOption(self, index): return self.options[index]
    def getSeaLevel(self): return self.sea
    def plot(self, x, y): return self.plots[y * self.width + x]
    def getGame(self): return self
    def getMapRand(self): return self
    def getSeaLevelInfo(self, sea): return self
    def getSeaLevelChange(self): return (-10, 0, 10)[self.sea]
    def getInfoTypeForString(self, key):
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


def run(path, size, diagnostics):
    environment = Environment(size, (size % 3, size % 3), size % 3)
    module = environment.load(path, diagnostics)
    output, errors = StringIO(), StringIO()
    oldout, olderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output, errors
    try:
        assert module.getGridSize([size]) == SIZES[size]
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


def main():
    assert sys.version_info[:2] == (2, 4), 'Use CPython 2.4 for this check'
    baseline = os.path.join(ROOT, 'tests', 'fixtures', 'Equus_02add351.py')
    installed = os.path.join(ROOT, 'PrivateMaps', 'Equus.py')
    for size in xrange(len(SIZES)):
        expected, unused = run(baseline, size, False)
        disabled, quiet = run(installed, size, False)
        enabled, logs = run(installed, size, True)
        assert expected == disabled == enabled, 'Output or RNG trace changed'
        assert quiet == '', 'Disabled logger wrote output'
        for stage in ('getGridSize', 'generatePlotTypes', 'generateTerrainTypes', 'addFeatures'):
            assert stage + ' BEGIN' in logs and stage + ' END' in logs
        assert 'WARN' not in logs and 'ERROR' not in logs, logs
    print('CPython %s: 7 sizes, 21 baseline/off/on generation passes OK (Civ stubs).' % sys.version.split()[0])


if __name__ == '__main__':
    main()
