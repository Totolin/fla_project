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

    def add_edge(self, node_from, node_to, node_value):
        self.graph['edges'].append({
            "from": node_from,
            "to": node_to,
            "value": node_value
        })

    def delete_node(self, node_name):
        print(node_name)
        self.graph['nodes']['single'] = list(filter(lambda x: x != node_name, self.graph['nodes']['single']))
        self.graph['nodes']['double'] = list(filter(lambda x: x != node_name, self.graph['nodes']['double']))
        if self.graph['nodes']['start'] == node_name:
            self.graph['nodes']['start'] = None
        self.graph['edges'] = list(filter(lambda x: x['from'] != node_name and x['to'] != node_name, self.graph['edges']))


    def get_dotcode(self):

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

        # Add them to the base string
        if double_nodes:
            base += "\tnode [shape = doublecircle]; %s;\n" % double_nodes

        if single_nodes:
            base += "\tnode [shape = circle]; %s;\n" % single_nodes

        # Add all edges to the graph string
        for edge in self.graph['edges']:
            base += "\n\t%s -> %s [ label = \"%s\" ]" % (edge['from'], edge['to'], edge['value'])

        base += "\n}"

        return base
