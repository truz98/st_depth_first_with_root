"""
    Algorithm : Constructing a Spanning Tree with a specified root : In depth first
"""
import os
import socket
import threading
import yaml
from typing import List

nodes = []  # Contains all nodes


# This class represent a node
class Node:
    id: int  # Use only to print logs - No use in the algorithm
    parent: 'Node' = None  # Parent
    f: List['Node'] = []  # Set of children
    nf: List['Node'] = []  # Set of non-children
    v: List['Node']  # Set of neighbours
    ne: List['Node']  # Set of neighbours not yet explored
    terminated: bool = False  # Use to stop the algorithm
    address: str  # Address of this node

    def __init__(self, id, address):
        # Add id and address to all nodes
        self.id = id
        self.address = address

    def add_neighbours(self, neighbours):
        # Non-explored neighbours are equals to neighbours at initialization
        self.v = neighbours
        self.ne = neighbours


def create_nodes(data):
    # Create all nodes, without neighbours. Return all nodes
    nodes = []
    for n in data:
        nodes.append(Node(n['id'], n['address']))
    return nodes


def get_node_from_ip(ip):
    # Retrieve node from ip. Return node
    for n in nodes:
        if n.address == ip:
            return n


def receive(node):
    # Wait until a packet is received. Return sender's node and the message received

    # Create socket to receive data
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind((node.address, 8000))
    serversocket.listen(5)

    # Receive data
    (clientsocket, address) = serversocket.accept()

    # Retrieve node source from ip
    node_src = get_node_from_ip(address[0])

    # Get message
    message = clientsocket.recv(2000).decode()

    return node_src, message


def read_files(all_files_path):
    # Read content of all files and return data contained inside each file
    data = []
    for f in all_files_path:
        try:
            # Open and read file
            with open(f) as file:
                yaml_node = yaml.load(file, Loader=yaml.FullLoader)
                data.append(yaml_node)

            # Close file
            file.close()
        except Exception as e:
            print(e)
            exit()
    return data


def root_function(node):
    # Priming method of the root node

    # Set parent, get a neighbour
    node.parent = node
    nk = node.ne.pop(0)

    # Create and send first socket
    message = "M"
    send(message, node, nk)

    # Connect to server
    server(node)


def send(message, node_src, node_dst):
    # Send a packet to another node

    # Create socket, bind and connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((node_src.address, 8000))
    s.connect((node_dst.address, 8000))

    # Send
    print("Node {} ({}) send <{}> to node {} ({})".format(node_src.id, node_src.address, message, node_dst.id,
                                                          node_dst.address))
    s.send(message.encode())

    # Close socket
    s.close()


def server(node):
    # Run until the node has terminated
    while not node.terminated:
        # Waiting for a message
        node_src, message = receive(node)

        match message:
            case "M":
                # M = Adoption request
                if node.parent is None:
                    # No parent = First adoption request received
                    node.parent = node_src
                    node.ne.remove(node_src)
                    if node.ne:
                        # Still non-explored neighbours  --> Ask to be the parent
                        node_dst = node.ne.pop()
                        send('M', node, node_dst)
                    else:
                        # No non-explored neighbours left --> Return to parent
                        send('P', node, node.parent)
                        node.terminated = True
                        print("Node {} has just finished.".format(node.id))
                else:
                    # Already a parent, or it's the root
                    node.ne.remove(node_src)
                    send('R', node, node_src)
                    node.nf.append(node_src)
            case ("R" | "P"):
                match message:
                    case "R":
                        # R = Adoption request rejected
                        node.nf.append(node_src)
                    case "P":
                        # P = Adoption request accepted
                        node.f.append(node_src)
                if node.ne:
                    # Still non-explored neighbours --> Ask to be the parent
                    node_dst = node.ne.pop()
                    send('M', node, node_dst)
                else:
                    # No non-explored neighbours left --> Return to parent
                    if not node.parent == node:
                        # It's not the root -> Send to parent
                        send('P', node, node.parent)
                    node.terminated = True
                    print("Node {} has just finished.".format(node.id))


if __name__ == "__main__":
    # Declare all files path here
    all_files_path = [
        os.path.join("Neighbours", "node-1.yaml"),
        os.path.join("Neighbours", "node-2.yaml"),
        os.path.join("Neighbours", "node-3.yaml"),
        os.path.join("Neighbours", "node-4.yaml"),
        os.path.join("Neighbours", "node-5.yaml"),
        os.path.join("Neighbours", "node-6.yaml"),
        os.path.join("Neighbours", "node-7.yaml"),
        os.path.join("Neighbours", "node-8.yaml"),
    ]
    # Read data from files
    data = read_files(all_files_path)

    # Create nodes
    nodes = create_nodes(data)
    nb_nodes = len(nodes)

    # Add all neighbours
    for i in range(nb_nodes):
        neighbours = data[i]['neighbours']
        nodes_neighbours = []
        for neighbour in neighbours:
            # Id is 1->n and list is 0->n-1
            nodes_neighbours.append(nodes[neighbour['id'] - 1])
        nodes[i].add_neighbours(nodes_neighbours)

    # Start each node in a thread, except root node
    for n in nodes[:-1]:
        x = threading.Thread(target=server, args=(n,))
        x.start()
        print("Node {} has started with ip {}.".format(n.id, n.address))

    # Start root node in another function
    x = threading.Thread(target=root_function, args=(nodes[nb_nodes - 1],))
    x.start()
    print("Node {} has started with ip {}. This is the root node.".format(nodes[nb_nodes - 1].id,
                                                                          nodes[nb_nodes - 1].address))
