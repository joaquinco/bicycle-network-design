from .cache import cached_property
from .persistance import read_graph_from_yaml, read_graph_from_csvs
from .transform import graph_to_mathprog, origin_destination_pairs_to_mathprog


class Model:
    def __init__(
        self,
        graph=None,
        graph_file=None,
        nodes_file=None,
        arcs_file=None,
        budget=None,
        odpairs=None,
        breakpoints=None,
        user_cost_weight='distance'
    ):
        self._graph = graph
        self.graph_file = graph_file,
        self.nodes_file = nodes_file
        self.arcs_file = arcs_file
        self.budget = budget
        self.odpairs = odpairs
        self.breakpoints = breakpoints

    @cached_property
    def graph(self):
        """
        Returns a networkx graph instance
        """
        if self._graph:
            return self._graph
        
        if self.nodes_file and self.arcs_file:
            return read_graph_from_csvs(self.nodes_file, self.arcs_file)

        if self.graph_file:
            return read_graph_from_yaml(self.graph_file)

        raise ValueError('Missing graph, graph_file or nodes_file and arcs_file')

    def write_data(self, output):
        """
        Write model to mathprog
        """
        output.write("data;\n\n")
        graph_to_mathprog(g, f)
        origin_destination_pairs_to_mathprog(
            self.graph,
            self.odpairs,
            self.breakpoints,
            output,
        )
        
        output.write(f"param B := {self.budget};\n")
        output.write("end;\n")
