# Copyright (c) 2024, Nathan Hansen
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from rpack import pack, packing_density, PackingImpossibleError
from itertools import product


def unique_rotation_combinations(shape, N):
    # !!--Assumes that all sizes are the same--!!
    # Given N shapes of the format (w, h)
    # Find all unique combinations of rotations (w, h) -> (h, w)
    # N sizes -> N+1 combinations
    # If represented in binary with 3 sizes:
    # [1, 1, 1], [1, 1, 0], [1, 0, 0], [0, 0, 0]
    revshape = (shape[1], shape[0])
    output = []
    for i in range(N):
        output.append([shape] * i + [revshape] * max(0, (N - i)))
    output.append([shape] * N)
    return output


def unique_keep_combinations(shape, N):
    # !!--Assumes that all sizes are the same--!!
    # Given N shapes of the format (w, h)
    # Find all unique combinations of keep/ignore
    # N sizes -> N+1 combinations
    # If represented in binary with 3 sizes:
    # [1, 1, 1], [1, 1, 0], [1, 0, 0], [0, 0, 0]
    return [[shape] * i for i in range(N + 1)]


def find_rotations(sizes, verbose=False):
    # Given an arbitrary list of 2-tuples:
    # [(w1, h1), (w2, h2), ...]
    # Finds all *unique* combinations of rotations:
    # [[(w1, h1), (w2, h2), ...],
    #  [(h1, w1), (w2, h2), ...],
    #  [(h1, w1), (h2, w2), ...],
    #  ...]
    # Output will be between 1 and 2^N lists of N sizes

    for s in sizes:
        if not isinstance(s, tuple) or len(s) != 2:
            raise TypeError("All sizes must be 2-tuples")

    # Find unique symmetric and non-symmetric shapes
    rotatable = {}
    symmetric = {}
    for s in sizes:
        tmp = s if s[0] < s[1] else (s[1], s[0])

        if s[0] == s[1]:
            try:
                symmetric[tmp] += 1
            except KeyError:
                symmetric[tmp] = 1
        else:
            try:
                rotatable[tmp] += 1
            except KeyError:
                rotatable[tmp] = 1

    # Get combinations of non-symmetric shape rotations
    tmp = []
    for s, c in rotatable.items():
        tmp.append(unique_rotation_combinations(s, c))

    # Symmetric shapes
    prepend = []
    for s, c in symmetric.items():
        prepend.extend([s] * c)

    # Get all combinations of combinations and flatten
    output = []
    for values in product(*tmp):
        sz = [*prepend]
        for v in values:
            if isinstance(v, list):
                sz.extend(v)
            else:
                sz.append(v)
        output.append(sz)

    if verbose:
        print(f"Found {len(output)} unique rotation sets of {len(sizes)} items")

    return output


def find_optimal_packing(sizes, max_width, max_height, verbose=False):
    # Given a list of rectangles represented by 2-tuples of
    # the format [(w, h), (w, h), ...] find the optimal
    # packing within the given max width and height
    rot_combs = find_rotations(sizes)

    best_density = None
    best_sizes = None
    best_positions = None
    for c in rot_combs:
        try:
            positions = pack(c, max_width, max_height)
        except PackingImpossibleError:
            # Can't fit the desired shapes within the limits
            continue

        # Assume the best solution has the highest density
        density = packing_density(c, positions)
        if best_density is None or density > best_density:
            best_density = density
            best_sizes = c
            best_positions = positions

    if best_density is None:
        if verbose:
            print("No solution found within max width and height!")
        return None, None
    else:
        if verbose:
            print(f"Best Density: {best_density:.1%}")
        return best_sizes, best_positions


def find_sorted_areas(sizes, area, threshold=0.9, verbose=False):
    # Given a list of rectangles represented by 2-tuples of
    # the format [(w, h), (w, h), ...] find which combinations
    # fit within a given area, then sort by total area of shapes.
    # If threshold is not None, then it represents the minimum %
    # of the given area that the shapes must cover to be valid.

    uniques = {}
    for s in sizes:
        tmp = s if s[0] < s[1] else (s[1], s[0])
        try:
            uniques[tmp] += 1
        except KeyError:
            uniques[tmp] = 1

    tmp = []
    for k, c in uniques.items():
        tmp.append(unique_keep_combinations(k, c))

    combs = []
    for values in list(product(*tmp)):
        sz = []
        for v in values:
            if isinstance(v, list):
                sz.extend(v)
            else:
                sz.append(v)
        if len(sz) > 0:
            combs.append(sz)

    output = []
    for c in combs:
        a = sum([t[0] * t[1] for t in c])
        if a > 0 and a <= area and (threshold is None or a >= threshold * area):
            output.append([c, a])

    output.sort(key=lambda x: x[1], reverse=True)

    if verbose:
        print(
            f"Found {len(output)} unique sets of {len(sizes)} items within given area"
        )

    # sizes, areas
    return [v[0] for v in output], [v[1] for v in output]


def find_max_usage(sizes, width, height, threshold=0.9, verbose=False):
    # Given a list of rectangles represented by 2-tuples of
    # the format [(w, h), (w, h), ...] find the optimal combination
    # and placements to use as much area within the width and height as possible.
    # Threshold specifies the minimum % of area that must be used

    size_sets, areas = find_sorted_areas(
        sizes, width * height, threshold, verbose=False
    )

    N = len(size_sets)
    if verbose:
        print(f"Found {N} sets of shapes that fit within given area")

    for i, sset in enumerate(size_sets):
        if verbose:
            print(f"> Trying set {i+1} of {N}...")
        best_sizes, best_positions = find_optimal_packing(sset, width, height)

        # Since we're evaluating in descending order of area used, the first valid solution is the best
        if best_sizes is not None:
            if verbose:
                print(
                    f"Best Area Usage: {areas[i]} of {width*height} ({areas[i]/(width*height):.1%})"
                )
            return best_sizes, best_positions
        # print("No solutions")

    if verbose:
        print("No solutions found!")
    return None, None


def multi_sheet_packing(sizes, width, height, verbose=True):
    remaining_sizes = [*sizes]
    sheets = []
    while len(remaining_sizes) > 0:
        located_sizes, positions = find_max_usage(remaining_sizes, width, height, None)
        if located_sizes is None:
            break
        sheets.append([located_sizes, positions])
        for s in located_sizes:
            if s in remaining_sizes:
                remaining_sizes.remove(s)
            elif (s[1], s[0]) in remaining_sizes:
                remaining_sizes.remove((s[1], s[0]))

    if verbose:
        items = sum([len(s[0]) for s in sheets])
        print(f"Fit {items} items on {len(sheets)} sheets")

    return sheets


def plot_text(axs, sizes, positions):
    for i, p in enumerate(positions):
        cx = p[0] + sizes[i][0] / 2
        cy = p[1] + sizes[i][1] / 2
        if sizes[i][0] < sizes[i][1]:
            axs.text(
                cx,
                cy,
                str(sizes[i]),
                rotation="vertical",
                rotation_mode="anchor",
                horizontalalignment="center",
                verticalalignment="center",
            )
        else:
            axs.text(
                cx,
                cy,
                str(sizes[i]),
                rotation_mode="anchor",
                horizontalalignment="center",
                verticalalignment="center",
            )


def plot_positions(sizes, positions, max_width, max_height, show_sizes=True):
    # Given a list of rectangles represented by 2-tuples of
    # the format [(w, h), (w, h), ...] and their positions
    # represented by 2-tuples of [(x, y), (x, y), ...]
    # plot the shapes

    fig, ax = plt.subplots()
    axs = fig.axes

    axs[0].add_collection(
        PatchCollection(
            [Rectangle((0, 0), max_width, max_height)], ec="k", fc=(0.9, 0.9, 0.9, 1)
        )
    )

    rects = []
    for i, p in enumerate(positions):
        rects.append(Rectangle(p, *sizes[i]))
        if show_sizes:
            plot_text(plt, sizes, positions)
    axs[0].add_collection(PatchCollection(rects, alpha=1, ec="k", fc="white"))

    axs[0].set_ylim(-1, max_height + 1)
    axs[0].set_xlim(-1, max_width + 1)

    axs[0].set_aspect("equal")

    plt.box(False)

    plt.show()


def multi_plot_positions(sheets, max_width, max_height, show_sizes=True):
    # Given a list of sheets containing rectangles represented by 2-tuples of
    # the format [(w, h), (w, h), ...] and their positions
    # represented by 2-tuples of [(x, y), (x, y), ...]
    # plot the shapes

    transpose = max_width <= max_height

    N = len(sheets)
    if transpose:
        fig, ax = plt.subplots(1, N, sharey=True)
    else:
        fig, ax = plt.subplots(N, 1, sharex=True)
    axs = fig.axes
    plt.tight_layout(pad=0)

    for i in range(N):
        axs[i].add_collection(
            PatchCollection(
                [Rectangle((0, 0), max_width, max_height)],
                ec="k",
                fc=(0.9, 0.9, 0.9, 1),
            )
        )

    for j, (sizes, positions) in enumerate(sheets):
        rects = []
        for i, p in enumerate(positions):
            rects.append(Rectangle(p, *sizes[i]))
            if show_sizes:
                plot_text(axs[j], sizes, positions)
        axs[j].add_collection(PatchCollection(rects, alpha=1, ec="k", fc="white"))

        axs[j].set_ylim(0, max_height)
        axs[j].set_xlim(0, max_width)
        axs[j].set_aspect("equal")
        axs[j].set_frame_on(False)

    plt.show()


if __name__ == "__main__":
    # from random import randint

    # sizes = []
    # for _ in range(10):
    #     sizes.append((randint(2, 30), randint(2, 30)))

    # sizes = [(4, 3), (4, 3), (2, 2), (2, 2), (3, 1), (8, 7), (7, 8), (2, 10)]
    # sizes = [(13, 39)] * 18

    sizes = [(3, 30)] * 30

    stock_width = 50
    stock_height = 50

    # packed_sizes, positions = find_max_usage(sizes, stock_width, stock_height, None)

    sheets = multi_sheet_packing(sizes, stock_width, stock_height)

    # packed_sizes, positions = find_optimal_packing(sizes, stock_width, stock_height)

    if len(sheets) > 0:
        multi_plot_positions(sheets, stock_width, stock_height)

    # for packed_sizes, positions in sheets:
    #     if packed_sizes is not None:
    #         plot_positions(packed_sizes, positions, stock_width, stock_height)
