## Sid Meier's Civilization 4
## Copyright Firaxis Games 2005
#
# Equus - a regional random map for MLP Civilization is Magic / AdvCiv 1.14.
# Install this file as <mod>/PrivateMaps/Equus.py. Python 2.4.
# One script, two atlases, chosen with the "Alternative Universe Expansions"
# map option: Equestria "Known World" (the default) and Equestria "Expanded".
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
ATLAS_WORLD = 2
CvMapOptions = (
    ("TXT_KEY_MAP_WORLD_WRAP", ("TXT_KEY_MAP_WRAP_FLAT",
     "TXT_KEY_MAP_WRAP_CYLINDER", "TXT_KEY_MAP_WRAP_TOROID"), 0),
    ("Atlas variation", ("Subtle", "Standard", "Lively"), 1),
    ("Alternative Universe Expansions", ('Equestria "Known World"',
     'Equestria "Expanded"'), 0),
)
# XANA 2026-11-22: choices of ATLAS_WORLD. A further world is one more label
# above, one more row in _GRID_SIZES, and one more branch in the three
# generation callbacks.
KNOWN_WORLD = 0
EXPANDED_WORLD = 1


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
    _diagnostic_write('grid=%dx%d plots=%d sea_level=%d climate=%d' %
                      (width, height, width * height, m.getSeaLevel(), m.getClimate()))
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
    return (u"Equus: a regional map with familiar seas, ranges and climate belts. "
            u"Play Equestria's Known World, or the Expanded world beyond it.")


def isAdvancedMap():
    return False


def isClimateMap():
    # XANA 2026-11-28: the atlases now answer the Climate option. The regions
    # stay where the picture paints them (the Crystal basin still lies north
    # of Ponyville); a climate moves their edges. See _Climate below.
    return True


def isSeaLevelMap():
    return True


def getTopLatitude():
    return 85


def getBottomLatitude():
    return -85


# Cells for Duel through XXL, one row per choice of ATLAS_WORLD. The Known
# World picture is portrait. The Expanded picture is landscape, and its Huge
# row is exactly the mod's own Huge map: 30 x 21 cells = 120 x 84 plots.
_GRID_SIZES = (
    ((7, 8), (10, 10), (12, 13), (16, 17), (19, 20), (24, 26), (30, 31)),
    ((9, 6), (12, 8), (16, 11), (20, 14), (24, 16), (30, 21), (37, 25)),
)


@_diagnostic_stage
def getGridSize(argsList):
    # AdvCiv multiplies a script's cell dimensions by four on both axes.
    # Keep roughly the 1.14 XML plot budget, in each atlas's own proportions.
    world = argsList[0]
    if world == -1:
        return []  # Loading a save; use its stored dimensions.
    sizes = _GRID_SIZES[_option(ATLAS_WORLD)]
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
    if _expanded():
        return _expanded_plot_types(world.getGridWidth(), world.getGridHeight(),
                                    _variation(), sea_shift)
    plots = _plot_types(world.getGridWidth(), world.getGridHeight(),
                        _variation(), sea_shift)
    climate = _Climate()
    if climate.hills or climate.peaks:
        _uplift(plots, world.getGridWidth(), world.getGridHeight(), climate,
                _known_level_ground(world.getGridWidth(), world.getGridHeight()),
                "Equus rocky uplift")
    return plots


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
    if _expanded():
        return _expanded_terrain_types()
    m = CyMap()
    width, height = m.getGridWidth(), m.getGridHeight()
    terrain = {}
    for key in ('GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW'):
        terrain[key] = gc.getInfoTypeForString('TERRAIN_' + key)
    drift_x = _noise_grid(12, 12, 'Equus biome east drift')
    drift_y = _noise_grid(12, 12, 'Equus biome south drift')
    patches = _noise_grid(25, 25, 'Equus ground cover')
    amplitude = 0.018 * _variation()
    climate = _Climate()
    biomes = _Biomes(climate, _KNOWN_ASPECT, (), (), _DRY_BASINS, _WET_WOODS)
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
            if climate.calm:
                key = _land_terrain(u, v, _noise(patches, east, south), plot.isPeak())
            else:
                key = _known_climate_terrain(u, v, _noise(patches, east, south),
                                             plot.isPeak(), climate, biomes)
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
    if _expanded():
        ExpandedFeatureGenerator().addFeatures()
    elif _Climate().calm:
        EquusFeatureGenerator().addFeatures()
    else:
        KnownClimateFeatureGenerator().addFeatures()
    return 0


# XANA 2026-11-28 BEGIN: the Climate option, for both atlases.
# A stock map slides whole latitude belts when the climate changes. An atlas
# has no belts to slide: its deserts, jungles and snowfields are painted where
# the picture has them. So a climate here moves the EDGE of each painted
# region instead. The Bone Dry Desert stays where it is, and under an arid sun
# it swells; in a cold age every frost line creeps outward and the jungles
# draw in. Each distance below is worked out from the numbers in the game's
# own CIV4ClimateInfo.xml, measured against its CLIMATE_TEMPERATE entry, so
#   * Temperate is exactly the atlas as painted (all distances are zero), and
#   * a climate added to that XML later is understood without editing this
#     script: give it colder latitudes, more desert, and so on, as usual.
# Distances ("reaches") are fractions of the map's HEIGHT. The stock generator
# measures latitude from equator to pole, which is half the map, so a latitude
# change in the XML moves a line by half that much of the map's height.
_STOCK_TEMPERATE = (0, 5, 5, 25, 0.0, 0.0, 0.0, 0.0, 0.95, 0.25)
_KNOWN_ASPECT = .92  # the Known World grid is a little taller than it is wide


def _between(low, value, high):
    return max(low, min(high, value))


def _climate_numbers(info):
    return (info.getDesertPercentChange(), info.getJungleLatitude(),
            info.getHillRange(), info.getPeakPercent(),
            info.getSnowLatitudeChange(), info.getTundraLatitudeChange(),
            info.getDesertBottomLatitudeChange(), info.getDesertTopLatitudeChange(),
            info.getIceLatitude(), info.getRandIceLatitude())


class _Climate:
    # The chosen climate as a handful of distances. With stock XML:
    #              snow    tundra   sand    jungle   ice    hills  peaks
    #   Temperate   0       0        0       0        0      0      0
    #   Tropical   -.050   -.050    -.010   +.0375   -.005   0      0
    #   Arid        0       0       +.040   -.014    -.005   0      0
    #   Rocky      +.0125  +.025    -.005   -.006     0     +40    +30
    #   Cold       +.050   +.075    -.020   -.023    +.050   0      0
    def __init__(self):
        chosen = base = _STOCK_TEMPERATE
        info = gc.getClimateInfo(CyMap().getClimate())
        if info is not None:
            chosen = _climate_numbers(info)
        info = gc.getClimateInfo(gc.getInfoTypeForString("CLIMATE_TEMPERATE"))
        if info is not None:
            base = _climate_numbers(info)
        (desert, jungle, hills, peaks, snow, tundra,
         desert_bottom, desert_top, ice, floes) = [
            now - usual for now, usual in zip(chosen, base)]
        # True for Temperate: every caller then takes the path it took before
        # climates existed, which keeps the Known World exactly as verified.
        self.calm = chosen == base
        # Frost lines advance when the XML lowers the snow and tundra latitudes.
        self.snow = _between(-.10, -snow / 2.0, .10)
        self.tundra = _between(-.10, -tundra / 2.0, .12)
        # Desert: a tenth of a percent of height for each percent of desert,
        # plus the widening of the stock desert belt.
        self.sand = _between(-.05, desert / 1000.0 + (desert_top - desert_bottom) / 10.0, .08)
        # The stock jungle belt ends at latitude 1 / iJungleLatitude. Frost
        # and sand each drive the jungle back by a quarter of their own advance.
        belt = 1.0 / max(1, chosen[1]) - 1.0 / max(1, base[1])
        self.jungle = _between(-.06, belt / 8.0 - max(0.0, self.tundra) / 4.0 -
                               max(0.0, self.sand) / 4.0, .06)
        self.ice = _between(-.05, -ice / 2.0 + floes / 10.0, .08)
        # Percent chances for _uplift(): negative values wear the land down.
        self.hills = _between(-60, 20 * hills, 60)
        self.peaks = _between(-60, 3 * peaks, 60)
        # Open ground is plains where the ground-cover noise falls below this.
        self.plains = -0.15 + 2.0 * self.sand
        # Trees thin out in dry climates: percentage points of forest cover.
        self.thin = int(_between(-8, 150 * self.sand, 12))


def _grown(ovals, reach, aspect):
    # Move the rim of every oval outward by `reach` (inward if negative).
    # `aspect` is the map's width over its height, so that the rim moves as
    # many plots east-west as north-south. A named place never shrinks below
    # half its painted size: a warm age thins Antleria's ice, it does not
    # erase the Ice Kingdom.
    if reach == 0.0:
        return ovals
    grown = []
    for cx, cv, rx, rv in ovals:
        grown.append((cx, cv, max(rx * .5, rx + reach / aspect),
                      max(rv * .5, rv + reach)))
    return tuple(grown)


class _Biomes:
    # One atlas's biome ovals as the climate leaves them.
    def __init__(self, climate, aspect, snowfields, tundra, dry_basins, wet_woods):
        self.snow = _grown(snowfields, climate.snow, aspect)
        self.tundra = _grown(tundra, climate.tundra, aspect)
        self.dry = _grown(dry_basins, climate.sand, aspect)
        self.wet = _grown(wet_woods, climate.jungle, aspect)
        # Under a harsher sun the grass around each desert scorches to plains.
        self.scorched = ()
        if climate.sand > 0.0:
            self.scorched = _grown(dry_basins, 1.75 * climate.sand, aspect)


def _known_climate_terrain(east, south, patch, peak, climate, biomes):
    # _land_terrain() with each frost line, desert and jungle moved by the
    # climate. With a Temperate climate it gives the same answers (checked by
    # tests/check_equus.py), but then _land_terrain() itself is used.
    if _in_biome(east, south, _CRYSTAL_BASIN) and not peak:
        return 'GRASS'  # the Crystal Heart keeps its valley green in any age
    if south < 0.077 + climate.snow or (peak and south < 0.175 + climate.snow):
        return 'SNOW'
    if south < 0.150 + climate.tundra:
        return 'TUNDRA'
    if _in_biome(east, south, biomes.dry):
        if patch < -0.57:
            return 'PLAINS'
        return 'DESERT'
    if _in_biome(east, south, biomes.wet) or _in_biome(east, south, _GRASSY_LOWLANDS):
        return 'GRASS'
    if _in_biome(east, south, biomes.scorched):
        return 'PLAINS'
    if south > 0.765 - climate.tundra and east < 0.690:
        if patch < -0.18:
            return 'TUNDRA'
        return 'PLAINS'
    if 0.399 < south < 0.469 and 0.276 < east < 0.522 and patch < 0.55:
        return 'PLAINS'
    if patch < climate.plains:
        return 'PLAINS'
    return 'GRASS'


def _known_level_ground(width, height):
    # Plots that _uplift() must not raise into peaks: the Known World's passes
    # and the Crystal Empire's basin, each with a plot to spare all round.
    level = set()
    for y in range(height):
        south = 1.0 - (y + 0.5) / height
        for x in range(width):
            east = (x + 0.5) / width
            for cx, cv, rx, rv in _PASSES + ((.390, .132, .054, .020),):
                if _in_oval(east, south, cx, cv, rx + 1.5 / width, rv + 1.5 / height):
                    level.add((x, y))
                    break
    return level


# A plot's eight neighbours, in order round it; the odd ones are its corners.
_AROUND = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))


def _way_through(plots, width, height, x, y):
    # Would a peak at (x, y) part two of its neighbours? Walk round the eight
    # plots about it: if the walkable ones form a single unbroken run, anyone
    # crossing (x, y) can go round instead. Two runs mean (x, y) may be the
    # only way between them. (A unit steps diagonally past a corner, so an
    # unwalkable corner between two walkable sides does not break a run.)
    walkable = []
    for dx, dy in _AROUND:
        kind = PlotTypes.PLOT_OCEAN
        if 0 <= x + dx < width and 0 <= y + dy < height:
            kind = plots[(y + dy) * width + x + dx]
        walkable.append(kind == PlotTypes.PLOT_LAND or kind == PlotTypes.PLOT_HILLS)
    for corner in (1, 3, 5, 7):
        if walkable[corner - 1] and walkable[(corner + 1) % 8]:
            walkable[corner] = True
    runs = 0
    for index in range(8):
        if walkable[index] and not walkable[index - 1]:
            runs += 1
    return runs > 1


def _uplift(plots, width, height, climate, level, label):
    # The Rocky climate. The atlas fixes where each range runs, so a rockier
    # world thickens the ranges it has: flat land beside hills may rise into
    # hills, and hills beside peaks may rise into peaks. Each plot is judged
    # against the map as it was before any plot rose, so a range grows by one
    # plot at most. No road is ever closed: plots in `level` (the marked
    # passes, causeways and basins) never become peaks, and neither does any
    # hill that is a way through (see _way_through), judged against the map
    # as it stands at that moment. Negative chances wear the edges down.
    dice = gc.getGame().getMapRand()
    before = list(plots)
    for y in range(height):
        for x in range(width):
            index = y * width + x
            kind = before[index]
            if kind != PlotTypes.PLOT_LAND and kind != PlotTypes.PLOT_HILLS:
                continue
            high = peaks = 0
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (1, -1), (-1, 1), (-1, -1)):
                if 0 <= x + dx < width and 0 <= y + dy < height:
                    other = before[index + dy * width + dx]
                    if other == PlotTypes.PLOT_PEAK:
                        peaks += 1
                    if other == PlotTypes.PLOT_PEAK or other == PlotTypes.PLOT_HILLS:
                        high += 1
            if kind == PlotTypes.PLOT_LAND:
                if climate.hills > 0 and high >= 1 and (x, y) not in level:
                    if dice.get(100, label) < climate.hills:
                        plots[index] = PlotTypes.PLOT_HILLS
            elif climate.peaks > 0 and peaks >= 2 and (x, y) not in level:
                if (not _way_through(plots, width, height, x, y) and
                        dice.get(100, label) < climate.peaks):
                    plots[index] = PlotTypes.PLOT_PEAK
            elif climate.hills < 0 and high <= 3:
                if dice.get(100, label) < -climate.hills:
                    plots[index] = PlotTypes.PLOT_LAND
    if climate.peaks < 0:
        for index in range(len(before)):
            if before[index] == PlotTypes.PLOT_PEAK:
                if dice.get(100, label) < -climate.peaks:
                    plots[index] = PlotTypes.PLOT_HILLS


class AtlasFeatureGenerator(EquusFeatureGenerator):
    # Forests and jungles for either atlas under any climate. A subclass says
    # which ovals to read (self.wet, self.woods) and where on its picture a
    # plot lies (spot); this class thins the trees in a dry climate.
    def __init__(self):
        EquusFeatureGenerator.__init__(self)
        self.climate = _Climate()
        if self.climate.thin:
            thin = self.climate.thin
            self.denseForest = self.forests.getHeightFromPercent(24 + thin)
            self.openForest = self.forests.getHeightFromPercent(83 + thin)
            self.wetJungle = self.jungles.getHeightFromPercent(41 + thin)

    def spot(self, x, y, south):
        return (x + 0.5) / self.iGridW, south

    def addJunglesAtPlot(self, plot, x, y, south):
        if plot.isWater():
            return  # open sea needs no place on the picture looked up
        east, south = self.spot(x, y, south)
        if (_in_biome(east, south, self.wet) and
                self.jungles.getHeight(x, y) >= self.wetJungle and
                plot.canHaveFeature(self.featureJungle)):
            plot.setFeatureType(self.featureJungle, -1)

    def addForestsAtPlot(self, plot, x, y, south):
        if not plot.canHaveFeature(self.featureForest):
            return
        east, south = self.spot(x, y, south)
        threshold = self.openForest
        if _in_biome(east, south, self.woods) or _in_biome(east, south, self.wet):
            threshold = self.denseForest
        if self.forests.getHeight(x, y) >= threshold:
            plot.setFeatureType(self.featureForest, -1)


class KnownClimateFeatureGenerator(AtlasFeatureGenerator):
    # The Known World under any climate but Temperate, which keeps using
    # EquusFeatureGenerator itself.
    def __init__(self):
        AtlasFeatureGenerator.__init__(self)
        self.wet = _grown(_WET_WOODS, self.climate.jungle, _KNOWN_ASPECT)
        self.woods = _WOODLANDS

    def addIceAtPlot(self, plot, x, y, south):
        # EquusFeatureGenerator's Great Iceberg Barrier, begun farther north
        # (or south) by the climate's reach.
        reach = self.climate.ice
        if south < 0.9 - reach or not plot.isWater() or plot.isLake():
            return
        east = (x + 0.5) / self.iGridW
        shelf = 0.995 - 0.060 * abs(2.0 * east - 1.0) - reach
        chance = int(55 + 1750 * (south - shelf))
        if chance > 0 and plot.canHaveFeature(self.featureIce):
            if self.mapRand.get(100, 'Equus southern pack ice') < chance:
                plot.setFeatureType(self.featureIce, -1)
# XANA 2026-11-28 END: the Climate option, for both atlases.


# XANA 2026-11-22 BEGIN: Equestria "Expanded" (Alternative Universe Expansions).
# (2026-11-28: sea room along any line, for the Inland Sea and the two rims;
# and the Climate option, through _Climate and _Biomes above.)
# A second atlas, traced from the "Equestria... and Beyond" world picture and
# chosen with the ATLAS_WORLD option. Every number below is a fraction of that
# picture's map area (inside its ornate frame): x from the west edge and v from
# the NORTH edge, exactly like the Known World tables above. Nothing in this
# block runs, and no random number is drawn here, unless that world is chosen.
_X_ASPECT = 1.5      # the picture is half again as wide as it is tall
_X_COAST_ROWS = 368  # latitudes at which the shore tables are sliced into spans

# Shores, as in the Known World: each triple is (distance south, west shore,
# east shore). To widen the Celestial Sea beside Manehattan, find the triples
# near v = .21 in _X_EQUESTRIA and pull their east shore west.
# A table can hold only one stretch of land per latitude, and this picture's
# coasts fold back on themselves. So each landmass is a main table plus named
# "arms" laid over it, wherever a bay puts a second stretch of land at the same
# latitude (the far side of Luna Bay; the Yucatan Ponynsula). Tables may
# overlap freely: a plot is land if any table covers it. -.10 and 1.10 carry a
# landmass past the top and bottom of the frame.
_X_EQUESTRIA = (  # Equestria, from Yakyakistan to Klugetown
    (.030, .084, .086), (.038, .079, .093), (.044, .075, .103),
    (.045, .075, .106), (.046, .075, .125), (.058, .067, .127),
    (.069, .059, .135), (.070, .059, .137), (.072, .057, .167),
    (.074, .054, .169), (.075, .034, .169), (.091, .023, .185),
    (.092, .022, .187), (.093, .022, .208), (.101, .025, .213),
    (.102, .025, .338), (.103, .025, .427), (.106, .026, .431),
    (.108, .056, .432), (.112, .065, .437), (.113, .067, .476),
    (.117, .069, .471), (.133, .072, .471), (.139, .077, .470),
    (.140, .077, .458), (.141, .077, .455), (.142, .091, .450),
    (.149, .097, .442), (.150, .097, .430), (.158, .101, .424),
    (.163, .106, .424), (.165, .107, .427), (.166, .108, .435),
    (.168, .109, .437), (.176, .109, .440), (.186, .118, .443),
    (.188, .119, .446), (.189, .119, .454), (.203, .119, .450),
    (.208, .123, .451), (.209, .125, .421), (.217, .126, .413),
    (.227, .113, .399), (.232, .109, .395), (.233, .103, .395),
    (.235, .099, .395), (.236, .083, .395), (.240, .078, .395),
    (.251, .071, .394), (.259, .071, .403), (.264, .073, .403),
    (.270, .072, .395), (.272, .070, .395), (.273, .064, .395),
    (.279, .060, .388), (.280, .046, .387), (.292, .047, .385),
    (.297, .042, .385), (.318, .042, .391), (.319, .062, .390),
    (.323, .066, .390), (.325, .066, .388), (.326, .066, .376),
    (.328, .066, .373), (.347, .054, .364), (.356, .049, .365),
    (.362, .042, .369), (.368, .041, .374), (.371, .040, .377),
    (.372, .040, .389), (.379, .035, .385), (.387, .036, .385),
    (.391, .035, .390), (.392, .047, .391), (.402, .053, .392),
    (.409, .058, .388), (.422, .055, .391), (.434, .053, .387),
    (.444, .056, .383), (.447, .052, .383), (.448, .028, .384),
    (.450, .025, .384), (.451, .020, .384), (.456, .019, .385),
    (.457, .019, .354), (.465, .019, .345), (.466, .029, .345),
    (.475, .042, .346), (.482, .043, .345), (.486, .037, .340),
    (.492, .034, .337), (.496, .022, .337), (.501, .021, .333),
    (.510, .011, .327), (.521, .007, .327), (.541, .018, .327),
    (.573, .011, .335), (.574, .043, .335), (.577, .046, .335),
    (.581, .046, .334), (.589, .040, .332), (.600, .040, .327),
    (.608, .043, .324), (.612, .047, .316), (.622, .049, .308),
    (.627, .054, .303), (.640, .054, .305), (.644, .054, .300),
    (.651, .056, .298), (.654, .056, .301), (.656, .056, .312),
    (.657, .056, .316), (.658, .056, .408), (.663, .056, .403),
    (.674, .068, .397), (.682, .072, .392), (.687, .081, .392),
    (.692, .084, .392), (.696, .084, .391), (.697, .085, .383),
    (.700, .085, .379), (.718, .087, .377), (.729, .083, .371),
    (.733, .076, .366), (.739, .077, .366), (.747, .074, .377),
    (.766, .074, .381), (.777, .070, .385), (.784, .067, .393),
    (.789, .067, .394), (.794, .069, .403), (.801, .069, .403),
    (.809, .069, .413), (.817, .072, .414), (.828, .086, .412),
    (.839, .091, .409), (.851, .091, .416), (.853, .089, .414),
    (.854, .136, .413), (.859, .140, .413), (.863, .140, .407),
    (.864, .243, .406), (.867, .247, .404), (.876, .248, .403),
    (.884, .251, .397), (.885, .251, .351), (.887, .251, .347),
    (.888, .251, .305), (.898, .247, .295), (.904, .246, .282),
    (.924, .245, .269), (.926, .245, .266), (.927, .245, .256),
    (.928, .247, .253))
_X_EQUESTRIA_ARMS = (
    # Mt. Everhoof
    ((-.10, .252, .325), (.006, .254, .320), (.010, .255, .320),
     (.011, .256, .308), (.014, .259, .305), (.023, .262, .303),
     (.031, .264, .305), (.037, .257, .307), (.045, .263, .311),
     (.056, .262, .316), (.073, .259, .329), (.081, .258, .341),
     (.084, .256, .341), (.085, .254, .323), (.086, .230, .322),
     (.089, .227, .319), (.097, .221, .322), (.099, .218, .328),
     (.100, .217, .335), (.102, .215, .337)),
    # Mt. Everhoof's western shoulder
    ((.018, .243, .244), (.025, .238, .254), (.035, .237, .254),
     (.037, .237, .253), (.038, .237, .245), (.042, .238, .240)),
    # Mt. Everhoof's eastern spur
    ((.057, .361, .362), (.063, .359, .366), (.073, .358, .381),
     (.082, .352, .384), (.084, .351, .386), (.085, .350, .395),
     (.092, .344, .400), (.093, .344, .408), (.096, .344, .415),
     (.099, .343, .419), (.101, .341, .425), (.103, .340, .426)),
    # Smokey's Cave, at Trottingham Bridge
    ((.087, .449, .453), (.091, .446, .459), (.092, .445, .466),
     (.108, .442, .466), (.109, .442, .468), (.110, .441, .474),
     (.113, .438, .476)),
    # Luna Bay's western arm
    ((.106, .028, .054), (.124, .033, .047), (.136, .033, .048),
     (.144, .033, .049), (.150, .026, .052), (.162, .025, .052),
     (.174, .023, .047), (.176, .023, .040), (.184, .029, .032)),
    # Tampa Neigh
    ((.456, .356, .385), (.469, .361, .393), (.471, .362, .396),
     (.472, .362, .403), (.475, .362, .403), (.479, .362, .411),
     (.494, .366, .413), (.495, .367, .392), (.497, .367, .389),
     (.498, .367, .384), (.507, .371, .375)),
    # Mareiami keys
    ((.494, .392, .413), (.499, .395, .413), (.501, .400, .413),
     (.508, .406, .419), (.521, .406, .418), (.531, .398, .420),
     (.541, .398, .419), (.544, .398, .415), (.552, .406, .408)),
    # Yucatan Ponynsula and the Changeling Kingdom
    ((.565, .378, .379), (.569, .374, .384), (.570, .373, .395),
     (.585, .371, .406), (.592, .368, .408), (.606, .371, .410),
     (.618, .369, .413), (.622, .365, .413), (.629, .364, .410),
     (.637, .355, .408), (.645, .351, .411), (.653, .334, .411),
     (.654, .320, .411), (.658, .317, .408)),
    # cape of the south-western sands
    ((.573, .011, .042), (.578, .013, .033), (.582, .014, .033),
     (.584, .014, .023), (.586, .015, .020)),
    # cliffs below the Royal Guard tower
    ((.853, .103, .135), (.862, .114, .132), (.863, .116, .124),
     (.864, .117, .122)),
    # Pine Needle Barrens
    ((.863, .140, .243), (.871, .145, .238), (.888, .154, .238),
     (.901, .167, .235), (.902, .169, .235), (.903, .206, .235),
     (.910, .211, .232), (.914, .215, .224), (.919, .218, .222)),
    # southern shore
    ((.887, .306, .345), (.895, .313, .343), (.897, .322, .341),
     (.898, .324, .335), (.902, .329, .329)),
    # Klugetown's shore
    ((.884, .353, .396), (.887, .356, .395), (.888, .366, .394),
     (.889, .368, .394), (.890, .376, .393), (.902, .385, .387)))
_X_PONYLAND = (  # Ponyland, the Fields of Forever and Horsetrailia
    (-.10, .667, .712), (.002, .667, .712), (.003, .676, .710),
    (.005, .678, .708), (.009, .681, .708), (.014, .681, .713),
    (.015, .681, .715), (.016, .681, .738), (.021, .675, .741),
    (.022, .666, .743), (.023, .665, .744), (.025, .665, .782),
    (.030, .665, .786), (.031, .664, .792), (.033, .663, .795),
    (.034, .662, .869), (.040, .655, .869), (.054, .653, .858),
    (.063, .646, .854), (.064, .644, .854), (.065, .597, .854),
    (.069, .597, .853), (.074, .592, .853), (.075, .505, .853),
    (.093, .505, .862), (.094, .505, .943), (.113, .503, .942),
    (.117, .503, .946), (.121, .499, .948), (.122, .485, .949),
    (.128, .482, .952), (.144, .479, .952), (.145, .495, .952),
    (.148, .500, .952), (.149, .509, .952), (.152, .513, .952),
    (.162, .513, .952), (.163, .513, .945), (.171, .513, .938),
    (.172, .513, .929), (.178, .513, .924), (.180, .513, .917),
    (.184, .513, .912), (.191, .513, .909), (.205, .516, .910),
    (.223, .505, .910), (.225, .503, .912), (.227, .495, .912),
    (.243, .478, .912), (.246, .474, .915), (.247, .474, .920),
    (.248, .689, .923), (.252, .692, .925), (.258, .692, .933),
    (.268, .689, .930), (.272, .689, .925), (.292, .689, .928),
    (.295, .685, .928), (.296, .677, .894), (.297, .668, .892),
    (.299, .739, .891), (.302, .743, .890), (.305, .743, .887),
    (.314, .744, .888), (.322, .749, .887), (.323, .749, .881),
    (.332, .744, .872), (.336, .740, .870), (.337, .734, .870),
    (.348, .734, .869), (.349, .734, .860), (.352, .734, .856),
    (.362, .735, .856), (.375, .737, .865), (.383, .748, .866),
    (.386, .749, .867), (.394, .750, .866), (.398, .756, .862),
    (.413, .764, .865), (.422, .768, .858), (.430, .770, .857),
    (.438, .773, .858), (.455, .783, .860), (.460, .787, .865),
    (.470, .789, .865), (.475, .789, .872), (.479, .789, .882),
    (.486, .791, .886), (.490, .792, .893), (.494, .795, .893),
    (.509, .795, .889), (.510, .796, .881), (.518, .800, .877),
    (.530, .806, .888), (.534, .806, .893), (.535, .805, .897),
    (.545, .801, .902), (.546, .800, .914), (.547, .799, .941),
    (.552, .791, .947), (.553, .788, .966), (.554, .761, .966),
    (.567, .756, .967), (.597, .762, .974), (.606, .770, .973),
    (.613, .778, .972), (.625, .776, .970), (.633, .770, .967),
    (.639, .771, .965), (.648, .778, .954), (.649, .778, .951),
    (.650, .779, .936), (.652, .782, .933), (.659, .785, .932),
    (.664, .789, .937), (.671, .799, .936), (.672, .799, .929),
    (.677, .803, .917), (.686, .804, .916), (.692, .805, .908),
    (.708, .817, .898), (.713, .816, .894), (.719, .809, .890),
    (.725, .810, .886), (.734, .807, .886), (.745, .808, .873),
    (.757, .803, .866), (.760, .804, .858), (.765, .805, .854),
    (.769, .810, .854), (.782, .807, .856), (.789, .807, .851),
    (.804, .799, .851), (.805, .805, .851), (.811, .812, .851),
    (.812, .824, .851), (.819, .834, .847), (.822, .838, .842))
_X_PONYLAND_ARMS = (
    # Midnight Castle and Bug Bear Territory
    ((.034, .565, .566), (.043, .555, .574), (.044, .549, .574),
     (.045, .538, .574), (.050, .534, .575), (.051, .514, .574),
     (.059, .508, .574), (.063, .507, .577), (.065, .506, .584),
     (.075, .505, .589)),
    # Sea of Shadows shore
    ((.047, .615, .615), (.050, .611, .618), (.051, .603, .618),
     (.057, .600, .623), (.058, .599, .639), (.065, .597, .643)),
    # Ponyland's southern shore
    ((.247, .474, .688), (.254, .474, .682), (.264, .476, .682),
     (.265, .476, .631), (.272, .466, .621), (.279, .466, .617),
     (.280, .466, .597), (.281, .466, .594), (.282, .466, .582),
     (.283, .467, .577), (.285, .468, .574), (.287, .468, .558),
     (.293, .468, .550), (.300, .474, .543), (.301, .506, .539),
     (.309, .516, .528), (.312, .524, .525)),
    # Jewel Desert's southern cape
    ((.264, .634, .681), (.272, .648, .677), (.277, .653, .665),
     (.278, .660, .665), (.279, .663, .663)),
    # Neighples
    ((.297, .668, .739), (.309, .669, .732), (.311, .694, .732),
     (.319, .703, .729), (.328, .705, .723), (.336, .703, .726),
     (.343, .702, .723), (.348, .704, .722), (.355, .715, .715)),
    # northern capes
    ((-.10, .758, .767), (.009, .757, .765), (.015, .756, .773),
     (.019, .755, .776), (.022, .752, .781), (.023, .745, .782),
     (.025, .745, .782)),
    ((.006, .803, .804), (.010, .800, .808), (.023, .800, .810),
     (.031, .799, .819)),
    # Cloud Castle
    ((-.10, .847, .857), (.015, .849, .858), (.018, .846, .858),
     (.019, .835, .858), (.023, .834, .859), (.030, .821, .866),
     (.031, .799, .867), (.034, .796, .868)),
    # Antleria: the Ice Kingdom's northern shore
    ((.051, .923, .925), (.059, .915, .927), (.061, .912, .927),
     (.062, .893, .926), (.063, .883, .926), (.076, .875, .928),
     (.081, .875, .933), (.082, .875, .938), (.088, .873, .940),
     (.094, .863, .942)))
_X_ZEBRICA = (  # Saddle Arabia, Zebrica, Abyssinia and the Dragon Lands
    (.323, .575, .581), (.324, .573, .588), (.326, .569, .592),
    (.327, .526, .593), (.335, .521, .597), (.337, .517, .601),
    (.338, .516, .608), (.342, .513, .613), (.353, .506, .615),
    (.354, .458, .615), (.367, .461, .617), (.382, .454, .615),
    (.388, .451, .620), (.399, .447, .619), (.402, .446, .623),
    (.403, .446, .729), (.409, .446, .729), (.413, .447, .734),
    (.414, .447, .754), (.427, .449, .748), (.433, .455, .747),
    (.436, .461, .743), (.446, .467, .740), (.458, .469, .737),
    (.466, .473, .738), (.475, .472, .754), (.498, .470, .748),
    (.505, .476, .747), (.513, .475, .744), (.514, .555, .744),
    (.515, .592, .745), (.516, .594, .745), (.526, .604, .743),
    (.533, .605, .742), (.539, .611, .743), (.562, .607, .741),
    (.574, .606, .744), (.580, .615, .745), (.593, .618, .732),
    (.598, .618, .723), (.605, .616, .713), (.606, .616, .690),
    (.609, .615, .687), (.621, .610, .685), (.633, .613, .682),
    (.638, .614, .687), (.639, .614, .742), (.645, .610, .744),
    (.646, .558, .744), (.651, .558, .746), (.658, .552, .748),
    (.659, .534, .748), (.672, .537, .749), (.675, .537, .752),
    (.676, .537, .757), (.686, .542, .759), (.696, .542, .767),
    (.699, .539, .768), (.700, .526, .768), (.713, .528, .768),
    (.717, .523, .768), (.718, .512, .768), (.728, .505, .766),
    (.741, .514, .764), (.747, .514, .760), (.753, .517, .761),
    (.759, .529, .762), (.763, .529, .766), (.769, .529, .766),
    (.772, .524, .765), (.773, .523, .714), (.775, .521, .713),
    (.776, .493, .711), (.791, .492, .709), (.800, .491, .699),
    (.801, .583, .698), (.802, .584, .687), (.809, .588, .677),
    (.811, .602, .675), (.814, .605, .671), (.830, .605, .664),
    (.837, .597, .663), (.844, .594, .652), (.851, .594, .649),
    (.852, .618, .647), (.856, .626, .641), (.859, .629, .633))
_X_ZEBRICA_ARMS = (
    # Griffonstone's northern cape
    ((.320, .482, .495), (.326, .471, .501), (.331, .463, .501),
     (.340, .458, .499), (.342, .455, .499), (.343, .449, .500),
     (.350, .448, .502), (.354, .458, .505)),
    # Turkey Region's northern capes
    ((.371, .650, .654), (.375, .642, .656), (.390, .645, .652),
     (.395, .638, .655), (.397, .638, .657)),
    ((.389, .669, .670), (.390, .668, .677), (.396, .661, .681),
     (.397, .637, .682), (.400, .634, .686), (.401, .633, .728),
     (.402, .624, .729), (.403, .624, .729)),
    # lighthouse point west of Oranma
    ((.361, .718, .719), (.370, .714, .727), (.390, .702, .728),
     (.401, .688, .728)),
    # Zebrica's south-western hook
    ((.513, .488, .548), (.522, .493, .542), (.523, .510, .542),
     (.526, .513, .540), (.535, .517, .533), (.544, .518, .534),
     (.545, .524, .534), (.547, .526, .536), (.555, .531, .534)),
    ((.514, .556, .589), (.526, .561, .579), (.530, .563, .579),
     (.532, .566, .578), (.533, .573, .576)),
    # Catebox Ridge's northern shore
    ((.615, .714, .715), (.621, .713, .724), (.622, .713, .731),
     (.625, .711, .734), (.626, .692, .735), (.633, .692, .741),
     (.639, .688, .742)),
    # Dragon Lands: the northern cape
    ((.593, .560, .562), (.600, .560, .568), (.601, .560, .573),
     (.603, .560, .576), (.604, .560, .588), (.622, .559, .587),
     (.628, .559, .590), (.632, .559, .594), (.633, .558, .600),
     (.635, .556, .604), (.646, .558, .609)),
    # Panthera
    ((.761, .500, .500), (.763, .495, .502), (.765, .494, .506),
     (.766, .494, .513), (.776, .493, .521)),
    ((.800, .492, .581), (.806, .492, .575), (.807, .492, .568),
     (.809, .492, .566), (.815, .492, .563), (.816, .516, .561),
     (.818, .519, .559), (.819, .526, .558), (.823, .529, .557),
     (.824, .544, .557), (.836, .550, .552)))
_X_POLAR = (
    # Agarica
    ((.932, .617, .637), (.949, .605, .650), (.950, .583, .650),
     (.951, .581, .652), (.953, .570, .652), (.955, .568, .655),
     (.956, .566, .663), (.958, .563, .665), (.968, .563, .674),
     (.979, .555, .676), (.987, .558, .690), (.995, .560, .693),
     (1.10, .560, .701)),
    # Agarica's eastern ice
    ((.914, .708, .710), (.918, .702, .716), (.921, .699, .718),
     (.922, .689, .718), (.931, .691, .726), (.932, .691, .741),
     (.937, .690, .737), (.946, .689, .738), (.953, .694, .741),
     (.958, .694, .744), (.960, .698, .745), (.967, .705, .744),
     (.977, .707, .740), (.980, .707, .744), (.981, .707, .757),
     (.987, .704, .757), (.994, .710, .760), (.996, .711, .763),
     (.997, .711, .768), (1.10, .711, .770)),
    # the Mysterious South
    ((.947, .408, .411), (.948, .390, .413), (.951, .388, .418),
     (.953, .390, .448), (.954, .408, .448), (.956, .411, .445),
     (.963, .411, .445), (.966, .411, .448), (.967, .411, .455),
     (.975, .406, .453), (.980, .398, .453), (.981, .381, .453),
     (.990, .366, .450), (.997, .360, .451), (.998, .334, .452),
     (1.10, .334, .452)),
    ((.982, .344, .345), (.989, .338, .353), (1.10, .335, .359)),
    # south-eastern ice shelf
    ((.906, .836, .836), (.908, .832, .841), (.920, .823, .847),
     (.921, .823, .861), (.925, .820, .867), (.926, .820, .881),
     (.937, .820, .895), (.938, .820, .947), (.951, .831, .944),
     (.953, .832, .924), (.954, .833, .923), (.955, .847, .921),
     (.961, .852, .918), (.962, .852, .899), (.967, .852, .891),
     (.970, .852, .872), (.973, .852, .868), (.979, .862, .864)),
    ((.911, .916, .917), (.918, .909, .919), (.926, .907, .923),
     (.931, .904, .932), (.932, .903, .954), (.938, .897, .947)),
    # Chaonville
    ((.891, .943, .944), (.896, .941, .949), (.897, .941, .956),
     (.908, .937, .957), (.915, .938, .961), (.926, .937, .959),
     (.932, .933, .954)))
_X_ISLANDS = (
    # Storm King's Realm
    ((.928, .114, .116), (.938, .107, .131), (.939, .106, .151),
     (.943, .101, .151), (.951, .098, .156), (.957, .104, .157),
     (.961, .106, .164), (.971, .111, .169), (.972, .112, .169),
     (.973, .118, .148), (.981, .130, .137)),
    # Monkey Dancing Islands
    ((.315, .927, .928), (.335, .920, .939), (.338, .917, .937),
     (.339, .909, .935), (.350, .908, .923), (.365, .913, .917),
     (.373, .913, .926), (.374, .912, .938), (.376, .909, .940),
     (.377, .899, .941), (.387, .902, .944), (.395, .900, .935),
     (.396, .899, .923), (.398, .899, .920), (.412, .902, .915),
     (.421, .905, .907)),
    ((.295, .896, .928), (.301, .901, .928), (.306, .902, .917),
     (.315, .904, .914), (.318, .908, .909)),
    # isle off Horsetrailia's south-east cape
    ((.697, .916, .917), (.708, .907, .923), (.709, .907, .938),
     (.722, .897, .937), (.728, .901, .938), (.743, .901, .933),
     (.749, .915, .931), (.751, .926, .931), (.752, .928, .930)))
_X_SHORES = ((_X_EQUESTRIA,) +
             _X_EQUESTRIA_ARMS +
             (_X_PONYLAND,) +
             _X_PONYLAND_ARMS +
             (_X_ZEBRICA,) +
             _X_ZEBRICA_ARMS +
             _X_POLAR +
             _X_ISLANDS)

# Small islands: center x, center v, radii. Each keeps a one-plot core on Duel.
_X_ISLES = (
    (.017, .124, .005, .015),  # ice islet west of Luna Bay
    (.423, .320, .010, .021),  # Trotaway Island
    (.413, .423, .013, .023),  # Bermuldy Island
    (.627, .338, .010, .019),  # Griffish Isles
    (.606, .324, .006, .009),
    (.643, .326, .005, .010),
    (.022, .636, .011, .011),  # islets off the south-western desert
    (.034, .660, .007, .010),
    (.050, .690, .010, .019),
    (.038, .866, .014, .027),  # Canabula
    (.447, .655, .012, .012),  # Galloppingos Islands
    (.428, .680, .008, .016),
    (.468, .675, .008, .018),
    (.440, .708, .012, .010),
    (.457, .729, .006, .014),
    (.460, .826, .010, .010),  # Black Skull Island
    (.482, .889, .010, .017),  # Mount Aris
    (.888, .437, .012, .023),  # Macow
    (.915, .493, .014, .023),  # Tapir isles
    (.952, .523, .006, .012))  # Tobi
# One guaranteed land plot inside each island that has a shore table.
_X_CORES = ((.134, .959),  # Storm King's Realm
            (.911, .390),  # Monkey Dancing Islands
            (.920, .728))  # isle off Horsetrailia's south-east cape

# Inland waters, which the shore tables pass straight over: center x, center v, radii.
_X_LAKES = (
    (.308, .246, .022, .026),  # the lake north-east of Canterlot
    (.279, .281, .014, .024),  # ... and its southern arm
    (.218, .772, .018, .014),  # Froud Valley lake
    (.853, .523, .011, .024),  # lagoon on Horsetrailia's isthmus
    (.828, .771, .013, .016))  # lake behind the Lost Lagoon

# The picture draws two bridges where it also draws open water. Civ has no
# bridges, so choose here: True lays a one-plot causeway that armies can walk
# (and ships cannot pass); False keeps each crossing as a strait.
EXPANDED_BRIDGES_ARE_LAND = True
# Each bridge is (causeway path across the water, channel path along it).
# The causeways run on into each shore, along the picture's railway, so that
# no peak can close a bridgehead.
_X_BRIDGES = (
    (((.405,.130), (.452,.104), (.516,.104), (.535,.118)),  # Trottingham Bridge
     ((.486,.040), (.486,.100), (.473,.118), (.473,.140), (.465,.165),
      (.455,.200))),
    (((.500,.250), (.490,.285), (.490,.360)),           # Griffonstone rail trestle
     ((.440,.312), (.502,.312))))
# The sea down the middle of the world, from below Trottingham to the Crystal
# Sea, as an (x, v) path that keeps to open water. It is a sea lane, and it is
# the line along which _X_SEA_ROOM parts the two shores.
_X_CELESTIAL_SEA = (
    (.465,.165), (.455,.200), (.445,.250), (.440,.300), (.437,.360),
    (.436,.450), (.438,.520), (.430,.600), (.420,.660), (.422,.760),
    (.428,.840), (.430,.910))
# The water that parts Ponyland from Zebrica: east along the Great Inland
# Sea, south-east past Oranma, south between Zebrica and Horsetrailia, and out
# into the Asparus Sea. Also both a sea lane and a line for _X_SEA_ROOM.
_X_INLAND_SEA = (
    (.502,.312), (.560,.311), (.600,.303), (.660,.300), (.688,.332),
    (.705,.352), (.727,.352), (.733,.375), (.745,.398), (.760,.416),
    (.770,.445), (.776,.500), (.772,.530), (.750,.560), (.752,.580),
    (.745,.600), (.752,.620), (.757,.640), (.767,.660), (.780,.680),
    (.790,.700), (.790,.760), (.780,.830))
# Sea room. As drawn, the Celestial Sea is seven plots across on a Huge map
# beside Griffonstone, and Bermuldy and Trotaway Islands fill half of that;
# the channel past Oranma is one plot. Each row here opens a sea along a
# line, like parting a curtain: the shores on both sides move straight away
# from the line, new sea fills the gap, and the land farther off is squeezed a
# little to make the room. Nothing is cut away, so capes and isles keep their
# shapes. The line may run any way and may bend. A line down a map edge
# pushes the land in from that edge, which is how the two rims get their sea.
#   extra   sea added on EACH side of the line, as a fraction of the map's
#           width. .0085 is one plot on a Huge map and .017 is two; the same
#           fraction is about one plot on Standard and half a plot on Duel.
#   rigid   within this distance of the line, land moves in one piece.
#   fade    the squeeze has died away at this distance from the line.
#           (Both are fractions of the map's width, in every direction.)
#   line    the (x, v) path. The widening eases in and out over about the
#           first and last _X_SEA_ROOM_EASE of its length.
# Set extra to 0 (or delete the row) for that sea exactly as the picture has
# it; empty the table for the whole picture as drawn.
_X_SEA_ROOM_EASE = .04
_X_SEA_ROOM = (
    (.015, .085, .210, _X_CELESTIAL_SEA),                # Equestria from the east
    (.015, .050, .150, _X_INLAND_SEA),                   # Ponyland from Zebrica
    (.013, .040, .160, ((0.0,.100), (0.0,.920))),        # the western rim
    (.013, .040, .160, ((1.0,.100), (1.0,.920))))        # the eastern rim
# Sea lanes that must stay open at every map size, as (x, v) paths. Without
# them a Duel grid would weld Equestria, Ponyland and Zebrica together, and
# seal bays whose mouths are narrower than one plot. Pack ice never forms on
# a lane either, so the Great Iceberg Barrier cannot close the southern route.
_X_STRAITS = (
    ((.001,.200), (.001,.935)),                         # North to South Luna Ocean
    ((.999,.300), (.999,.860)),                         # Sparkling Sea, round Horsetrailia's cape
    _X_CELESTIAL_SEA,                                   # Celestial Sea to Crystal Sea
    _X_INLAND_SEA,                                      # Great Inland Sea to Asparus Sea
    ((.600,.578), (.555,.575), (.515,.590), (.480,.610)),  # Tergum Sea
    ((.001,.935), (.085,.915), (.200,.923), (.250,.935), (.330,.938), (.400,.935),
     (.470,.930), (.520,.925), (.560,.895), (.620,.880), (.680,.870),
     (.740,.845), (.800,.840), (.900,.840), (.990,.840)))  # north of the Great Iceberg Barrier
# Necks of land that must stay walkable at every map size.
_X_LAND_LINKS = (
    ((.815,.390), (.815,.530), (.822,.585)),            # Sanchez tunnel and Horsetrailia's isthmus
    ((.848,.150), (.875,.125)),                         # Antleria
    ((.640,.108), (.730,.108)),                         # Grundleland road, Ponyland to the Fields
    ((.665,.600), (.665,.680)),                         # Zebrica to Abyssinia
    ((.600,.722), (.650,.722)),                         # Dragon Lands to Abyssinia
    ((.600,.700), (.600,.780)),                         # the pass over the Dragon's Spine
    ((.480,.462), (.530,.462)),                         # Griffonstone to Saddle Arabia
    ((.356,.690), (.375,.620)))                         # Yucatan Ponynsula

# Ranges: half-width (in x units), crest strength, path of (x, v) points.
_X_RANGES = (
    # ---- Equestria
    # Yak Range and Mt. Everhoof
    (.030, 1.00, ((.030,.075), (.070,.050), (.120,.050), (.170,.070),
                  (.220,.075), (.270,.060), (.300,.040), (.340,.070),
                  (.380,.095), (.440,.110))),
    # the Yak Range's southern wall
    (.022, .95, ((.140,.105), (.180,.110), (.220,.115), (.260,.105),
                 (.310,.100), (.345,.105))),
    # Crystal Mountains
    (.022, .95, ((.185,.125), (.215,.155), (.250,.175), (.290,.190),
                 (.330,.170), (.360,.150), (.390,.160))),
    # Unicorn Range
    (.016, .85, ((.135,.210), (.165,.235), (.190,.265), (.195,.290))),
    # Smokey Mountains
    (.022, .83, ((.085,.285), (.105,.270), (.135,.275), (.160,.300))),
    # Canterlot
    (.012, 1.00, ((.262,.305), (.270,.335))),
    # Foal Mountain
    (.015, .83, ((.305,.335), (.325,.345), (.345,.340))),
    # Rambling Rock Ridge
    (.013, .70, ((.292,.385), (.305,.405), (.318,.425))),
    # Macintosh Hills
    (.016, .55, ((.245,.485), (.275,.480), (.305,.470))),
    # Appaloosan Mountains
    (.024, .95, ((.050,.515), (.085,.490), (.125,.475), (.165,.475),
                 (.205,.475), (.240,.485))),
    # San Palomino mesas
    (.020, .60, ((.055,.470), (.075,.455), (.100,.445))),
    # Arimaspi Territory
    (.016, .90, ((.070,.560), (.090,.550), (.110,.560))),
    # south-western bluffs
    (.014, .65, ((.055,.600), (.075,.615), (.090,.640), (.075,.660))),
    # Badlands
    (.022, .60, ((.220,.555), (.245,.550), (.265,.570))),
    # Bumpy Cliffs, around Froud Valley
    (.014, .80, ((.135,.770), (.140,.720), (.175,.705), (.205,.715),
                 (.232,.740), (.250,.780))),
    (.014, .80, ((.135,.770), (.145,.830), (.180,.860), (.215,.855))),
    # cliffs below the Royal Guard tower
    (.012, .70, ((.075,.800), (.095,.835), (.125,.865))),
    # domed hills north of the Bone Dry Desert
    (.018, .65, ((.262,.825), (.285,.820), (.300,.835))),
    # Changeling hive
    (.008, .90, ((.385,.585), (.386,.600))),
    # Storm King's Realm
    (.014, .90, ((.115,.945), (.145,.950), (.160,.965))),
    # Mount Aris
    (.010, .96, ((.479,.882), (.487,.895))),
    # ---- Ponyland and the east
    # Bug Bear Territory
    (.020, .95, ((.515,.085), (.535,.060), (.555,.050), (.575,.075))),
    # Purple Mountains
    (.017, .95, ((.665,.035), (.675,.070), (.688,.095))),
    (.012, .80, ((.625,.115), (.655,.120))),
    # Volcano of Gloom
    (.012, 1.00, ((.652,.150), (.658,.165))),
    # Black Mountains
    (.018, .95, ((.672,.135), (.680,.150), (.685,.190), (.675,.230),
                 (.660,.265))),
    # Jewel Desert's canyon wall
    (.008, .60, ((.615,.170), (.620,.215))),
    # Mt. Vehoovius
    (.020, .92, ((.705,.225), (.720,.250), (.745,.260), (.757,.290),
                 (.765,.325))),
    # Cloud Castle peaks
    (.014, .90, ((.805,.020), (.845,.015))),
    # white hills below Cloud Castle
    (.025, .55, ((.775,.060), (.805,.075), (.830,.100))),
    # Antleria's twin peaks
    (.014, .95, ((.880,.165), (.895,.150))),
    # eastern coast range
    (.017, .90, ((.880,.190), (.870,.225), (.868,.265), (.862,.300),
                 (.855,.335))),
    # Sanchez Mountains
    (.022, .92, ((.780,.425), (.805,.415), (.830,.420), (.852,.405))),
    # Horsetrailia's western range
    (.020, .90, ((.785,.610), (.805,.635), (.830,.655), (.860,.670),
                 (.885,.665))),
    # Ram Brat escarpment
    (.016, .75, ((.860,.535), (.885,.560), (.915,.595), (.945,.615),
                 (.962,.590))),
    (.012, .60, ((.850,.730), (.865,.725))),
    (.012, .60, ((.915,.725), (.925,.732))),
    # ---- Zebrica, Abyssinia and the Dragon Lands
    # Griffonstone and Griffin Gorge
    (.013, .85, ((.466,.345), (.464,.385), (.468,.420), (.478,.450))),
    # Zebrica's northern hills
    (.014, .85, ((.665,.445), (.690,.450))),
    # the mountains east of Oranma
    (.012, .85, ((.752,.455), (.745,.490), (.735,.520))),
    (.014, .80, ((.740,.500), (.730,.540), (.715,.575))),
    # Catebox Ridge
    (.018, .85, ((.695,.645), (.725,.635), (.755,.645))),
    # Abyssinia's southern ridges
    (.016, .70, ((.705,.735), (.740,.715), (.770,.700))),
    (.012, .70, ((.635,.755), (.670,.750), (.705,.745))),
    # Dragon Lands volcanoes
    (.017, .95, ((.565,.615), (.575,.645), (.590,.655), (.610,.665))),
    # Dragon's Spine
    (.018, .95, ((.550,.753), (.565,.750), (.590,.745), (.615,.740),
                 (.635,.735))),
    # lava fields
    (.014, .60, ((.530,.700), (.540,.730))))
# Level ground inside a range: center x, center v, radii.
_X_BASINS = ((.283, .143, .022, .024),                  # Crystal Empire
             (.105, .078, .022, .018))                  # Yakyakistan
# Passes: a range is cut down to hills inside these ovals.
_X_PASSES = ((.120,.110,.012,.022),                     # Yakyakistan to Luna Bay
             (.235,.182,.012,.022), (.345,.163,.012,.022),  # Crystal Mountains
             (.192,.485,.011,.030),                     # Appaloosan rail gap
             (.452,.106,.018,.022), (.514,.100,.014,.022),  # Trottingham bridgeheads
             (.683,.115,.020,.018), (.692,.205,.012,.020),  # Grundleland road, Black Mountains
             (.496,.400,.011,.075),                     # Griffonstone's railway
             (.822,.428,.009,.026),                     # Sanchez tunnel
             (.842,.656,.009,.022),                     # Horsetrailia's outback road
             (.600,.745,.014,.030), (.580,.785,.050,.018),  # Dragon's Spine, Panthera's coast road
             (.206,.728,.010,.020), (.242,.820,.012,.020))  # Froud Valley's gates

# Biome ovals: center x, center v, radii, as in the Known World tables.
_X_HAVENS = (
    (.283, .143, .030, .030),  # Crystal Empire
    (.948, .935, .013, .036))  # Chaonville
_X_SNOWFIELDS = (
    (.160, .165, .075, .035),  # snowfields above Vanhoover
    (.038, .145, .022, .048),  # Luna Bay's western arm
    (.017, .124, .008, .020),
    (.545, .072, .035, .040),  # Bug Bear Territory
    (.720, .042, .032, .050),  # white coast north of the Purple Mountains
    (.905, .112, .058, .068),  # Antleria, the Ice Kingdom
    (.720, .762, .038, .020))  # Black Valley
_X_TUNDRA = (
    (.190, .178, .130, .030),  # Vanhoover and the Crystal foothills
    (.590, .055, .095, .050),  # Ponyland's northern shore
    (.790, .070, .075, .065),  # the white hills
    (.665, .805, .042, .040),  # Abyssinia's southern shore
    (.818, .797, .028, .025),  # Horsetrailia's southern cape
    (.136, .950, .040, .040),  # Storm King's Realm
    (.600, .975, .030, .018))  # Agarica Forest
_X_DRY_BASINS = (
    (.085, .455, .060, .025),  # San Palomino Desert, Las Pegasus
    (.035, .550, .028, .050),  # south-western sands
    (.085, .635, .035, .050),  # Bay of the Battle of Dunsmare
    (.240, .565, .035, .040),  # Badlands
    (.185, .790, .060, .065),  # Froud Valley
    (.345, .845, .065, .050),  # Bone Dry Desert and Klugetown
    (.565, .410, .065, .085),  # Saddle Arabia
    (.690, .425, .065, .035),  # Turkey Region and Oranma
    (.745, .440, .012, .035),
    (.748, .355, .015, .030),  # Marlonga
    (.640, .215, .035, .060),  # Jewel Desert
    (.585, .715, .040, .030),  # Red Ruby Desert
    (.710, .695, .055, .040),  # Desert of Infinity
    (.845, .630, .050, .055),  # Breezewood and the Opal Mines
    (.905, .585, .040, .035))  # Ram Brat Sand Dunes
_X_STEPPES = (
    (.190, .430, .070, .040),  # Appleloosa and Salt Lick City
    (.535, .720, .020, .035),  # Dragon Lands lava fields
    (.690, .740, .070, .025),  # Abyssinia's southern plateau
    (.870, .690, .050, .030),  # Horsetrailia's savanna
    (.280, .825, .030, .025),  # domed hills
    (.480, .345, .020, .030))  # Griffonstone's heights
_X_GRASSY_LOWLANDS = (
    (.235, .330, .060, .045),  # Ponyville and Canterlot
    (.800, .220, .060, .140),  # Fields of Forever
    (.300, .760, .060, .050),  # Prancing Plains
    (.380, .630, .025, .050))  # Changeling Kingdom
_X_WET_WOODS = (
    (.130, .590, .075, .070),  # Amarezonia: Forbidden Jungle
    (.260, .630, .070, .070),  # Amarezonia: the eastern rainforest
    (.170, .680, .070, .035),  # Forest of Leota
    (.655, .555, .045, .080),  # Zebrica's central jungle
    (.715, .535, .035, .060),  # Zebrica's eastern jungle
    (.630, .470, .030, .035),  # Harmonia
    (.655, .670, .030, .050),  # Abyssinia's northern forest
    (.555, .795, .055, .030),  # Panthera
    (.645, .785, .040, .025),  # Zanzebra
    (.820, .500, .050, .060),  # Horsetrailia's rainforest
    (.785, .580, .025, .035),
    (.835, .745, .040, .045),  # Lost Lagoon
    (.915, .370, .030, .060),  # Monkey Dancing Islands
    (.888, .438, .016, .028),  # Macow
    (.915, .490, .020, .030),  # Tapir isles
    (.450, .680, .035, .045))  # Galloppingos Islands
_X_WOODLANDS = (
    (.130, .300, .070, .060),  # Smokey Mountains and White Tail Woods
    (.160, .230, .050, .030),  # Vanhoover's forests
    (.285, .430, .045, .040),  # Everfree Forest
    (.370, .170, .045, .050),  # Stratusburg to Manehattan
    (.360, .280, .040, .060),  # Hollow Shades
    (.365, .455, .040, .050),  # woods south of Horseshoe Bay
    (.330, .700, .045, .070),  # Silver & Scott Meadow woods
    (.305, .885, .045, .030),  # southern shore
    (.200, .890, .050, .035),  # Pine Needle Barrens
    (.110, .740, .035, .050),  # Timberwolf Territory
    (.600, .115, .070, .040),  # Ponyland's northern forests
    (.555, .210, .060, .050),  # Flutter Valley
    (.500, .265, .030, .035),
    (.725, .165, .040, .040),  # forests about Mt. Vehoovius
    (.730, .300, .035, .040),
    (.875, .250, .035, .085),  # eastern coast
    (.820, .440, .045, .035),  # Sanchez Mountains
    (.475, .420, .030, .080),  # Griffonstone
    (.535, .490, .035, .025))  # Zebrica's western shore


def _expanded():
    return _option(ATLAS_WORLD) == EXPANDED_WORLD


def _coast_rows(shores):
    # Slice every shore table once into rows[r] = [(west, east), ...], the land
    # spans at latitude (r + .5) / _X_COAST_ROWS. Testing a plot is then a
    # short list scan, however many tables and triples describe the world.
    rows = [[] for row in xrange(_X_COAST_ROWS)]
    for shore in shores:
        for i in range(1, len(shore)):
            upper, old_left, old_right = shore[i - 1]
            lower, left, right = shore[i]
            first = int(upper * _X_COAST_ROWS + .5)
            last = int(lower * _X_COAST_ROWS + .5)
            for row in xrange(max(first, 0), min(last, _X_COAST_ROWS)):
                t = ((row + .5) / _X_COAST_ROWS - upper) / (lower - upper)
                rows[row].append((old_left + (left - old_left) * t,
                                  old_right + (right - old_right) * t))
    return rows


def _on_land(rows, x, v):
    # Rows are clamped, so a landmass that touches the frame runs off the map
    # instead of gaining a sliver of sea when the coast is shifted.
    row = int(v * _X_COAST_ROWS)
    if v < 0.0:
        row = 0
    elif row >= _X_COAST_ROWS:
        row = _X_COAST_ROWS - 1
    for west, east in rows[row]:
        if west <= x <= east:
            return True
    return False


def _shore(rows, x, v, sea_shift):
    # The Known World insets each shore table. Here tables overlap, and an
    # inset would open cracks along their seams, so sea level instead tests
    # four neighbouring points as well. A high sea keeps a plot dry only if
    # all five samples are dry; a low sea makes it dry if any one is.
    if sea_shift == 0.0:
        return _on_land(rows, x, v)
    reach = abs(sea_shift)
    low_sea = sea_shift < 0.0
    for dx, dv in ((0.0, 0.0), (reach, 0.0), (-reach, 0.0),
                   (0.0, reach * _X_ASPECT), (0.0, -reach * _X_ASPECT)):
        if _on_land(rows, x + dx, v + dv) == low_sea:
            return low_sea
    return not low_sea


def _sea_rooms():
    # Prepare _X_SEA_ROOM for the plot loops. Everything here is measured in
    # "ground" units, (x, v / _X_ASPECT), in which a plot is square, so that a
    # distance means the same number of plots in every direction. Each room is
    # (extra, rigid, fade, the two ends of its line, buckets): the buckets
    # sort the line's segments into a coarse grid, so that a plot far from
    # every line costs one dictionary lookup per room and a plot near one
    # measures only the few segments around it.
    rooms = []
    for extra, rigid, fade, line in _X_SEA_ROOM:
        if extra <= 0.0:
            continue
        buckets = {}
        reach = fade + .05
        for i in range(1, len(line)):
            ax, ag = line[i - 1][0], line[i - 1][1] / _X_ASPECT
            dx, dg = line[i][0] - ax, line[i][1] / _X_ASPECT - ag
            segment = (ax, ag, dx, dg, dx * dx + dg * dg)
            for col in range(int((min(ax, ax + dx) - reach) * 20) - 1,
                             int((max(ax, ax + dx) + reach) * 20) + 2):
                for row in range(int((min(ag, ag + dg) - reach) * 20) - 1,
                                 int((max(ag, ag + dg) + reach) * 20) + 2):
                    buckets.setdefault((col, row), []).append(segment)
        ends = (line[0][0], line[0][1] / _X_ASPECT, line[-1][0], line[-1][1] / _X_ASPECT)
        rooms.append((extra, rigid, fade, ends, buckets))
    return rooms


def _room_pull(room, x, g):
    # How one room acts on a point: (distance from its line, unit direction
    # away from the line as two numbers, sea to add here). None if the point
    # is out of the room's reach.
    # The direction is not simply "away from the nearest point". On the inside
    # of a bend that would flip abruptly along the bend's bisector and tear
    # the picture there. Every nearby segment votes instead, the nearest ones
    # overwhelmingly, so the direction turns smoothly through a bend and is
    # the perpendicular beside a straight stretch.
    extra, rigid, fade, ends, buckets = room
    segments = buckets.get((int(x * 20), int(g * 20)))
    if segments is None:
        return None
    nearest, pull_x, pull_g = fade * fade, 0.0, 0.0
    for ax, ag, dx, dg, length2 in segments:
        t = max(0.0, min(1.0, ((x - ax) * dx + (g - ag) * dg) / length2))
        ex, eg = x - ax - t * dx, g - ag - t * dg
        distance2 = ex * ex + eg * eg
        if distance2 < nearest:
            nearest = distance2
        weight = max(distance2, .000000000001) ** -3
        pull_x += ex * weight
        pull_g += eg * weight
    if nearest >= fade * fade:
        return None
    distance = nearest ** .5
    # Ease the widening in from each end of the line. A point level with an
    # end is as far from that end as it is from the line, and gets nothing;
    # the farther along the line it lies, the more those two distances differ.
    from_start = ((x - ends[0]) ** 2 + (g - ends[1]) ** 2) ** .5 - distance
    from_end = ((x - ends[2]) ** 2 + (g - ends[3]) ** 2) ** .5 - distance
    extra = extra * max(0.0, min(1.0, from_start / _X_SEA_ROOM_EASE,
                                 from_end / _X_SEA_ROOM_EASE))
    size = (pull_x * pull_x + pull_g * pull_g) ** .5
    if size == 0.0:
        return distance, 0.0, 0.0, extra  # on the line itself
    return distance, pull_x / size, pull_g / size, extra


def _room_to_atlas(room, x, g):
    # One room's step from the map to the picture: None in its strip of new
    # sea. Beside the strip the map shows the picture moved over by `extra`;
    # from `rigid` out to `fade` the move shrinks to nothing, which is where
    # the land is squeezed. The slope of that shrinking is far below 1, so
    # the picture is never folded over.
    pull = _room_pull(room, x, g)
    if pull is None:
        return x, g
    distance, away_x, away_g, extra = pull
    if extra <= 0.0:
        return x, g
    if distance < extra:
        return None
    if distance < room[1]:
        move = extra
    else:
        move = extra * (room[2] - distance) / (room[2] - room[1])
    return x - move * away_x, g - move * away_g


def _to_atlas(rooms, east, south):
    # Which (x, v) of the picture shows at this map position? None means the
    # plot lies in a strip of new sea. The rooms act one after another.
    spot = east, south / _X_ASPECT
    for room in rooms:
        spot = _room_to_atlas(room, spot[0], spot[1])
        if spot is None:
            return None
    return spot[0], spot[1] * _X_ASPECT


def _to_map(rooms, x, v):
    # The reverse of _to_atlas(): where on the map a point of the picture is
    # drawn. Sea lanes, land links and island cores are placed with it, so
    # that they move with the shores they belong to. The rooms are undone in
    # reverse order. A point on a room's own line stays put, in the middle of
    # the new sea, and points within a hair of the line (`pinch`) are spread
    # evenly across the strip, so that a lane which wanders a little off the
    # line it follows is still drawn in one piece.
    g = v / _X_ASPECT
    pinch = .004
    for index in range(len(rooms) - 1, -1, -1):
        room = rooms[index]
        pull = _room_pull(room, x, g)
        if pull is None:
            continue
        distance, away_x, away_g, extra = pull
        if extra <= 0.0:
            continue
        if distance < pinch:
            move = extra * distance / pinch
        elif distance < room[1] - extra:
            move = extra
        else:
            # Solve d - extra * (fade - d) / (fade - rigid) = distance for d.
            slope = extra / (room[2] - room[1])
            move = (distance + slope * room[2]) / (1.0 + slope) - distance
        want_x, want_g = x, g
        x, g = x + move * away_x, g + move * away_g
        if distance >= pinch:
            # Round a bend the direction at the new place differs slightly
            # from the direction at the old one. A few corrections close the gap.
            for attempt in (1, 2, 3, 4):
                back = _room_to_atlas(room, x, g)
                if back is None:
                    break
                x, g = x + want_x - back[0], g + want_g - back[1]
    return x, g * _X_ASPECT


def _trace(cells, path, width, height, orthogonal, rooms):
    # Add every plot that an (x, v) path passes through to the set `cells`,
    # walking plot by plot so that the trail has no gaps even where sea room
    # stretches it. A sea lane (`orthogonal`) must also be continuous edge to
    # edge: where two of its water plots met only at a corner, land units
    # could still step diagonally across it, so a lane never steps diagonally.
    last = None
    for i in range(1, len(path)):
        ax, av = path[i - 1]
        bx, bv = path[i]
        steps = int(4 * max(abs(bx - ax) * width, abs(bv - av) * height)) + 1
        for step in range(steps + 1):
            t = step / float(steps)
            mx, mv = _to_map(rooms, ax + (bx - ax) * t, av + (bv - av) * t)
            x = max(0, min(width - 1, int(mx * width)))
            y = max(0, min(height - 1, int((1.0 - mv) * height)))
            while last is not None and last != (x, y):
                lx, ly = last
                east_west = lx != x and (ly == y or abs(x - lx) >= abs(y - ly))
                if lx < x and (east_west or not orthogonal):
                    lx += 1
                elif lx > x and (east_west or not orthogonal):
                    lx -= 1
                if ly < y and not (east_west and orthogonal):
                    ly += 1
                elif ly > y and not (east_west and orthogonal):
                    ly -= 1
                last = (lx, ly)
                cells.add(last)
            cells.add((x, y))
            last = (x, y)


def _fixed_plots(width, height, rooms):
    # Plots decided before any shore table is consulted, so that the same seas
    # divide and the same necks join at every map size: (channels, causeways).
    channels, causeways = set(), set()
    for path in _X_STRAITS:
        _trace(channels, path, width, height, True, rooms)
    for path in _X_LAND_LINKS:
        _trace(causeways, path, width, height, False, rooms)
    for causeway, channel in _X_BRIDGES:
        if EXPANDED_BRIDGES_ARE_LAND:
            _trace(causeways, causeway, width, height, False, rooms)
        else:
            _trace(channels, channel, width, height, True, rooms)
    return channels, causeways


def _expanded_ridges():
    # _ridge_segments() for the wide picture. Latitudes are divided by the
    # aspect so that a range is as broad north-south as it is east-west, and
    # the segments are sorted into a coarse grid so that each plot measures
    # only the handful of ranges near it.
    buckets = {}
    for radius, strength, path in _X_RANGES:
        for i in range(1, len(path)):
            ax, av = path[i - 1][0], path[i - 1][1] / _X_ASPECT
            bx, bv = path[i][0], path[i][1] / _X_ASPECT
            dx, dv = bx - ax, bv - av
            segment = (ax, av, dx, dv, dx * dx + dv * dv, radius * radius, strength)
            west, east = min(ax, bx) - radius, max(ax, bx) + radius
            north, south = min(av, bv) - radius, max(av, bv) + radius
            for col in range(int(west * 24), int(east * 24) + 1):
                for row in range(int(north * 24), int(south * 24) + 1):
                    buckets.setdefault((col, row), []).append(segment)
    return buckets


def _expanded_crest(buckets, x, v):
    v = v / _X_ASPECT
    best = 0.0
    for ax, av, dx, dv, length2, radius2, strength in buckets.get((int(x * 24), int(v * 24)), ()):
        t = max(0.0, min(1.0, ((x - ax) * dx + (v - av) * dv) / length2))
        ex, ev = x - ax - t * dx, v - av - t * dv
        best = max(best, strength * (1.0 - (ex * ex + ev * ev) / radius2))
    return best


def _expanded_plot_types(width, height, variation, sea_shift):
    # Each plot is decided in this order:
    #   1. causeways and sea lanes, which are the same at every map size;
    #   2. sea room: plots in a strip of new sea are water, and every other
    #      plot learns which point of the picture it shows (`home`, `here`);
    #   3. the shore tables, read at that position nudged by seeded noise, so
    #      that a whole bay or cape shifts together from game to game;
    #   4. small isles, then lakes;
    #   5. relief: the nearest range's crest, rolling uplands, and one die;
    #   6. last of all, a Rocky climate thickens the ranges (_uplift).
    warp_x = _noise_grid(30, 21, "Equus expanded coast east-west")
    warp_v = _noise_grid(31, 20, "Equus expanded coast north-south")
    uplands = _noise_grid(43, 29, "Equus expanded rolling uplands")
    dice = gc.getGame().getMapRand()
    coast = _coast_rows(_X_SHORES)
    ridges = _expanded_ridges()
    rooms = _sea_rooms()
    channels, causeways = _fixed_plots(width, height, rooms)
    cores = set()
    for cx, cv in _X_CORES + tuple([isle[:2] for isle in _X_ISLES]):
        cx, cv = _to_map(rooms, cx, cv)
        cores.add((int(cx * width), int((1.0 - cv) * height)))
    climate = _Climate()
    level = set(causeways)  # ground that the Rocky climate may not raise
    # This picture holds a whole world where the Known World's holds one
    # continent, so a coast wanders about half as far across it: a little over
    # one plot on a Huge map. v moves farther in fractions to match x on the
    # ground, the picture being wider than it is tall.
    reach_x = .010 * variation
    reach_v = reach_x * _X_ASPECT
    plots = []
    for y in range(height):
        south = 1.0 - (y + 0.5) / height
        for x in range(width):
            east = (x + 0.5) / width
            if (x, y) in causeways:
                plots.append(PlotTypes.PLOT_LAND)  # level ground: never a peak
                continue
            spot = _to_atlas(rooms, east, south)
            if (x, y) in channels or spot is None:
                plots.append(PlotTypes.PLOT_OCEAN)
                continue
            home, here = spot
            atlas_x = home + reach_x * _noise(warp_x, east, south)
            atlas_v = here + reach_v * _noise(warp_v, east, south)
            land = (x, y) in cores or _shore(coast, atlas_x, atlas_v, sea_shift)
            if not land:
                # As in the Known World: small islands move half as far as
                # the mainland and never shrink below most of one plot.
                for cx, cv, rx, rv in _X_ISLES:
                    rx = max(rx - sea_shift * .30, .75 / width)
                    rv = max(rv - sea_shift * .30 * _X_ASPECT, .75 / height)
                    if _in_oval((home + atlas_x) * .5, (here + atlas_v) * .5, cx, cv, rx, rv):
                        land = True
                        break
            if land and (x, y) not in cores and _in_biome(atlas_x, atlas_v, _X_LAKES):
                land = False
            if not land:
                plots.append(PlotTypes.PLOT_OCEAN)
                continue
            if _in_biome(home, here, _X_BASINS):
                plots.append(PlotTypes.PLOT_LAND)
                level.add((x, y))
                continue
            crest = _expanded_crest(ridges, atlas_x, atlas_v)
            if _in_biome(atlas_x, atlas_v, _X_PASSES):
                crest = min(crest, .38)
                level.add((x, y))
            local = _noise(uplands, east, south)
            relief = crest + .22 * local + (.10 + .08 * variation) * (
                dice.get(201, "Equus expanded relief") / 100.0 - 1.0)
            if relief > .84:
                plots.append(PlotTypes.PLOT_PEAK)
            elif relief > .22:
                plots.append(PlotTypes.PLOT_HILLS)
            else:
                plots.append(PlotTypes.PLOT_LAND)
    if climate.hills or climate.peaks:
        _uplift(plots, width, height, climate, level, "Equus expanded uplift")
    return plots


def _expanded_land_terrain(east, south, patch, peak, climate, biomes):
    # `climate` moves the frost lines below and `biomes` holds the ovals as
    # that climate leaves them; under Temperate both are the picture as drawn.
    if _in_biome(east, south, _X_HAVENS) and not peak:
        return 'GRASS'  # the Crystal Heart keeps its valley green in any age
    cold = _in_biome(east, south, biomes.tundra)
    # Both ends of this world are frozen: the top edge, and Agarica with its
    # ice in the far south. (Equestria's own southern cape and Mount Aris
    # reach nearly as far south, hence the eastings.)
    if (south < .030 + climate.snow or
            (south > .885 - climate.snow and east > .540) or
            (south > .940 - climate.snow and east > .300)):
        if cold and not peak:
            return 'TUNDRA'  # Agarica Forest: forests cannot grow on snow
        return 'SNOW'
    if _in_biome(east, south, biomes.snow):
        return 'SNOW'
    # ... or the Yak Range and Mt. Everhoof
    if cold or (south < .125 + climate.tundra and east < .460):
        if peak or patch > .45:
            return 'SNOW'
        return 'TUNDRA'
    if _in_biome(east, south, biomes.dry):
        if patch < -0.57:
            return 'PLAINS'
        return 'DESERT'
    if _in_biome(east, south, biomes.wet) or _in_biome(east, south, _X_GRASSY_LOWLANDS):
        return 'GRASS'
    if _in_biome(east, south, _X_STEPPES):
        if patch > .55:
            return 'GRASS'
        return 'PLAINS'
    if _in_biome(east, south, biomes.scorched):
        return 'PLAINS'
    # As in the Known World, Equestria cools again beyond the Bone Dry Desert.
    if south > .860 - climate.tundra and east < .260:
        if patch < -0.18:
            return 'TUNDRA'
        return 'PLAINS'
    if patch < climate.plains:
        return 'PLAINS'
    return 'GRASS'


def _expanded_terrain_types():
    m = CyMap()
    width, height = m.getGridWidth(), m.getGridHeight()
    terrain = {}
    for key in ('GRASS', 'PLAINS', 'DESERT', 'TUNDRA', 'SNOW'):
        terrain[key] = gc.getInfoTypeForString('TERRAIN_' + key)
    drift_x = _noise_grid(20, 14, 'Equus expanded biome east drift')
    drift_y = _noise_grid(20, 14, 'Equus expanded biome south drift')
    patches = _noise_grid(41, 28, 'Equus expanded ground cover')
    amplitude = 0.010 * _variation()
    rooms = _sea_rooms()
    climate = _Climate()
    biomes = _Biomes(climate, _X_ASPECT, _X_SNOWFIELDS, _X_TUNDRA,
                     _X_DRY_BASINS, _X_WET_WOODS)
    result = []
    for y in range(height):
        south = 1.0 - (y + 0.5) / height
        for x in range(width):
            plot = m.plot(x, y)
            if plot.isWater():
                result.append(plot.getTerrainType())  # Keep shallow/deep water from the DLL.
                continue
            east = (x + 0.5) / width
            spot = _to_atlas(rooms, east, south)
            if spot is None:
                spot = east, south  # a causeway laid across new sea
            u = spot[0] + amplitude * _noise(drift_x, east, south)
            v = spot[1] + amplitude * _X_ASPECT * _noise(drift_y, east, south)
            key = _expanded_land_terrain(u, v, _noise(patches, east, south),
                                         plot.isPeak(), climate, biomes)
            result.append(terrain[key])
    return result


def _floe_line(east):
    # Latitude at which the Great Iceberg Barrier begins, from west to east.
    # West of the Storm King's Realm the South Luna Ocean stays open.
    if east < .170:
        return .990
    if east < .330:
        return .945
    if east < .500:
        return .905
    if east < .680:
        return .885
    return .845


class ExpandedFeatureGenerator(AtlasFeatureGenerator):
    # The Expanded tables under any climate. The inherited getLatitudeAtPlot()
    # still hands each method the plot's distance from the top of the map.
    def __init__(self):
        AtlasFeatureGenerator.__init__(self)
        self.rooms = _sea_rooms()
        self.lanes = _fixed_plots(self.iGridW, self.iGridH, self.rooms)[0]
        self.wet = _grown(_X_WET_WOODS, self.climate.jungle, _X_ASPECT)
        self.woods = _X_WOODLANDS
        self.asked = self.found = None

    def spot(self, x, y, south):
        # The point of the picture at this plot, as the plot and terrain
        # passes saw it. The jungle and forest methods both ask about each
        # plot, one straight after the other, so the last answer is kept.
        if self.asked != (x, y):
            east = (x + 0.5) / self.iGridW
            self.asked = (x, y)
            self.found = _to_atlas(self.rooms, east, south)
            if self.found is None:
                self.found = east, south
        return self.found

    def addIceAtPlot(self, plot, x, y, south):
        if not plot.isWater() or plot.isLake() or (x, y) in self.lanes:
            return
        # A cold climate brings both ice fronts toward the middle of the map
        # by its reach; the sea lanes stay open even then.
        reach = self.climate.ice
        if south < .040 + reach:
            # the Frozen North's pack ice
            chance = min(90, int(90 - 2250 * (south - reach)))
        else:
            line = _floe_line((x + 0.5) / self.iGridW) - reach
            if south < line:
                return
            chance = int(20 + 300 * (south - line))
        if chance > 0 and plot.canHaveFeature(self.featureIce):
            if self.mapRand.get(100, 'Equus expanded pack ice') < chance:
                plot.setFeatureType(self.featureIce, -1)
# XANA 2026-11-22 END: Equestria "Expanded" (Alternative Universe Expansions).
