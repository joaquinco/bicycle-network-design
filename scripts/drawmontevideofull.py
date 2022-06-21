import argparse
import os
import sys

from matplotlib import pyplot as plt
import osmnx as ox

import bcnetwork as bc


cache_path = 'instances/montevideo/raw_graph.pkl'


def draw_montevideo_full(fig_path, skip_cache=False):
    if os.path.exists(cache_path) and not skip_cache:
        full_montevideo_graph = bc.persistance.load(cache_path)
    else:
        full_montevideo_graph = ox.graph_from_point(
            (-34.90485576, -56.16071664), dist=12000)
        full_montevideo_graph = bc.persistance.normalize_graph_shape(
            full_montevideo_graph)
        bc.persistance.save(full_montevideo_graph, cache_path)

    mdeofig, mdeoax = plt.subplots(constrained_layout=True)
    bc.draw.draw(
        full_montevideo_graph,
        ax=mdeoax,
        with_labels=False,
        width=0.05,
        node_size=0.0,
        edge_color=bc.colors.gray_dark,
    )
    mdeofig.savefig(fig_path, dpi=300)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fig_path')
    parser.add_argument('--no-cache', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    draw_montevideo_full(args.fig_path, skip_cache=args.no_cache)


main()
