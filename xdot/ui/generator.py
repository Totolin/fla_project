dotcode = """
digraph finite_state_machine {
	rankdir=LR;
	size="8,5"
	node [shape = doublecircle]; LR_0 LR_3 LR_4 LR_8;
	node [shape = circle];
	LR_0 -> LR_2 [ label = "SS(B)" ];
	LR_0 -> LR_1 [ label = "SS(S)" ];
	LR_1 -> LR_3 [ label = "S($end)" ];
	LR_2 -> LR_6 [ label = "SS(b)" ];
	LR_2 -> LR_5 [ label = "SS(a)" ];
	LR_2 -> LR_4 [ label = "S(A)" ];
	LR_5 -> LR_7 [ label = "S(b)" ];
	LR_5 -> LR_5 [ label = "S(a)" ];
	LR_6 -> LR_6 [ label = "S(b)" ];
	LR_6 -> LR_5 [ label = "S(a)" ];
	LR_7 -> LR_8 [ label = "S(b)" ];
	LR_7 -> LR_5 [ label = "S(a)" ];
	LR_8 -> LR_6 [ label = "S(b)" ];
	LR_8 -> LR_5 [ label = "S(a)" ];
}
"""


class Generator:
    """
    Class that generates dotcode from a dict graph
    """

    def __init__(self):
        # Create an empty graph to start with
        self.graph = {
            "nodes": {
                "single": [],
                "double": [],
                "start": None
            },
            "edges": []
        }

    def get_graph(self):
        return self.graph

    def set_graph(self, gr):
        self.graph = gr

    def add_node(self, node_name, double=False):
        self.graph['nodes']['double' if double else 'single'].append(node_name)

    def add_edge(self, node_from, node_to, edge_value):
        self.graph['edges'].append({
            "from": node_from,
            "to": node_to,
            "value": edge_value
        })

    def delete_node(self, node_name):
        self.graph['nodes']['single'] = list(filter(lambda x: x != node_name, self.graph['nodes']['single']))
        self.graph['nodes']['double'] = list(filter(lambda x: x != node_name, self.graph['nodes']['double']))
        if self.graph['nodes']['start'] == node_name:
            self.graph['nodes']['start'] = None
        self.graph['edges'] = list(
            filter(lambda x: x['from'] != node_name and x['to'] != node_name, self.graph['edges']))

    def delete_edge(self, node_from, node_to):
        self.graph['edges'] = list(
            filter(lambda x: not (x['from'] == node_from and x['to'] == node_to), self.graph['edges'])
        )

    def calculate_start(self):
        # Start with no starting node
        start = None

        # Create a list of all nodes
        nodes = list(self.graph['nodes']['single'] + self.graph['nodes']['double'])

        # Also add current starting node to the list
        if self.graph['nodes']['start']:
            nodes = [self.graph['nodes']['start']] + nodes

        for edge in self.graph['edges']:
            name = edge['to']
            if name in nodes and name != edge['from']:
                nodes.remove(name)

        if nodes:
            start = nodes[0]

        if start:
            # We found a starting node
            self.graph['nodes']['start'] = start

            # Remove it from other lists
            if start in self.graph['nodes']['single']:
                self.graph['nodes']['single'].remove(start)
            if start in self.graph['nodes']['double']:
                self.graph['nodes']['double'].remove(start)

    def check_string(self, query):
        current_state = self.graph['nodes']['start']
        edges = self.graph['edges']

        if not current_state:
            return False

        for ch in query:
            found = False
            for edge in list(filter(lambda x: x['from'] == current_state, edges)):
                if ch in self.get_values_from_edge(edge):
                    current_state = edge['to']
                    found = True

            if not found:
                return False

        if current_state in self.graph['nodes']['double']:
            return True

        return False

    def get_values_from_edge(self, edge):
        # Remove all spaces from value
        values_string = "".join(edge['value'].split())

        # Return array of values
        return values_string.split(',')

    def is_empty(self):
        return not self.graph['nodes']['start']

    def is_deterministic(self):
        all_nodes = list([self.graph['nodes']['start']] + \
                         self.graph['nodes']['single'] + \
                         self.graph['nodes']['double'])

        for node in all_nodes:
            # Get all edges from this node
            out_edges = [edge for edge in self.graph['edges'] if edge['from'] == node]

            # Get all values from edges
            edge_values = []
            for edge in out_edges:
                edge_values += self.get_values_from_edge(edge)

            if len(edge_values) != len(set(edge_values)):
                # Duplicates found
                return False

        return True

    def get_dotcode(self):

        # Calculate starting node
        self.calculate_start()

        # Set all default properties of the graph
        base = """ """
        base += "digraph finite_state_machine {\n"
        base += "\trankdir=LR;\n"
        base += "\tsize=\"8,5\"\n"

        # Create a string with all double circle nodes
        double_nodes = ''
        for node in self.graph['nodes']['double']:
            double_nodes += node + ' '
        double_nodes = double_nodes[:-1]

        # Create a string with all single circle nodes
        single_nodes = ''
        for node in self.graph['nodes']['single']:
            single_nodes += node + ' '
        single_nodes = single_nodes[:-1]

        # Add doubles and singles to the base string
        if self.graph['nodes']['start']:
            base += "\tnode [shape = Mcircle]; %s;\n" % self.graph['nodes']['start']

        if double_nodes:
            base += "\tnode [shape = doublecircle]; %s;\n" % double_nodes

        if single_nodes:
            base += "\tnode [shape = circle]; %s;\n" % single_nodes

        # Add all edges to the graph string
        for edge in self.graph['edges']:
            base += "\n\t%s -> %s [ label = \"%s\" ]" % (edge['from'], edge['to'], edge['value'])

        base += "\n}"

        return base
