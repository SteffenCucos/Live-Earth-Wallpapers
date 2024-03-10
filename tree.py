
class Node:
    def __init__(self, num: int):
        self.num = num
        self.connected: list[Node] = []

    def add_connection(self, node: 'Node'):
        self.connected.append(node)


def print_tree(root: Node, visited=None, level=0):
    if not visited:
        visited = set()

    print(" "*level + str(root.num))
    visited.add(root.num)
    for node in root.connected:
        if not node.num in visited:
            print_tree(node, visited, level + 1)


def getOrCreateNode(nodeMap: dict[int, Node], num: int):
    if num in nodeMap.keys():
        return nodeMap.get(num)
    else:
        node = Node(num)
        nodeMap[num] = node
        return node


def process_tree(edges: list[tuple[int]]):
    nodeMap: dict[int, Node] = {}

    for edge in edges:
        leftNum = edge[0]
        rightNum = edge[1]

        leftNode = getOrCreateNode(nodeMap, leftNum)
        rightNode = getOrCreateNode(nodeMap, rightNum)

        leftNode.add_connection(rightNode)
        rightNode.add_connection(leftNode)

    return nodeMap[1]


if __name__ == "__main__":
    edges1 = [
        [4, 5],
        [5, 3],
        [1, 5],
        [2, 1]
    ]
    root1: Node = process_tree(edges1)
    print("Tree 1")
    print_tree(root1)

    edges2 = [
        [4, 5],
        [5, 3],
        [1, 5],
        [2, 5]
    ]

    root2: Node = process_tree(edges2)
    print("Tree 2")
    print_tree(root2)