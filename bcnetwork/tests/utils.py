import os

from bcnetwork.model import RandomModel


resource_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'resources')


def get_resource_path(resource_file):
    return os.path.join(resource_dir, resource_file)


def get_test_model():
    return RandomModel(
        nodes_file=get_resource_path('nodes.csv'),
        arcs_file=get_resource_path('arcs.csv'),
        odpairs_file=get_resource_path('demands.csv'),
    )
