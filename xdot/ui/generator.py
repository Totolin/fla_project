test_data = {
    "nodes": [
        "n1", "n2"
    ],
    "edges": [
        {
            "from": "n1",
            "to": "n2"
        }
    ]
}

from .elements import Graph

def generate_graph(data):
    data = test_data
    graph = Graph()