from parsing import Map
from typing import Any


class Algorithm:

    def __init__(self, drone_map: Map) -> None:

        self.drone_map = drone_map
        self.connections = drone_map.connections
        self.zones_dict = drone_map.zones
        self.start_zone = drone_map.start_zone
        self.end_zone = drone_map.end_zone
        self.zone_names = self.zones_dict.keys()
        self.acc_weights = {zone_name: (0 if zone_name == self.start_zone else
                                        float('inf')) for zone_name in self.zone_names}
        self.previous_zone = {zone_name: None for zone_name in self.zone_names
                              if zone_name != self.start_zone}
        self.visited_zones = []

    def explore_zones(self, curr_zone_name: str) -> dict[str, str]:

        self.visited_zones.append(curr_zone_name)
        possible_zones = self.drone_map.get_connections(
                curr_zone_names, self.visited_zones)
        for zone_name in possible_zones:
            zone_weight = self.zones_dict[zone_name].weigth
            if zone_weight:
                new_weight = acc_weights[curr_zone_name] + zone_weigth
                self.acc_weights[zone_name] = min(
                    new_weight, acc_weights[zone_name])
        possible_weights = {zone_name: weight for zone_name, weight in
                            self.acc_weights.items() if zone_name in possible_moves}
        next_zone = min(possible_weights, key=possible_weights.get)
        non_visited_weights = {
                zone_name: weight for zone_name, weight in self.acc_weights.items()
                in zone_name not in self.visited_zones}
        next_zone = min(non_visited_weights, key=non_visited_weights.get)
        self.previous_zone[next_zone] = curr_zone_name
        if next_zone != self.end_zone:
            self.explore_zones(next_zone)
        return (self.previous_zone)
