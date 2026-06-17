from parsing import Map
from random import choice
from typing import Any


class Algorithm:

    def __init__(self, map_info: Map) -> None:

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

        if number not in self.turn_occupancy.keys():
            occupancy = dict()
            for zone in self.zone_names:
                occupancy[zone] = 0
            for connection in self.connections.keys():
                occupancy[connection] = 0
            self.turn_occupancy[number] = occupancy
        self.turn_occupancy[number][element] += 1

    def get_connection(self, zone1: str, zone2: str) -> str:

        connection = zone1 + "-" + zone2
        if connection not in self.connections.keys():
            connection = zone2 + "-" + zone1
        return (connection)

    def calc_wait_time(self, curr_zone: str, next_zone: str) -> int:

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

        neighbors = self.zones_connected[curr_zone]
        for zone in neighbors:
            zone_weight = self.zones_dict[zone].weight
            if zone_weight:
                wait_time = self.calc_wait_time(curr_zone, zone)
                new_weight = (self.acc_weights[curr_zone] + zone_weight +
                              wait_time)
                self.acc_weights[zone] = min(
                    new_weight, self.acc_weights[zone])

    def choose_next_zone(self, curr_zone: str) -> str:

        candidates_dict = {
            zone: weight for zone, weight in self.acc_weights.items() if
            zone not in self.visited_zones}
        min_weight = min(candidates_dict.values())
        candidates = [zone for zone in candidates_dict.keys() if
                      candidates_dict[zone] == min_weight]
        priority_candidates = [zone for zone in candidates if
                               self.zones_dict[zone].zone == "priority"]
        if priority_candidates:
            return (choice(priority_candidates))
        return (choice(candidates))

    def choose_previous_zone(self, next_zone: str) -> None:

        connected_next_zone = []
        for zone in reversed(self.visited_zones):
            if next_zone in self.zones_connected[zone]:
                connected_next_zone.append(zone)
        min_weight = min([self.acc_weights[zone] for zone
                          in connected_next_zone])
        prev_candidates = [zone for zone in connected_next_zone if
                           self.acc_weights[zone] == min_weight]
        prev_priority_candidates = [zone for zone in prev_candidates if
                                    self.zones_dict[zone].zone == "priority"]
        choosen_zone = choice(prev_candidates)
        if prev_priority_candidates:
            choosen_zone = choice(prev_priority_candidates)
        self.prev_zone_dict[next_zone] = choosen_zone

    def algorithm(self) -> None:

        curr_zone = self.start_zone
        self.visited_zones = []
        self.prev_zone_dict = {zone_name: "" for zone_name in self.zone_names
                               if zone_name != self.start_zone}
        self.acc_weights = {
            zone_name: (0 if zone_name == self.start_zone else
                        float('inf')) for zone_name in self.zone_names}

        while (curr_zone != self.end_zone):

            self.visited_zones.append(curr_zone)
            self.update_acc_weights(curr_zone)
            next_zone = self.choose_next_zone(curr_zone)
            self.choose_previous_zone(next_zone)
            curr_zone = next_zone

    def get_drone_solution(self) -> list[str]:

        curr_zone = self.end_zone
        path = [curr_zone]

        while (curr_zone in self.prev_zone_dict.keys()):

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
            while (curr_zone_turn >= prev_zone_turn):
                self.update_occupancy(curr_zone_turn, prev_zone)
                if (curr_zone_turn > prev_zone_turn):
                    path.append("waiting")
                else:
                    path.append(prev_zone)
                curr_zone_turn -= 1
            curr_zone = prev_zone

        path.pop()
        return (path)

    def get_fleet_solution(self) -> list[list[str]]:

        solution = []

        for drone_num in range(self.nb_drones):

            self.algorithm()
            solution.append(self.get_drone_solution())

        return (solution)
