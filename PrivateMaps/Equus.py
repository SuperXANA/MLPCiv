## Sid Meier's Civilization 4
## Copyright Firaxis Games 2005
#
# Equus - a regional random map for MLP Civilization is Magic / AdvCiv 1.14.
# Install this file as <mod>/PrivateMaps/Equus.py. Python 2.4.
# Optional diagnostics: set EQUUS_DIAGNOSTICS below to True. See
# docs/Equus_Runtime_Verification.md for Civ's Python log settings and tests.
# The atlas uses x from west to east and v from north to south. Civ's y
# increases northward; plot and terrain arrays always use y * width + x.

from CvPythonExtensions import *
import CvMapGeneratorUtil


gc = CyGlobalContext()
localText = CyTranslator()

# XANA's named options, in the contiguous order expected by Custom Game.
WORLD_WRAP = 0
ATLAS_VARIATION = 1
CvMapOptions = (
    ("TXT_KEY_MAP_WORLD_WRAP", ("TXT_KEY_MAP_WRAP_FLAT",
     "TXT_KEY_MAP_WRAP_CYLINDER", "TXT_KEY_MAP_WRAP_TOROID"), 0),
    ("Atlas variation", ("Subtle", "Standard", "Lively"), 1),
)


# XANA 2026-11-02 BEGIN: optional Equus runtime diagnostics (North Light).
# Keep this out of CvMapOptions: existing option indices and defaults stay put.
EQUUS_DIAGNOSTICS = False


def _diagnostic_write(message, error=False):
    # Civ redirects stdout/stderr to its Python debug/error logging facilities.
    # Use those streams (as CvUtil does), without choosing a filesystem path.
    # A missing/disabled/broken logger must never prevent map generation.
    try:
        import sys
        stream = sys.stdout
        if error:
            stream = sys.stderr
        stream.write('[Equus] ' + message + '\n')
    except:
        pass


def _diagnostic_counts(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return ', '.join(['%s:%d' % (key, counts[key])
                      for key in sorted(counts.keys())])


def _diagnostic_begin(stage):
    _diagnostic_write(stage + ' BEGIN')
    if stage == 'getGridSize':
        return  # The map is not necessarily allocated yet.
    m = CyMap()
    width, height = m.getGridWidth(), m.getGridHeight()
    _diagnostic_write('grid=%dx%d plots=%d sea_level=%d' %
                      (width, height, width * height, m.getSeaLevel()))
    for index in range(len(CvMapOptions)):
        choice = _option(index)
        _diagnostic_write('option[%d] raw=%d effective=%d label=%s' %
                          (index, m.getCustomMapOption(index), choice,
                           CvMapOptions[index][1][choice]))
    if width <= 0 or height <= 0:
        _diagnostic_write('ERROR non-positive grid dimensions', True)


def _diagnostic_end(stage, result, args, kwargs):
    if stage == 'getGridSize':
        if args:
            args_list = args[0]
        else:
            args_list = kwargs['argsList']
        if args_list[0] == -1:
            _diagnostic_write('getGridSize load sentinel; keep saved dimensions')
        else:
            _diagnostic_write('world=%d cells=%s expected_plots=%dx%d' %
                              (args_list[0], result, result[0] * 4, result[1] * 4))
    else:
        m = CyMap()
        width, height = m.getGridWidth(), m.getGridHeight()
        if stage in ('generatePlotTypes', 'generateTerrainTypes'):
            _diagnostic_write('%s array=%d expected=%d' %
                              (stage, len(result), width * height))
            if len(result) != width * height:
                _diagnostic_write('ERROR unexpected output-array size', True)
            if stage == 'generatePlotTypes':
                for label, value in (('ocean', PlotTypes.PLOT_OCEAN),
                                     ('land', PlotTypes.PLOT_LAND),
                                     ('hills', PlotTypes.PLOT_HILLS),
                                     ('peak', PlotTypes.PLOT_PEAK)):
                    _diagnostic_write('plot %s=%d' % (label, result.count(value)))
            else:
                _diagnostic_write('terrain_ids={' + _diagnostic_counts(result) + '}')
                for key in ('GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW'):
                    value = gc.getInfoTypeForString('TERRAIN_' + key)
                    _diagnostic_write('terrain %s id=%d count=%d' %
                                      (key, value, result.count(value)))
                    if value < 0:
                        _diagnostic_write('ERROR missing TERRAIN_' + key, True)
        elif stage == 'addFeatures':
            features = []
            for y in range(height):
                for x in range(width):
                    features.append(m.plot(x, y).getFeatureType())
            _diagnostic_write('feature_ids={' + _diagnostic_counts(features) + '}')
    _diagnostic_write(stage + ' END')


def _diagnostic_error(stage):
    _diagnostic_write(stage + ' ERROR (traceback follows)', True)
    try:
        import sys
        import traceback
        traceback.print_exc(file=sys.stderr)
    except:
        pass


def _diagnostic_stage(callback):
    def run(*args, **kwargs):
        if not EQUUS_DIAGNOSTICS:
            return callback(*args, **kwargs)
        try:
            _diagnostic_begin(callback.__name__)
        except:
            _diagnostic_write(callback.__name__ + ' WARN context unavailable')
        try:
            result = callback(*args, **kwargs)
        except:
            _diagnostic_error(callback.__name__)
            raise  # Retain the game's ordinary failure handling; never fake success.
        try:
            _diagnostic_end(callback.__name__, result, args, kwargs)
        except:
            _diagnostic_write(callback.__name__ + ' WARN summary unavailable')
        return result
    run.__name__ = callback.__name__
    run.__doc__ = callback.__doc__
    return run
# XANA 2026-11-02 END: optional Equus runtime diagnostics (North Light).


def getDescription():
    return u"Equus: a regional map with familiar seas, ranges and climate belts."


def isAdvancedMap():
    return False


def isClimateMap():
    return False  # Climate is regional: the Crystal basin lies north of Ponyville.


def isSeaLevelMap():
    return True


def getTopLatitude():
    return 85


def getBottomLatitude():
    return -85


@_diagnostic_stage
def getGridSize(argsList):
    # AdvCiv multiplies a script's cell dimensions by four on both axes.
    # Keep roughly the 1.14 XML plot budget, in the portrait atlas proportions.
    world = argsList[0]
    if world == -1:
        return []  # Loading a save; use its stored dimensions.
    sizes = ((7, 8), (10, 10), (12, 13), (16, 17),
             (19, 20), (24, 26), (30, 31))  # Duel through XXL
    return sizes[min(world, len(sizes) - 1)]


def getNumCustomMapOptions():
    return len(CvMapOptions)


def _option_text(label):
    if label.startswith("TXT_KEY_"):
        return localText.getText(label, ())
    return unicode(label)


def getCustomMapOptionName(argsList):
    return _option_text(CvMapOptions[argsList[0]][0])


def getNumCustomMapOptionValues(argsList):
    return len(CvMapOptions[argsList[0]][1])


def getCustomMapOptionDescAt(argsList):
    option, choice = argsList
    return _option_text(CvMapOptions[option][1][choice])


def getCustomMapOptionDefault(argsList):
    return CvMapOptions[argsList[0]][2]


def isRandomCustomMapOption(argsList):
    return False


def _option(index):
    choice = CyMap().getCustomMapOption(index)
    if 0 <= choice < len(CvMapOptions[index][1]):
        return choice
    return CvMapOptions[index][2]


def getWrapX():
    return _option(WORLD_WRAP) != 0


def getWrapY():
    return _option(WORLD_WRAP) == 2


def _variation():
    return (0.5, 1.0, 1.5)[_option(ATLAS_VARIATION)]


def _noise_grid(columns, rows, label):
    # Sample the game's seeded map RNG once per lattice node, in fixed order.
    # No seed resets, wall-clock input, or map state retained between games.
    dice = gc.getGame().getMapRand()
    return [[(dice.get(2049, label) - 1024) / 1024.0
             for col in xrange(columns)] for row in xrange(rows)]


def _noise(grid, x, v):
    # Interpolate neighboring samples so a bay or forest edge moves together.
    last_x, last_v = len(grid[0]) - 1, len(grid) - 1
    fx = max(0.0, min(1.0, x)) * last_x
    fv = max(0.0, min(1.0, v)) * last_v
    col, row = min(int(fx), last_x - 1), min(int(fv), last_v - 1)
    dx, dv = fx - col, fv - row
    north = grid[row][col] * (1.0 - dx) + grid[row][col + 1] * dx
    south = grid[row + 1][col] * (1.0 - dx) + grid[row + 1][col + 1] * dx
    return north * (1.0 - dv) + south * dv


# Atlas coordinates are fractions of the reference picture: x increases east,
# v increases SOUTH. Each coastline station is (v, west shore, east shore).
# Negative and >1 coordinates carry a landmass past the edge of the frame.
_EQUESTRIA = (
    (-.10, -.10, 1.10), (.10, -.10, .91), (.143, -.10, .90),
    (.154, .091, .882), (.171, .124, .868), (.189, .102, .858),
    (.208, .083, .809), (.222, .075, .753), (.240, .098, .727),
    (.256, .084, .690), (.285, .073, .704), (.302, .058, .653),
    (.316, -.10, .658), (.343, -.10, .672), (.368, -.10, .658),
    (.391, -.10, .700), (.402, -.10, .684), (.410, -.10, .650),
    (.422, -.10, .661), (.430, .086, .699), (.443, .143, .700),
    (.463, .148, .695), (.481, .139, .699), (.504, .104, .713),
    (.530, .099, .742), (.549, .116, .744), (.558, .205, .735),
    (.588, .214, .711), (.614, .221, .699), (.638, .206, .678),
    (.654, .189, .648), (.686, .185, .651), (.707, .191, .677),
    (.737, .188, .678), (.749, .201, .711), (.765, .284, .686),
    (.786, .309, .669), (.802, .364, .657), (.826, .381, .641),
    (.840, .429, .642), (.850, .540, .642), (.867, .615, .647),
    (.880, .648, .655))
_GRIFFONSTONE = (
    (-.10, .62, 1.10), (.130, .645, 1.10), (.175, .737, 1.10),
    (.203, .840, 1.10), (.223, .858, 1.10), (.246, .841, 1.10),
    (.267, .876, 1.10), (.290, .846, 1.10), (.324, .828, 1.10),
    (.365, .820, 1.10), (.397, .841, 1.10), (.430, .877, 1.10),
    (.442, .960, 1.10), (.464, 1.024, 1.10))
_DRAGON_COAST = (
    (.479, .905, .969), (.496, .874, 1.10), (.524, .853, 1.10),
    (.552, .826, 1.10), (.578, .837, 1.10), (.613, .852, 1.10),
    (.660, .858, 1.10), (.691, .840, 1.10), (.721, .834, 1.10),
    (.737, .852, 1.10), (.760, .912, 1.10), (.780, .964, 1.10),
    (.795, 1.030, 1.10))
_STORM_REALM = (
    (.852, .206, .225), (.869, .187, .253), (.883, .168, .274),
    (.899, .175, .314), (.920, .204, .336), (.939, .242, .367),
    (.946, .259, .275))
_SHORES = (_EQUESTRIA, _GRIFFONSTONE, _DRAGON_COAST, _STORM_REALM)

# Center and radii for offshore islands, from north to south.
_ISLES = ((.104, .174, .010, .012), (.076, .194, .009, .011),
          (.810, .225, .014, .020),  # Griffish Isles
          (.706, .707, .011, .007),  # Black Skull Island
          (.722, .888, .018, .021))  # Mount Aris

# Each range has a half-width, a crest strength, and a path of (x, v) points.
# Keep Unicorn and Foal ranges separate so the Ponyville valley stays open.
_RANGES = (
    (.055, 1.00, ((.00,.105), (.14,.065), (.25,.117), (.41,.048),
                  (.53,.106), (.66,.089), (.76,.108), (.92,.055), (1.,.106))),
    (.032, .96, ((.285,.159), (.375,.142), (.480,.154), (.589,.187),
                 (.678,.197), (.738,.174))),       # Crystal Mountains
    (.022, .85, ((.137,.213), (.169,.248), (.219,.284))),  # Unicorn Range
    (.028, .83, ((.105,.299), (.168,.289), (.267,.304))),  # Smokey Mountains
    (.015, 1.00, ((.408,.259), (.415,.310))),               # Canterlot
    (.019, .83, ((.452,.302), (.504,.282), (.594,.310))),  # Foal Mountain
    (.019, .68, ((.425,.373), (.479,.352), (.500,.362))),  # Rambling Rock
    (.041, .80, ((.305,.502), (.401,.468), (.499,.454), (.575,.464),
                 (.627,.505), (.635,.552))),       # Macintosh Hills / Badlands
    (.034, .90, ((.278,.580), (.318,.547), (.371,.590))),  # Arimaspi
    (.038, .91, ((.936,.172), (.946,.252), (.904,.325), (.973,.402))),
    (.034, .92, ((.874,.551), (.933,.503), (.991,.537))),  # Dragons' Lair
    (.022, .88, ((.203,.881), (.232,.908), (.312,.925))),
    (.017, .96, ((.718,.887), (.728,.889))))               # Mount Aris

# Three breaks across the Crystal Mountains, for travel between central
# Equestria and the northern highlands. Values are center x, v, and radii.
_PASSES = ((.305,.160,.022,.039), (.494,.157,.019,.046),
           (.647,.194,.022,.045))


def _inside_shore(shore, x, v, inset):
    if v < shore[0][0] + inset or v > shore[-1][0] - inset:
        return False
    v = max(shore[0][0], min(shore[-1][0], v))
    for i in range(1, len(shore)):
        lower, left, right = shore[i]
        if v <= lower:
            upper, old_left, old_right = shore[i - 1]
            t = (v - upper) / (lower - upper)
            return (old_left + (left - old_left) * t + inset <= x and
                    x <= old_right + (right - old_right) * t - inset)
    return False


def _in_oval(x, v, cx, cv, rx, rv):
    dx, dv = (x - cx) / rx, (v - cv) / rv
    return dx * dx + dv * dv <= 1.0


def _ridge_segments():
    segments = []
    for radius, strength, path in _RANGES:
        for i in range(1, len(path)):
            ax, av = path[i - 1]
            bx, bv = path[i]
            dx, dv = bx - ax, bv - av
            bounds = (min(ax, bx) - radius, max(ax, bx) + radius,
                      min(av, bv) - radius, max(av, bv) + radius)
            segments.append((bounds, ax, av, dx, dv, dx * dx + dv * dv,
                             radius * radius, strength))
    return segments


def _crest(segments, x, v):
    best = 0.0
    for bounds, ax, av, dx, dv, length2, radius2, strength in segments:
        if x < bounds[0] or x > bounds[1] or v < bounds[2] or v > bounds[3]:
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (v - av) * dv) / length2))
        ex, ev = x - ax - t * dx, v - av - t * dv
        best = max(best, strength * (1.0 - (ex * ex + ev * ev) / radius2))
    return best


def _plot_types(width, height, variation, sea_shift):
    warp_x = _noise_grid(18, 19, "Equus coast east-west")
    warp_v = _noise_grid(19, 18, "Equus coast north-south")
    uplands = _noise_grid(27, 29, "Equus rolling uplands")
    dice = gc.getGame().getMapRand()
    segments = _ridge_segments()
    island_cores = set()
    for cx, cv, rx, rv in _ISLES:
        island_cores.add((int(cx * width), int((1.0 - cv) * height)))
    # The narrowest stretches of open water on the atlas can round away
    # on a small grid. Reserve one water row/column at each crossing.
    dragon_strait_y = int((1.0 - .467) * height)
    aris_channel_x = int(.682 * width)
    plots = []
    for y in range(height):
        south = 1.0 - (y + 0.5) / height
        for x in range(width):
            east = (x + 0.5) / width
            if ((y == dragon_strait_y and east > .775) or
                    (x == aris_channel_x and south > .821)):
                plots.append(PlotTypes.PLOT_OCEAN)
                continue
            atlas_x = east + .018 * variation * _noise(warp_x, east, south)
            atlas_v = south + .016 * variation * _noise(warp_v, east, south)
            land = (x, y) in island_cores
            for shore in _SHORES:
                if _inside_shore(shore, atlas_x, atlas_v, sea_shift):
                    land = True
                    break
            if not land:
                # Guarantee the small islands can resolve on a Duel grid.
                # They move less than the mainland and keep a one-tile core.
                for cx, cv, rx, rv in _ISLES:
                    rx = max(rx - sea_shift * .30, .75 / width)
                    rv = max(rv - sea_shift * .30, .75 / height)
                    if _in_oval((east + atlas_x) * .5, (south + atlas_v) * .5, cx, cv, rx, rv):
                        land = True
                        break
            if not land or _in_oval(atlas_x, atlas_v, .414, .333, .017, .010):
                plots.append(PlotTypes.PLOT_OCEAN)  # includes Saddle Lake
                continue
            if _in_oval(east, south, .390, .132, .054, .020):
                plots.append(PlotTypes.PLOT_LAND)  # Crystal Empire's inner basin
                continue
            crest = _crest(segments, atlas_x, atlas_v)
            for cx, cv, rx, rv in _PASSES:
                if _in_oval(atlas_x, atlas_v, cx, cv, rx, rv):
                    crest = min(crest, .38)
                    break
            local = _noise(uplands, east, south)
            relief = crest + .22 * local + (.10 + .08 * variation) * (
                dice.get(201, "Equus relief") / 100.0 - 1.0)
            if relief > .84:
                plots.append(PlotTypes.PLOT_PEAK)
            elif relief > .22:
                plots.append(PlotTypes.PLOT_HILLS)
            else:
                plots.append(PlotTypes.PLOT_LAND)
    return plots


@_diagnostic_stage
def generatePlotTypes():
    world = CyMap()
    change = gc.getSeaLevelInfo(world.getSeaLevel()).getSeaLevelChange()
    sea_shift = max(-0.008, min(0.008, change * 0.001))
    return _plot_types(world.getGridWidth(), world.getGridHeight(),
                       _variation(), sea_shift)


# Biome ovals are (center east, center south, east radius, south radius).
# Coordinates are fractions of the illustrated map, measured from its upper left.
_CRYSTAL_BASIN = ((0.390, 0.133, 0.070, 0.023),)
_DRY_BASINS = (
    (0.211, 0.489, 0.104, 0.053),  # San Palomino Desert
    (0.505, 0.505, 0.098, 0.046),  # Badlands
    (0.446, 0.686, 0.277, 0.072),  # Bone Dry Desert and Klugetown
)
_GRASSY_LOWLANDS = (
    (0.359, 0.305, 0.116, 0.052),  # Ponyville and central valley
    (0.390, 0.395, 0.050, 0.030),  # Froggy Bottom Bog and river meadows
)
_WET_WOODS = (
    (0.582, 0.580, 0.113, 0.046),  # Forbidden Jungle
    (0.686, 0.471, 0.052, 0.091),  # Hayseed Swamps
    (0.940, 0.687, 0.103, 0.098),  # Kirin Grove
)
_WOODLANDS = (
    (0.360, 0.370, 0.077, 0.034),  # Everfree Forest
    (0.188, 0.366, 0.115, 0.041),  # White Tail Woods and the western slopes
    (0.578, 0.271, 0.057, 0.024),  # Hollow Shades
    (0.902, 0.347, 0.077, 0.082),  # Griffonstone
    (0.336, 0.586, 0.094, 0.037),  # Farthest Reaches
)


def _in_biome(east, south, ovals):
    for cx, cy, rx, ry in ovals:
        if _in_oval(east, south, cx, cy, rx, ry):
            return True
    return False


def _land_terrain(east, south, patch, peak):
    if _in_biome(east, south, _CRYSTAL_BASIN) and not peak:
        return 'GRASS'
    if south < 0.077 or (peak and south < 0.175):
        return 'SNOW'
    if south < 0.150:
        return 'TUNDRA'
    if _in_biome(east, south, _DRY_BASINS):
        if patch < -0.57:
            return 'PLAINS'
        return 'DESERT'
    if _in_biome(east, south, _WET_WOODS) or _in_biome(east, south, _GRASSY_LOWLANDS):
        return 'GRASS'
    # The mainland cools again beyond the Bone Dry Desert, at Basalt Beach.
    if south > 0.765 and east < 0.690:
        if patch < -0.18:
            return 'TUNDRA'
        return 'PLAINS'
    if 0.399 < south < 0.469 and 0.276 < east < 0.522 and patch < 0.55:
        return 'PLAINS'  # Appleloosa, between the desert and the central grasslands
    if patch < -0.15:
        return 'PLAINS'
    return 'GRASS'


@_diagnostic_stage
def generateTerrainTypes():
    m = CyMap()
    width, height = m.getGridWidth(), m.getGridHeight()
    terrain = {}
    for key in ('GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW'):
        terrain[key] = gc.getInfoTypeForString('TERRAIN_' + key)
    drift_x = _noise_grid(12, 12, 'Equus biome east drift')
    drift_y = _noise_grid(12, 12, 'Equus biome south drift')
    patches = _noise_grid(25, 25, 'Equus ground cover')
    amplitude = 0.018 * _variation()
    result = []
    for y in range(height):
        south = 1.0 - (y + 0.5) / height
        for x in range(width):
            plot = m.plot(x, y)
            if plot.isWater():
                result.append(plot.getTerrainType())  # Keep shallow/deep water from the DLL.
                continue
            east = (x + 0.5) / width
            u = east + amplitude * _noise(drift_x, east, south)
            v = south + amplitude * _noise(drift_y, east, south)
            key = _land_terrain(u, v, _noise(patches, east, south), plot.isPeak())
            result.append(terrain[key])
    return result


class EquusFeatureGenerator(CvMapGeneratorUtil.FeatureGenerator):
    # Keep the utility's shuffled XML appearance pass (e.g. flood plains and
    # oases). Its stock forest/jungle fractals supply texture inside our regions.
    def __init__(self):
        CvMapGeneratorUtil.FeatureGenerator.__init__(self)
        self.denseForest = self.forests.getHeightFromPercent(24)
        self.openForest = self.forests.getHeightFromPercent(83)
        self.wetJungle = self.jungles.getHeightFromPercent(41)

    def getLatitudeAtPlot(self, x, y):
        # The three regional methods below all use distance from the atlas top.
        return 1.0 - (y + 0.5) / self.iGridH

    def addIceAtPlot(self, plot, x, y, south):
        if south < 0.9 or not plot.isWater() or plot.isLake():
            return
        east = (x + 0.5) / self.iGridW
        # The Great Iceberg Barrier reaches farther north in the outer corners.
        shelf = 0.995 - 0.060 * abs(2.0 * east - 1.0)
        chance = int(55 + 1750 * (south - shelf))
        if chance > 0 and plot.canHaveFeature(self.featureIce):
            if self.mapRand.get(100, 'Equus southern pack ice') < chance:
                plot.setFeatureType(self.featureIce, -1)

    def addJunglesAtPlot(self, plot, x, y, south):
        east = (x + 0.5) / self.iGridW
        if _in_biome(east, south, _WET_WOODS):
            if self.jungles.getHeight(x, y) >= self.wetJungle and plot.canHaveFeature(self.featureJungle):
                plot.setFeatureType(self.featureJungle, -1)

    def addForestsAtPlot(self, plot, x, y, south):
        if not plot.canHaveFeature(self.featureForest):
            return
        east = (x + 0.5) / self.iGridW
        threshold = self.openForest
        if _in_biome(east, south, _WOODLANDS) or _in_biome(east, south, _WET_WOODS):
            threshold = self.denseForest
        if self.forests.getHeight(x, y) >= threshold:
            plot.setFeatureType(self.featureForest, -1)


@_diagnostic_stage
def addFeatures():
    EquusFeatureGenerator().addFeatures()
    return 0
