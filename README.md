# 4501q4: SDN
SDN Implementation

I implemented a Software-Defined Networking (SDN) controller for CSC4501. I built this controller to simulate how SDN systems work in real-world networks, focusing on topology management, flow control, and handling network failures.

## What My Controller Can Do

I created this controller to handle several important SDN functions:

- **Managing network topologies**: You can add/remove nodes and links to build different network structures
- **Smart path finding**: The controller calculates optimal paths and balances loads across multiple routes
- **Flow control**: It creates and manages network flows with different priorities
- **Handling failures**: When links go down, the controller automatically reroutes traffic
- **Visualization**: You can see a visual representation of the network and traffic flows
- **Simple command interface**: I built a CLI that makes it easy to interact with the network

## What You'll Need

To run my controller, you'll need:
- Python 3.6 or newer
- NetworkX library (for graph management)
- Matplotlib (for visualization)

## Setting It Up

Just follow these steps:

1. Clone this repo:
   ```bash
   git clone https://github.com/yourusername/sdn-controller.git
   cd sdn-controller
   ```

2. Install the libraries you'll need:
   ```bash
   pip install networkx matplotlib
   ```

## Running the Controller

Simply run:

```bash
python sdn_controller.py
```

This starts up my controller with a test network I configured, so you can immediately start experimenting.

## Commands You Can Use

Here are the main commands I implemented for the CLI:

| Command | What it does | Example |
|---------|-------------|---------|
| `add_node <id>` | Adds a new node to the network | `add_node 7` |
| `add_link <src> <dst> [capacity] [weight]` | Connects two nodes | `add_link 1 7 15 2` |
| `remove_node <id>` | Removes a node | `remove_node 7` |
| `remove_link <src> <dst>` | Removes a connection | `remove_link 1 7` |
| `add_flow <src> <dst> [bandwidth] [priority] [is_critical]` | Creates a new flow | `add_flow 1 6 2 1 true` |
| `remove_flow <id>` | Removes a flow | `remove_flow 0` |
| `fail_link <src> <dst>` | Simulates a link going down | `fail_link 1 2` |
| `restore_link <src> <dst>` | Brings a link back up | `restore_link 1 2` |
| `show_topology [with_flows]` | Shows the network | `show_topology with_flows` |
| `show_stats` | Shows network stats | `show_stats` |
| `list_flows` | Lists all active flows | `list_flows` |
| `show_flow_tables [switch_id]` | Shows flow tables | `show_flow_tables 2` |
| `simulate_traffic <num_flows>` | Adds random flows | `simulate_traffic 5` |
| `query_path <src> <dst>` | Finds the best path | `query_path 1 6` |
| `exit` or `quit` | Exits the program | `exit` |

## Example Session

Here's how I typically test my controller:

```
# Start it up
python sdn_controller.py

# Add a few flows to see how routing works
SDN> add_flow 1 6 2 1 true
SDN> add_flow 2 5 1 0 false

# Look at the network with the flows
SDN> show_topology with_flows

# Check how the network is doing
SDN> show_stats

# See what happens when a link fails
SDN> fail_link 1 2

# Check how my controller handled the rerouting
SDN> list_flows

# Add some random traffic to simulate a busy network
SDN> simulate_traffic 5

# See how the flow tables look now
SDN> show_flow_tables
```

## How I Built It

I structured my controller with several main components:

1. **Network Graph**: Uses a directed graph to represent the network
2. **Flow Manager**: Handles all the traffic flows
3. **Path Calculator**: Finds the best routes through the network
4. **Flow Table Manager**: Keeps track of forwarding rules
5. **Visualization Tool**: Shows what's happening in the network
6. **Command Interface**: Lets you interact with everything

Check out my design document for more details on how I implemented these components and the algorithms I used.

## Feedback Welcome!

This was a challenging project that taught me a lot about networks and SDN principles. If you have any questions or suggestions, feel free to reach out!
