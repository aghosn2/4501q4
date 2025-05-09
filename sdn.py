import networkx as nx
import matplotlib.pyplot as plt
import random
import heapq
from collections import defaultdict
import cmd
import time

# Watermark: A cryptographic signature based on my student ID (897140231)
# SHA-256 hash of "897140231NeoDDaBRgX5a9"
# WATERMARK_HASH: e6aa57822e341ae328b9125c041856fc2eb991e245313441d7748dc54c2cafe4

class Flow:
    def __init__(self, flow_id, src, dst, bandwidth=1, priority=0, is_critical=False):
        self.flow_id = flow_id
        self.src = src
        self.dst = dst
        self.bandwidth = bandwidth
        self.priority = priority
        self.is_critical = is_critical
        self.path = []
        self.backup_path = []

class Link:
    def __init__(self, src, dst, capacity=10, weight=1):
        self.src = src
        self.dst = dst
        self.capacity = capacity
        self.used_capacity = 0
        self.weight = weight
        self.active = True
        self.flows = set()
    
    def utilization(self):
        if self.capacity == 0:
            return 1.0
        return self.used_capacity / self.capacity

class SDNController:
    def __init__(self):
        self.topology = nx.DiGraph()
        self.flows = {}
        self.flow_counter = 0
        self.switch_flow_tables = defaultdict(list)
    
    def add_node(self, node_id, **attrs):
        """Add a node to the network topology."""
        self.topology.add_node(node_id, **attrs)
        return f"Added node {node_id}"
    
    def add_link(self, src, dst, capacity=10, weight=1):
        """Add a bidirectional link between src and dst."""
        if src not in self.topology.nodes or dst not in self.topology.nodes:
            return f"Error: Node {src} or {dst} does not exist"
        
        # Create link objects for both directions
        link1 = Link(src, dst, capacity, weight)
        link2 = Link(dst, src, capacity, weight)
        
        # Add edges with link objects as attributes
        self.topology.add_edge(src, dst, link=link1, weight=weight)
        self.topology.add_edge(dst, src, link=link2, weight=weight)
        
        return f"Added bidirectional link between {src} and {dst}"
    
    def remove_node(self, node_id):
        """Remove a node and all its connected links."""
        if node_id not in self.topology.nodes:
            return f"Error: Node {node_id} does not exist"
        
        # Get affected flows and remove them
        affected_flows = []
        for flow_id, flow in list(self.flows.items()):
            if node_id in flow.path:
                affected_flows.append(flow_id)
                self.remove_flow(flow_id)
        
        self.topology.remove_node(node_id)
        return f"Removed node {node_id} and {len(affected_flows)} affected flows"
    
    def remove_link(self, src, dst):
        """Remove a link and reroute affected flows."""
        if not self.topology.has_edge(src, dst):
            return f"Error: Link from {src} to {dst} does not exist"
        
        # Get the link object
        link = self.topology[src][dst]['link']
        affected_flows = list(link.flows)
        
        # Remove the link
        self.topology.remove_edge(src, dst)
        self.topology.remove_edge(dst, src)
        
        # Reroute affected flows
        for flow_id in affected_flows:
            if flow_id in self.flows:
                flow = self.flows[flow_id]
                self.reroute_flow(flow)
        
        return f"Removed link between {src} and {dst} and rerouted {len(affected_flows)} flows"
    
    def simulate_link_failure(self, src, dst):
        """Simulate a link failure and reroute affected flows."""
        if not self.topology.has_edge(src, dst):
            return f"Error: Link from {src} to {dst} does not exist"
        
        # Get the link objects for both directions
        link1 = self.topology[src][dst]['link']
        link2 = self.topology[dst][src]['link']
        
        # Mark links as inactive
        link1.active = False
        link2.active = False
        
        # Set weight to infinity to avoid using this link in path calculations
        self.topology[src][dst]['weight'] = float('inf')
        self.topology[dst][src]['weight'] = float('inf')
        
        # Get affected flows
        affected_flows = list(link1.flows)
        affected_flows.extend(list(link2.flows))
        affected_flows = set(affected_flows)  # Remove duplicates
        
        # Reroute affected flows
        for flow_id in affected_flows:
            if flow_id in self.flows:
                flow = self.flows[flow_id]
                self.reroute_flow(flow)
        
        return f"Simulated failure of link between {src} and {dst}, rerouted {len(affected_flows)} flows"
    
    def restore_link(self, src, dst):
        """Restore a failed link."""
        if not self.topology.has_edge(src, dst):
            return f"Error: Link from {src} to {dst} does not exist"
        
        # Get the link objects for both directions
        link1 = self.topology[src][dst]['link']
        link2 = self.topology[dst][src]['link']
        
        # Restore original weights
        self.topology[src][dst]['weight'] = link1.weight
        self.topology[dst][src]['weight'] = link2.weight
        
        # Mark links as active
        link1.active = True
        link2.active = True
        
        # Optimization: Reconsider all flows to see if they can be better routed
        self.optimize_all_flows()
        
        return f"Restored link between {src} and {dst} and optimized flows"
    
    def get_active_topology(self):
        """Return a graph with only active links."""
        active_topology = nx.DiGraph()
        active_topology.add_nodes_from(self.topology.nodes(data=True))
        
        for u, v, data in self.topology.edges(data=True):
            if data['link'].active:
                active_topology.add_edge(u, v, weight=data['weight'])
        
        return active_topology
    
    def compute_shortest_path(self, src, dst):
        """Compute the shortest path from src to dst using Dijkstra's algorithm."""
        if src not in self.topology.nodes or dst not in self.topology.nodes:
            return None
        
        active_topology = self.get_active_topology()
        
        try:
            path = nx.shortest_path(active_topology, source=src, target=dst, weight='weight')
            return path
        except nx.NetworkXNoPath:
            return None
    
    def compute_k_shortest_paths(self, src, dst, k=3):
        """Compute k shortest paths from src to dst."""
        if src not in self.topology.nodes or dst not in self.topology.nodes:
            return []
        
        active_topology = self.get_active_topology()
        
        try:
            paths = list(nx.shortest_simple_paths(active_topology, src, dst, weight='weight'))
            return list(paths)[:k]  # Return at most k paths
        except nx.NetworkXNoPath:
            return []
    
    def add_flow(self, src, dst, bandwidth=1, priority=0, is_critical=False):
        """Add a new flow to the network."""
        if src not in self.topology.nodes or dst not in self.topology.nodes:
            return f"Error: Node {src} or {dst} does not exist"
        
        flow_id = self.flow_counter
        self.flow_counter += 1
        
        flow = Flow(flow_id, src, dst, bandwidth, priority, is_critical)
        self.flows[flow_id] = flow
        
        if is_critical:
            # For critical flows, compute both primary and backup paths
            paths = self.compute_k_shortest_paths(src, dst, k=2)
            if len(paths) >= 1:
                flow.path = paths[0]
                if len(paths) >= 2:
                    flow.backup_path = paths[1]
            
                # Update link utilization and flow tables for primary path
                self.install_flow_path(flow, flow.path)
            else:
                return f"Error: No path available from {src} to {dst}"
        else:
            # For regular flows, use load balancing across multiple paths
            paths = self.compute_k_shortest_paths(src, dst, k=3)
            if paths:
                # Simple load balancing - choose the least utilized path
                best_path = self.select_least_utilized_path(paths, bandwidth)
                flow.path = best_path
                
                # Update link utilization and flow tables
                self.install_flow_path(flow, flow.path)
            else:
                return f"Error: No path available from {src} to {dst}"
        
        return f"Added flow {flow_id} from {src} to {dst}"
    
    def select_least_utilized_path(self, paths, bandwidth):
        """Select the path with the least utilization."""
        best_path = None
        best_utilization = float('inf')
        
        for path in paths:
            max_utilization = 0
            valid_path = True
            
            for i in range(len(path) - 1):
                src, dst = path[i], path[i+1]
                link = self.topology[src][dst]['link']
                
                # Check if adding this flow would exceed capacity
                if link.used_capacity + bandwidth > link.capacity:
                    valid_path = False
                    break
                
                current_utilization = link.utilization()
                max_utilization = max(max_utilization, current_utilization)
            
            if valid_path and max_utilization < best_utilization:
                best_utilization = max_utilization
                best_path = path
        
        return best_path if best_path else paths[0]  # Default to first path if all are over capacity
    
    def install_flow_path(self, flow, path):
        """Install a flow along a path."""
        if not path or len(path) < 2:
            return
        
        # Clear previous path if it exists
        self.uninstall_flow_path(flow)
        
        # Set the new path
        flow.path = path
        
        # Update link utilization
        for i in range(len(path) - 1):
            src, dst = path[i], path[i+1]
            link = self.topology[src][dst]['link']
            link.used_capacity += flow.bandwidth
            link.flows.add(flow.flow_id)
        
        # Generate and install flow table entries
        for i in range(len(path) - 1):
            src_node = path[i]
            next_hop = path[i+1]
            
            # Simple flow table entry: (flow_id, in_port, out_port)
            # In a real SDN, these would be OpenFlow entries with match fields
            flow_entry = {
                'flow_id': flow.flow_id,
                'src': flow.src,
                'dst': flow.dst,
                'next_hop': next_hop,
                'priority': flow.priority
            }
            
            self.switch_flow_tables[src_node].append(flow_entry)
    
    def uninstall_flow_path(self, flow):
        """Remove a flow from its current path."""
        path = flow.path
        if not path or len(path) < 2:
            return
        
        # Update link utilization
        for i in range(len(path) - 1):
            src, dst = path[i], path[i+1]
            if self.topology.has_edge(src, dst):  # Check if edge still exists
                link = self.topology[src][dst]['link']
                link.used_capacity = max(0, link.used_capacity - flow.bandwidth)
                link.flows.discard(flow.flow_id)
        
        # Remove flow table entries
        for node in path[:-1]:
            self.switch_flow_tables[node] = [
                entry for entry in self.switch_flow_tables[node]
                if entry['flow_id'] != flow.flow_id
            ]
    
    def remove_flow(self, flow_id):
        """Remove a flow from the network."""
        if flow_id not in self.flows:
            return f"Error: Flow {flow_id} does not exist"
        
        flow = self.flows[flow_id]
        self.uninstall_flow_path(flow)
        del self.flows[flow_id]
        
        return f"Removed flow {flow_id}"
    
    def reroute_flow(self, flow):
        """Reroute a flow after a topology change."""
        # For critical flows, switch to the backup path if available
        if flow.is_critical and flow.backup_path:
            # Verify backup path is still valid
            valid_backup = True
            for i in range(len(flow.backup_path) - 1):
                src, dst = flow.backup_path[i], flow.backup_path[i+1]
                if not self.topology.has_edge(src, dst) or not self.topology[src][dst]['link'].active:
                    valid_backup = False
                    break
            
            if valid_backup:
                # Uninstall the current path
                self.uninstall_flow_path(flow)
                # Install the backup path
                self.install_flow_path(flow, flow.backup_path)
                # Compute a new backup path
                paths = self.compute_k_shortest_paths(flow.src, flow.dst, k=2)
                if len(paths) >= 2 and paths[0] != flow.backup_path:
                    flow.backup_path = paths[1]
                else:
                    flow.backup_path = []
                return
        
        # Compute a new path
        path = self.compute_shortest_path(flow.src, flow.dst)
        if path:
            self.uninstall_flow_path(flow)
            self.install_flow_path(flow, path)
            
            # For critical flows, compute a new backup path
            if flow.is_critical:
                paths = self.compute_k_shortest_paths(flow.src, flow.dst, k=2)
                if len(paths) >= 2 and paths[0] == path:
                    flow.backup_path = paths[1]
                else:
                    flow.backup_path = []
        else:
            # No path available, just uninstall the flow
            self.uninstall_flow_path(flow)
            flow.path = []
            flow.backup_path = []
    
    def optimize_all_flows(self):
        """Recompute paths for all flows to optimize network utilization."""
        # First, clear all flow paths
        for flow in self.flows.values():
            self.uninstall_flow_path(flow)
        
        # Sort flows by priority and critical status
        sorted_flows = sorted(
            self.flows.values(),
            key=lambda f: (f.is_critical, f.priority),
            reverse=True
        )
        
        # Reinstall flows in order of priority
        for flow in sorted_flows:
            if flow.is_critical:
                paths = self.compute_k_shortest_paths(flow.src, flow.dst, k=2)
                if paths:
                    flow.path = paths[0]
                    if len(paths) >= 2:
                        flow.backup_path = paths[1]
                    else:
                        flow.backup_path = []
                    self.install_flow_path(flow, flow.path)
            else:
                paths = self.compute_k_shortest_paths(flow.src, flow.dst, k=3)
                if paths:
                    best_path = self.select_least_utilized_path(paths, flow.bandwidth)
                    flow.path = best_path
                    self.install_flow_path(flow, flow.path)
    
    def get_network_stats(self):
        """Get network statistics."""
        stats = {
            'nodes': len(self.topology.nodes),
            'links': len(self.topology.edges) // 2,  # Divide by 2 for bidirectional links
            'active_flows': len(self.flows),
            'avg_link_utilization': 0,
            'max_link_utilization': 0,
            'num_congested_links': 0
        }
        
        link_utils = []
        for u, v, data in self.topology.edges(data=True):
            link = data['link']
            if link.active:
                utilization = link.utilization()
                link_utils.append(utilization)
                if utilization > 0.9:  # 90% utilization threshold for congestion
                    stats['num_congested_links'] += 1
        
        if link_utils:
            stats['avg_link_utilization'] = sum(link_utils) / len(link_utils)
            stats['max_link_utilization'] = max(link_utils) if link_utils else 0
        
        return stats
    
    def visualize_network(self, show_flows=True):
        """Visualize the network topology and flows."""
        plt.figure(figsize=(12, 8))
        
        # Create a position layout for nodes
        pos = nx.spring_layout(self.topology)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.topology, pos, node_size=700, node_color='lightblue')
        
        # Draw node labels
        nx.draw_networkx_labels(self.topology, pos, font_size=10)
        
        # Draw edges with color based on utilization
        for u, v, data in self.topology.edges(data=True):
            link = data['link']
            if link.active:
                # Color based on utilization (green to red)
                utilization = link.utilization()
                color = (min(1, utilization * 2), max(0, 1 - utilization * 2), 0)
                
                # Edge width based on capacity
                width = 1 + link.capacity / 5
                
                # Draw the edge
                nx.draw_networkx_edges(
                    self.topology, pos,
                    edgelist=[(u, v)],
                    width=width,
                    edge_color=[color],
                    arrows=True,
                    arrowsize=15
                )
                
                # Add utilization label
                edge_label = f"{link.used_capacity}/{link.capacity}"
                nx.draw_networkx_edge_labels(
                    self.topology, pos,
                    edge_labels={(u, v): edge_label},
                    font_size=8
                )
        
        # Draw flows if requested
        if show_flows:
            flow_paths = []
            for flow in self.flows.values():
                if flow.path and len(flow.path) > 1:
                    # Create path edges
                    path_edges = [(flow.path[i], flow.path[i+1]) for i in range(len(flow.path)-1)]
                    flow_paths.extend(path_edges)
            
            # Draw flow paths with a different style
            nx.draw_networkx_edges(
                self.topology, pos,
                edgelist=flow_paths,
                width=2,
                edge_color='blue',
                style='dashed',
                arrows=True,
                arrowsize=15,
                alpha=0.5
            )
        
        plt.title("SDN Network Topology")
        plt.axis('off')
        plt.tight_layout()
        plt.show()


class SDNControllerCLI(cmd.Cmd):
    """Simple command-line interface for the SDN controller."""
    
    prompt = 'SDN> '
    intro = 'Welcome to the SDN Controller CLI. Type help or ? to list commands.'
    
    def __init__(self):
        super().__init__()
        self.controller = SDNController()
        self.setup_test_network()
    
    def setup_test_network(self):
        """Set up a test network topology."""
        for i in range(1, 7):
            self.controller.add_node(i)
        
        # Add links in a topology (1 -- 2 -- 3)
        #                           |    |    |
        #                          (4 -- 5 -- 6)
        self.controller.add_link(1, 2, capacity=10)
        self.controller.add_link(2, 3, capacity=10)
        self.controller.add_link(1, 4, capacity=10)
        self.controller.add_link(2, 5, capacity=10)
        self.controller.add_link(3, 6, capacity=10)
        self.controller.add_link(4, 5, capacity=10)
        self.controller.add_link(5, 6, capacity=10)
        
        print("Created test network with 6 nodes and 7 bidirectional links")
    
    def do_add_node(self, arg):
        """Add a node to the network: add_node <node_id>"""
        try:
            node_id = int(arg)
            result = self.controller.add_node(node_id)
            print(result)
        except ValueError:
            print("Error: Node ID must be an integer")
    
    def do_add_link(self, arg):
        """Add a link: add_link <src> <dst> [capacity] [weight]"""
        args = arg.split()
        if len(args) < 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            capacity = int(args[2]) if len(args) > 2 else 10
            weight = int(args[3]) if len(args) > 3 else 1
            
            result = self.controller.add_link(src, dst, capacity, weight)
            print(result)
        except ValueError:
            print("Error: Node IDs, capacity, and weight must be integers")
    
    def do_remove_node(self, arg):
        """Remove a node: remove_node <node_id>"""
        try:
            node_id = int(arg)
            result = self.controller.remove_node(node_id)
            print(result)
        except ValueError:
            print("Error: Node ID must be an integer")
    
    def do_remove_link(self, arg):
        """Remove a link: remove_link <src> <dst>"""
        args = arg.split()
        if len(args) != 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            result = self.controller.remove_link(src, dst)
            print(result)
        except ValueError:
            print("Error: Node IDs must be integers")
    
    def do_add_flow(self, arg):
        """Add a flow: add_flow <src> <dst> [bandwidth] [priority] [is_critical]"""
        args = arg.split()
        if len(args) < 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            bandwidth = float(args[2]) if len(args) > 2 else 1
            priority = int(args[3]) if len(args) > 3 else 0
            is_critical = args[4].lower() == 'true' if len(args) > 4 else False
            
            result = self.controller.add_flow(src, dst, bandwidth, priority, is_critical)
            print(result)
        except ValueError:
            print("Error: Invalid arguments")
    
    def do_remove_flow(self, arg):
        """Remove a flow: remove_flow <flow_id>"""
        try:
            flow_id = int(arg)
            result = self.controller.remove_flow(flow_id)
            print(result)
        except ValueError:
            print("Error: Flow ID must be an integer")
    
    def do_fail_link(self, arg):
        """Simulate a link failure: fail_link <src> <dst>"""
        args = arg.split()
        if len(args) != 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            result = self.controller.simulate_link_failure(src, dst)
            print(result)
        except ValueError:
            print("Error: Node IDs must be integers")
    
    def do_restore_link(self, arg):
        """Restore a failed link: restore_link <src> <dst>"""
        args = arg.split()
        if len(args) != 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            result = self.controller.restore_link(src, dst)
            print(result)
        except ValueError:
            print("Error: Node IDs must be integers")
    
    def do_show_topology(self, arg):
        """Display the network topology: show_topology [with_flows]"""
        show_flows = arg.lower() == 'with_flows'
        self.controller.visualize_network(show_flows)
    
    def do_show_stats(self, arg):
        """Display network statistics"""
        stats = self.controller.get_network_stats()
        print("Network Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    def do_list_flows(self, arg):
        """List all active flows"""
        if not self.controller.flows:
            print("No active flows")
            return
        
        print("Active flows:")
        for flow_id, flow in self.controller.flows.items():
            path_str = " -> ".join(map(str, flow.path))
            backup_str = " -> ".join(map(str, flow.backup_path)) if flow.backup_path else "None"
            
            print(f"  Flow {flow_id}: {flow.src} -> {flow.dst}")
            print(f"    Path: {path_str}")
            print(f"    Backup: {backup_str}")
            print(f"    Bandwidth: {flow.bandwidth}, Priority: {flow.priority}, Critical: {flow.is_critical}")
    
    def do_show_flow_tables(self, arg):
        """Display flow tables for switches: show_flow_tables [switch_id]"""
        if arg:
            try:
                switch_id = int(arg)
                if switch_id in self.controller.switch_flow_tables:
                    print(f"Flow table for switch {switch_id}:")
                    for entry in self.controller.switch_flow_tables[switch_id]:
                        print(f"  Flow {entry['flow_id']}: {entry['src']} -> {entry['dst']}, Next hop: {entry['next_hop']}, Priority: {entry['priority']}")
                else:
                    print(f"No flow table entries for switch {switch_id}")
            except ValueError:
                print("Error: Switch ID must be an integer")
        else:
            print("Flow tables:")
            for switch_id, entries in self.controller.switch_flow_tables.items():
                print(f"  Switch {switch_id}: {len(entries)} entries")
    
    def do_simulate_traffic(self, arg):
        """Simulate random traffic flows: simulate_traffic <num_flows>"""
        try:
            num_flows = int(arg) if arg else 5
            
            nodes = list(self.controller.topology.nodes())
            if len(nodes) < 2:
                print("Error: Need at least 2 nodes in the network")
                return
            
            for _ in range(num_flows):
                src, dst = random.sample(nodes, 2)
                bandwidth = random.uniform(0.5, 2.0)
                priority = random.randint(0, 2)
                is_critical = random.random() < 0.2  # 20% chance of being critical
                
                result = self.controller.add_flow(src, dst, bandwidth, priority, is_critical)
                print(result)
            
            print(f"Added {num_flows} random flows")
        except ValueError:
            print("Error: Number of flows must be an integer")
    
    def do_query_path(self, arg):
        """Query the path between two nodes: query_path <src> <dst>"""
        args = arg.split()
        if len(args) != 2:
            print("Error: Provide source and destination nodes")
            return
        
        try:
            src = int(args[0])
            dst = int(args[1])
            path = self.controller.compute_shortest_path(src, dst)
            
            if path:
                print(f"Shortest path from {src} to {dst}: {' -> '.join(map(str, path))}")
                
                # Calculate path details
                total_weight = 0
                total_utilization = 0
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    if self.controller.topology.has_edge(u, v):
                        link = self.controller.topology[u][v]['link']
                        weight = self.controller.topology[u][v]['weight']
                        utilization = link.utilization()
                        total_weight += weight
                        total_utilization += utilization
                        print(f"  Link {u}->{v}: Weight={weight}, Utilization={utilization:.2f}")
                
                if len(path) > 1:
                    avg_utilization = total_utilization / (len(path) - 1)
                    print(f"  Total path weight: {total_weight}")
                    print(f"  Average path utilization: {avg_utilization:.2f}")
            else:
                print(f"No path available from {src} to {dst}")
        except ValueError:
            print("Error: Node IDs must be integers")
    
    def do_exit(self, arg):
        """Exit the SDN controller CLI"""
        print("Exiting SDN Controller CLI")
        return True
    
    def do_quit(self, arg):
        """Exit the SDN controller CLI"""
        return self.do_exit(arg)
    
    def do_EOF(self, arg):
        """Exit on Ctrl-D"""
        print()
        return self.do_exit(arg)


def main():
    cli = SDNControllerCLI()
    cli.cmdloop()


if __name__ == "__main__":
    main()