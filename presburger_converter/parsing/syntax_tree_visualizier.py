# syntax_tree_visualizer.py

from graphviz import Digraph


def syntax_tree_to_dot(ast, filename="syntax_tree"):
    dot = Digraph(comment='Syntax Tree')
    counter = {"id": 0}

    def add_node(node, parent_id=None):
        node_id = f"node{counter['id']}"
        counter['id'] += 1

        label = type(node).__name__

        # Special label for variables/constants
        if isinstance(node, (Var, Const, Zero, One)):
            label += f"\\n{str(node)}"
        elif isinstance(node, Mult):
            label += f"\\n{node.n} * {node.var}"

        dot.node(node_id, label)

        if parent_id is not None:
            dot.edge(parent_id, node_id)

        # Recurse for children
        if isinstance(node, Add):
            add_node(node.left, node_id)
            add_node(node.right, node_id)
        elif isinstance(node, (LessEqual, Eq, Less, Greater, GreaterEqual, And, Or, Implies, Iff)):
            add_node(node.left, node_id)
            add_node(node.right, node_id)
        elif isinstance(node, Not):
            add_node(node.expr, node_id)
        elif isinstance(node, (Exists, ForAll)):
            # Show variable name specially
            var_node_id = f"node{counter['id']}"
            counter['id'] += 1
            dot.node(var_node_id, f"Var\\n{node.var}")
            dot.edge(node_id, var_node_id)
            add_node(node.formula, node_id)

    add_node(ast)

    #dot.render(filename, format='png', cleanup=True)
    #print(f"Syntax tree rendered to {filename}.png")