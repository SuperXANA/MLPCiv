#!/usr/bin/env python3
"""Print an Equus map as text, without launching Civilization IV.

    python3 tests/preview_equus.py --world 1 --size 5 --seed 7 --climate 4

It runs PrivateMaps/Equus.py against the stand-ins in tests/check_equus.py, so
coasts, relief and terrain are what the script computes. Forests and jungles
are only indicative: the game draws them from its own fractals, the harness
from a simple pattern. Use it to see what an edit to the atlas tables does.

    world      0 Equestria "Known World", 1 Equestria "Expanded"
    size       0 Duel ... 5 Huge, 6 XXL
    variation  0 Subtle, 1 Standard, 2 Lively
    sea        0 low, 1 normal, 2 high
    climate    0 Temperate, 1 Tropical, 2 Arid, 3 Rocky, 4 Cold (stock XML values)
    straits    draw the Expanded world's two bridges as straits

Legend: blank sea, ~ pack ice, . grass, , plains, : desert, - tundra, * snow,
        n hills, ^ peak, f forest, j jungle
"""
import argparse

import check_equus as harness

GROUND = {10: ".", 11: ",", 12: ":", 13: "-", 14: "*"}
FEATURES = {30: "~", 31: "j", 32: "f"}


def preview(world, size, variation, sea, seed, straits, climate=0):
    def tweak(module):
        if straits:
            module.EXPANDED_BRIDGES_ARE_LAND = False
    options = (0, variation, world)
    cells = harness.cells_for(size, options)
    width, height = cells[0] * 4, cells[1] * 4
    plots, terrains, features = harness.generate(
        harness.INSTALLED, size, options, sea, seed, tweak=tweak, climate=climate)[:3]
    lines = []
    for y in range(height - 1, -1, -1):  # Civ's y runs north: print the top row first
        line = ""
        for x in range(width):
            index = y * width + x
            if features[index] in FEATURES:
                line += FEATURES[features[index]]
            elif plots[index] == 0:
                line += " "
            elif plots[index] == 3:
                line += "^"
            elif plots[index] == 2:
                line += "n"
            else:
                line += GROUND[terrains[index]]
        lines.append(line.rstrip())
    land = sum(1 for plot in plots if plot)
    summary = "%d x %d plots, %d%% land, %d peaks, %d hills" % (
        width, height, 100 * land // len(plots), plots.count(3), plots.count(2))
    return "\n".join(lines), summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--world", type=int, default=1, choices=(0, 1))
    parser.add_argument("--size", type=int, default=3, choices=range(7))
    parser.add_argument("--variation", type=int, default=1, choices=(0, 1, 2))
    parser.add_argument("--sea", type=int, default=1, choices=(0, 1, 2))
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--straits", action="store_true")
    parser.add_argument("--climate", type=int, default=0, choices=range(5))
    args = parser.parse_args()
    picture, summary = preview(args.world, args.size, args.variation, args.sea,
                               args.seed, args.straits, args.climate)
    print(picture)
    print(summary)


if __name__ == "__main__":
    main()
