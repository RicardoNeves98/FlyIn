from parsing import Map
from typing import Any


class Algorithm:

    def __init__(self, drone_map: Map) -> None:

        self.drone_map = drone_map
        self.zones_dict = drone_map.zones
        self.zone_connections = drone_map.zone_connections
        self.start_zone = drone_map.start_zone
        self.end_zone = drone_map.end_zone
        self.zone_names = self.zones_dict.keys()
        self.acc_weights = {zone_name: (0 if zone_name == self.start_zone else
                                        float('inf')) for zone_name in self.zone_names}
        self.previous_zone = {zone_name: None for zone_name in self.zone_names
                              if zone_name != self.start_zone}
        self.visited_zones = []

    def explore_zones(self, curr_zone_name: str) -> dict[str, str]:

        while (curr_zone_name != self.end_zone):
            self.visited_zones.append(curr_zone_name)
            possible_zones = self.zone_connections[curr_zone_name]
            for connection in possible_zones:
                zone_name = connection.destination
                zone_weight = self.zones_dict[zone_name].weight
                if zone_weight:
                    new_weight = self.acc_weights[curr_zone_name] + zone_weight
                    self.acc_weights[zone_name] = min(
                        new_weight, self.acc_weights[zone_name])
            choice_dict = {
                zone_name: weight for zone_name, weight in self.acc_weights.items() if
                zone_name not in self.visited_zones}
            next_zone = min(choice_dict, key=choice_dict.get)
            self.previous_zone[next_zone] = curr_zone_name
            curr_zone_name = next_zone
        return (self.previous_zone)
