import re
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Any, Optional, Literal, Self


class Zone(BaseModel):

    name: str
    pos: tuple[int, int]
    zone: Optional[Literal["normal", "blocked", "priority", "restricted"]]
    weight: Optional[int] = Field(default=1)
    color: Optional[str] = Field(default=None)
    max_drones: Optional[int] = Field(default=1)

    @model_validator(mode="after")
    def get_weight(self) -> Self:

        if self.zone == "restricted":
            self.weight = 2
        elif self.zone == "priority":
            self.weight = 0.5
        elif self.zone == "blocked":
            self.weight = None


class Connection(BaseModel):

    name: str
    destination: str
    active: bool = Field(default=True)
    max_link_capacity: Optional[int] = Field(default=1)


class Map(BaseModel):

    nb_drones: int = Field(ge=1)
    zones: dict[str, Zone]
    zone_connections: dict[str, list[Connection]]
    nb_connections: int = Field(ge=1)
    start_zone: str
    end_zone: str

    @model_validator(mode="before")
    def get_neighbors(cls, map_dict: dict[str, Any]) -> dict[str, Any]:

        zone_names_set = set(map_dict["zones"].keys())
        zone_connections = dict()
        connections_set = set()
        nb_connections = len(map_dict["connections"])
        for zone_name in zone_names_set:
            zone_connections[zone_name] = list()
        for connection in map_dict["connections"]:
            connection_set = frozenset({connection["zone1"], connection["zone2"]})
            if not connection_set <= zone_names_set:
                raise ValueError("[ERROR] Connection '{connection}' links unknown zones")
            zone1_name, zone2_name = connection_set
            zone_connections[zone1_name].append({
                "name": connection["name"], "destination": zone2_name, 
                "active": map_dict["zones"][zone1_name]["zone"] != "blocked",
                "max_link_capacity": connection["max_link_capacity"]})
            zone_connections[zone2_name].append({
                "name": connection["name"], "destination": zone1_name, 
                "active": map_dict["zones"][zone1_name]["zone"] != "blocked",
                "max_link_capacity": connection["max_link_capacity"]})
            connections_set.add(connection_set)
        if len(connections_set) < nb_connections:
            raise ValueError("[ERROR] There are multiple connections with the same zones")
        del map_dict["connections"]
        map_dict["zone_connections"] = zone_connections
        map_dict["nb_connections"] = nb_connections 
        return (map_dict)

    @model_validator(mode="after")
    def check_path(self) -> Self:
    
        path_to_end = False
        curr_zones_name = [self.start_zone]
        visited_zones = curr_zones_name
        max_moves = self.nb_connections
        while max_moves:
            new_zones = []
            for zone_name in curr_zones_name:
                for connection in self.zone_connections[zone_name]:
                    new_zones.append(connection.destination)
            new_zones = [zone for zone in new_zones if zone not in visited_zones]
            print(new_zones)
            curr_zones = new_zones
            visited_zones.extend(new_zones)
            if any(self.end_zone == zone_name for zone_name in curr_zones_name):
                path_to_end = True
                break
            max_moves -= 1
        if not path_to_end:
            raise ValueError("[ERROR] There is no path from start zone to end zone")
        return (self)


class ParsingFile:

    def __init__(self, map_config: str) -> None:

        self.map_config = map_config

    def check_args(self) -> str:

        if not self.map_config.startswith("maps/"):
            raise ValueError("[ERROR] File must be inside 'maps' folder")
        if not self.map_config.endswith(".txt"):
            raise ValueError("[ERROR] File must be text format")

    def create_map_dict(self) -> None:

        @staticmethod
        def read_info(key_type: str, valid_keys: list[str], value: str,
                      pattern: str, shape: str) -> dict[str, Any]:

            info_dict = dict()
            info = re.search(pattern, value)
            if not info:
                raise ValueError("[ERROR] " + key_type.capitalize() +
                                 " must have this format: " + shape)
            if key_type == "zone":
                name, x_pos, y_pos, metadata = info.groups()
                info_dict["pos"] = (x_pos, y_pos)
            elif key_type == "connection":
                zone1, zone2, metadata = info.groups()
                info_dict["zone1"], info_dict["zone2"] = zone1, zone2
                name = zone1 + "-" + zone2
            info_dict["name"] = name
            if (not metadata or "zone" not in metadata) and key_type == "zone":
                info_dict["zone"] = "normal"
            if ((not metadata or "max_link_capacity" not in metadata) and
                key_type == "connection"):
                info_dict["max_link_capacity"] = 1
            if metadata:
                metadata_list = metadata.split()
                for data in metadata_list:
                    key, value = data.split("=")
                    if key in valid_keys:
                        info_dict[key] = value
                    else:
                        raise ValueError(f"[ERROR] '{key}' is not valid metadata")
            return (info_dict)

        map_dict = dict()
        map_dict["zones"] = dict()
        connections = []
        with open(self.map_config, "r") as file:
            line_count = 1
            for line in file:
                if line.startswith("#") or line.strip() == "":
                    continue
                var, value = line.split(":")
                value = value.strip()
                if line_count == 1 and var == "nb_drones":
                    map_dict[var] = value
                elif "hub" in var:
                    zone_info = read_info(
                        "zone", ["zone", "color", "max_drones"], value,
                        r"^([^\s\[\]\-]+)\s+([^\s\[\]]+)\s+([^\s\[\]]+)(?:\s+\[(.*?)\])?$",
                        "<name> <number> <number> [optional]")
                    if var == "start_hub":
                        if "start_zone" in map_dict.keys():
                            raise ValueError("[ERROR] There can only be one start zone")
                        map_dict["start_zone"] = zone_info["name"]
                    elif var == "end_hub":
                        if "end_zone" in map_dict.keys():
                            raise ValueError("[ERROR] There can only be one end zone")
                        map_dict["end_zone"] = zone_info["name"]
                    if zone_info["name"] in map_dict["zones"].keys():
                        raise ValueError("[ERROR] Different zones cant have the same name")
                    map_dict["zones"][zone_info["name"]] = zone_info
                elif var == "connection":
                    connection_info = read_info(
                        "connection", ["max_link_capacity"], value,
                        r"^([^-\s]+)\-([^-\s]+)(?:\s+\[(.*?)\])?$",
                        "<zone1-zone2> [optional]")
                    connections.append(connection_info)
                else:
                    raise ValueError(f"[ERROR] Unknown name '{line}'")
                line_count += 1
        map_dict["connections"] = connections
        return (map_dict)

