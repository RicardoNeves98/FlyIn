*This project has been created as part of the 42 curriculum by rcarmo-n*

# Fly-In

## Description

Fly-In is a drone fleet routing and visualization simulator designed to compute collision-free paths across a network of interconnected zones.

The project parses a custom map configuration file describing zones, connections, capacities, and drone constraints. It then calculates optimal routes for multiple drones while respecting:

* Zone occupancy limits
* Connection capacity limits
* Restricted zones with additional traversal costs
* Priority zones that are favored during route selection
* Blocked zones that cannot be traversed

After computing the routes, the program launches a graphical simulation using Pygame, allowing users to visualize drone movement in real time across the network.

The primary goal of the project is to demonstrate graph-based pathfinding, resource-constrained routing, input validation, and real-time visualization within a drone traffic management scenario.

---

# Features

* Custom map configuration format
* Strong input validation using Pydantic
* Graph construction from map files
* Multi-drone route planning
* Capacity-aware routing
* Collision avoidance
* Restricted, blocked, normal, and priority zone support
* Real-time graphical visualization with Pygame
* Turn-based simulation output
---

# Instructions

## Requirements

* Python 3
* Pygame
* Pydantic

## Installation

Create the virtual environment and install development tools and runtime dependencies:

```bash
make install
```

## Running the Project

Run the simulation using a map file located inside the `maps/` directory:

```bash
make run MAP=maps/example.txt
```

or

```bash
python3 main.py maps/example.txt
```

## Debug Mode

```bash
make debug MAP=maps/example.txt
```

## Static Analysis

Run linting and type checking:

```bash
make lint
```

## Cleaning Generated Files

```bash
make clean
```

---

# Map Format

A map file describes the drone network.

Example:

```text
nb_drones: 3

start_hub: A 0 0 [color=green]
hub: B 1 0 [zone=priority color=yellow]
hub: C 2 0 [zone=restricted color=orange]
end_hub: D 3 0 [color=red]

connection: A-B
connection: B-C
connection: C-D
```

## Supported Zone Types

| Zone Type  | Description                                    |
| ---------- | ---------------------------------------------- |
| normal     | Standard traversable zone                      |
| priority   | Preferred when multiple routes have equal cost |
| restricted | Traversable but incurs additional cost         |
| blocked    | Cannot be traversed                            |

## Optional Metadata

### Zone Metadata

```text
[zone=priority]
[color=yellow]
[max_drones=2]
```

### Connection Metadata

```text
[max_link_capacity=3]
```

---

# Algorithm Choices and Implementation Strategy

## Graph Representation

The map is modeled as an undirected graph:

* Zones represent graph nodes.
* Connections represent graph edges.
* An adjacency list is automatically generated during validation.

This representation provides efficient neighbor lookup and route exploration.

## Validation Phase

Before route computation begins, the map undergoes several validation steps:

* File structure validation
* Zone uniqueness verification
* Connection consistency verification
* Duplicate connection detection
* Start/end hub validation
* Reachability validation

A breadth-first search is performed to ensure at least one valid path exists between the start and end zones.

## Pathfinding Strategy

The routing algorithm is inspired by Dijkstra's shortest-path algorithm.

Each zone maintains an accumulated traversal cost:

```text
cost = previous_cost + zone_weight + waiting_time
```

Where:

* Normal zones have weight 1.
* Restricted zones have weight 2.
* Blocked zones have weight 0 and are excluded.
* Waiting time is dynamically calculated according to occupancy constraints.

The algorithm repeatedly:

1. Selects the unvisited zone with the lowest accumulated cost.
2. Stores predecessor information.
3. Updates neighboring zones.
4. Continues until the destination is reached.

## Priority Zone Handling

When several candidate zones share the same minimum cost:

* Priority zones are preferred.
* If multiple priority zones exist, one is selected randomly.
* Otherwise, a random minimum-cost candidate is selected.

This strategy promotes routing through preferred corridors without sacrificing optimality.

## Occupancy Management

To avoid collisions and congestion, the algorithm maintains a turn-based occupancy table.

After calculating a drone route it updates, by turn:

* Zone occupancy
* Connection occupancy

Before scheduling a move, the algorithm checks:

* Destination zone capacity
* Connection capacity

If the path is the optimal and limit is exceeded, the drone waits until the move becomes feasible.

This mechanism guarantees conflict-free fleet routing.

## Fleet Routing Strategy

Drones are planned sequentially.

After computing a route for one drone:

* Its occupancy information is stored.
* Subsequent drones consider those reservations.
* Routes adapt dynamically to existing traffic.

This produces realistic traffic-aware path planning.

---

# Visual Representation

## Pygame Visualization

The simulation includes a graphical interface built with Pygame.

The visualization converts map coordinates into screen coordinates and displays:

* Zones as colored nodes
* Connections as graph edges
* Drones as moving markers

## Animation System

Drone movement is animated progressively instead of teleporting between zones.

Each movement is decomposed into many smaller steps, creating smooth transitions between nodes.

The animation reflects:

* Drone movement
* Waiting periods
* Restricted zone traversal
* Concurrent fleet activity

## User Interaction

The visualizer supports:

### Pause / Resume

Press:

```text
SPACE
```

to pause or resume the simulation.

### Window Controls

Users can close the simulation at any time using the standard window controls.

## User Experience Benefits

The visualization significantly improves understanding of the routing process by:

* Making path decisions visible
* Showing traffic interactions between drones
* Demonstrating capacity constraints
* Allowing real-time observation of congestion effects
* Providing immediate feedback about algorithm behavior

Without the visualization, route planning would only be represented through console output.

---

# Project Structure

```text
.
├── main.py
├── parsing.py
├── algorithm.py
├── visuals.py
└── Makefile
```

### main.py

Program entry point.

### parsing.py

Configuration parsing and validation.

### algorithm.py

Pathfinding and fleet scheduling logic.

### visuals.py

Pygame-based graphical simulation.

---

# Resources

## Documentation

* Python Documentation
* Pydantic Documentation
* Pygame Documentation
* MyPy Documentation
* Flake8 Documentation

## Algorithms and Concepts

* Graph Theory
* Breadth-First Search (BFS)
* Dijkstra's Shortest Path Algorithm
* Resource-Constrained Pathfinding
* Traffic Scheduling and Occupancy Management

## Tutorials and References

* Pygame Official Tutorials
* Python Type Hinting Documentation
* Pydantic Model Validation Guides

---

# AI Usage

Artificial Intelligence tools were used during the development of this project for:

* Code documentation generation
* Refactoring suggestions
* Type-hint verification assistance
* README drafting and organization
* Discussion and validation of algorithmic approaches

---

# Future Improvements

Potential enhancements include:

* Alternative pathfinding strategies (A*)
* Dynamic obstacle support
* Real-time route recalculation
* Interactive map editor
* Enhanced drone visualization
* Statistics and performance metrics
* Exportable simulation reports
* Support for larger-scale drone fleets
* Advanced traffic prioritization policies
