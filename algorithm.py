from parsing import Map
from random import choice
from typing import Any


class Algorithm:

    """Compute collision-free routes for a fleet of drones.

    The algorithm determines paths between the configured start and end
    zones while respecting zone capacities, connection capacities, and
    special zone behaviors such as restricted and priority zones.
    """

    def __init__(self, map_info: Map) -> None:

        """Initialize the algorithm with map information.

        Args:
            map_info: Parsed map containing zones, connections, drone
                count, and routing constraints.
        """

        self.map_info = map_info
        self.nb_drones = map_info.nb_drones
        self.zones_dict = map_info.zones
        self.zones_connected = map_info.zones_connected
        self.connections = map_info.connections
        self.start_zone = map_info.start_zone
        self.end_zone = map_info.end_zone
        self.zone_names = self.zones_dict.keys()
        self.turn_occupancy: dict[int | float, Any] = dict()

    def update_occupancy(self, number: int | float, element: str) -> None:

        """Update occupancy information for a specific turn.

        Creates occupancy tracking for the turn if it does not already
        exist, then increments the occupancy count of the given zone or
        connection.

        Args:
            number: Turn number to update.
            element: Zone or connection whose occupancy is being tracked.
        """

        if number not in self.turn_occupancy.keys():
            occupancy = dict()
            for zone in self.zone_names:
                occupancy[zone] = 0
            for connection in self.connections.keys():
                occupancy[connection] = 0
            self.turn_occupancy[number] = occupancy
        self.turn_occupancy[number][element] += 1

    def get_connection(self, zone1: str, zone2: str) -> str:

        """Retrieve the connection name linking two zones.

        Args:
            zone1: Name of the first zone.
            zone2: Name of the second zone.

        Returns:
            The connection identifier connecting the two zones.
        """

        connection = zone1 + "-" + zone2
        if connection not in self.connections.keys():
            connection = zone2 + "-" + zone1
        return (connection)

    def calc_wait_time(self, curr_zone: str, next_zone: str) -> int:

        """Calculate the waiting time required before a move.

        The waiting time depends on the current occupancy of the target
        connection and destination zone. Additional delay may be required
        when moving into restricted zones.

        Args:
            curr_zone: Current zone of the drone.
            next_zone: Candidate destination zone.

        Returns:
            Number of turns the drone must wait before the move can be
            performed.
        """

        connection = self.get_connection(curr_zone, next_zone)
        max_link_cap = self.connections[connection].max_link_capacity
        max_cap = self.zones_dict[next_zone].max_drones

        next_turn = self.acc_weights[curr_zone] + 1
        dest_turn = next_turn
        if self.zones_dict[next_zone].zone == "restricted":
            dest_turn += 1

        count = 0
        while True:
            try:
                if self.turn_occupancy[next_turn][connection] < max_link_cap:
                    if self.turn_occupancy[dest_turn][next_zone] < max_cap:
                        break
                count += 1
                next_turn += 1
                dest_turn += 1
            except KeyError:
                return (count)
        return (count)

    def update_acc_weights(self, curr_zone: str) -> None:

        """Update accumulated path weights for neighboring zones.

        Evaluates all neighboring zones and updates their accumulated
        travel cost based on zone weights and any required waiting time.

        Args:
            curr_zone: Zone whose neighbors are being evaluated.
        """

        neighbors = self.zones_connected[curr_zone]
        for zone in neighbors:
            zone_weight = self.zones_dict[zone].weight
            if zone_weight:
                wait_time = self.calc_wait_time(curr_zone, zone)
                new_weight = (self.acc_weights[curr_zone] +
                              zone_weight + wait_time)
                self.acc_weights[zone] = min(
                    new_weight, self.acc_weights[zone])

    def choose_next_zone(self) -> str:

        """Choose the next zone to explore.

        Among unvisited zones, selects one with the minimum accumulated
        weight. Priority zones are preferred when multiple candidates
        share the same weight.

        Args:
            curr_zone: Current zone being processed.

        Returns:
            The selected next zone.
        """

        candidates_dict = {
            zone: weight for zone, weight in self.acc_weights.items()
            if zone not in self.visited_zones}
        min_weight = min(candidates_dict.values())
        candidates = [
            zone for zone in candidates_dict.keys()
            if candidates_dict[zone] == min_weight]
        priority_candidates = [
            zone for zone in candidates
            if self.zones_dict[zone].zone == "priority"]
        if priority_candidates:
            return (choice(priority_candidates))
        return (choice(candidates))

    def choose_previous_zone(self, next_zone: str) -> None:

        """Store the predecessor of a zone in the computed path.

        Determines which previously visited neighboring zone provides
        the best route to the specified zone and records it for later
        path reconstruction.

        Args:
            next_zone: Zone whose predecessor is being selected.
        """

        connected_next_zone = []
        for zone in reversed(self.visited_zones):
            if next_zone in self.zones_connected[zone]:
                connected_next_zone.append(zone)

        min_weight = min([
            self.acc_weights[zone] for zone in connected_next_zone])
        prev_candidates = [
            zone for zone in connected_next_zone
            if self.acc_weights[zone] == min_weight]
        prev_priority_candidates = [
            zone for zone in prev_candidates
            if self.zones_dict[zone].zone == "priority"]
        choosen_zone = choice(prev_candidates)
        if prev_priority_candidates:
            choosen_zone = choice(prev_priority_candidates)
        self.prev_zone_dict[next_zone] = choosen_zone

    def algorithm(self) -> None:

        """Execute the pathfinding algorithm.

        Computes accumulated path costs and predecessor information for
        all reachable zones until the destination zone is reached.
        """

        curr_zone = self.start_zone
        self.visited_zones = []
        self.prev_zone_dict = {
            zone_name: "" for zone_name in self.zone_names
            if zone_name != self.start_zone}
        self.acc_weights = {
            zone_name: (0 if zone_name == self.start_zone else float("inf"))
            for zone_name in self.zone_names}

        while curr_zone != self.end_zone:

            self.visited_zones.append(curr_zone)
            self.update_acc_weights(curr_zone)
            next_zone = self.choose_next_zone()
            self.choose_previous_zone(next_zone)
            curr_zone = next_zone

    def get_drone_solution(self) -> list[str]:

        """Build the route for a single drone.

        Reconstructs the path from the destination zone back to the start
        zone and updates occupancy information for all turns occupied by
        the drone.

        Returns:
            A list describing the drone's route and waiting actions.
        """

        curr_zone = self.end_zone
        path = [curr_zone]

        while curr_zone in self.prev_zone_dict.keys():

            prev_zone = self.prev_zone_dict[curr_zone]
            curr_connection = self.get_connection(prev_zone, curr_zone)

            curr_zone_turn = self.acc_weights[curr_zone]
            prev_zone_turn = self.acc_weights[prev_zone]

            self.update_occupancy(curr_zone_turn, curr_connection)
            curr_zone_turn -= 1

            if self.zones_dict[curr_zone].zone == "restricted":
                self.update_occupancy(curr_zone_turn, curr_connection)
                path.append(curr_connection)
                curr_zone_turn -= 1

            while curr_zone_turn >= prev_zone_turn:

                self.update_occupancy(curr_zone_turn, prev_zone)
                if curr_zone_turn > prev_zone_turn:
                    path.append("waiting")
                else:
                    path.append(prev_zone)
                curr_zone_turn -= 1

            curr_zone = prev_zone

        path.pop()
        return (path)

    def get_fleet_solution(self) -> list[list[str]]:

        """Generate routes for all drones in the fleet.

        Routes are generated sequentially so that occupancy information
        from previously planned drones is taken into account.

        Returns:
            A list containing the route of each drone.
        """

        solution = []

        for drone_num in range(self.nb_drones):

            self.algorithm()
            solution.append(self.get_drone_solution())

        return (solution)
