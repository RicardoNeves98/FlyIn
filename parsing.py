import re
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Any, Optional, Literal, Self


class Zone(BaseModel):

    name: str
    start: bool = Field(default=False)
    end: bool = Field(default=False)
    pos: tuple[int, int]
    zone_type: Optional[Literal[
        "normal", "blocked", "priority", "restricted"]] = Field(default="normal")
    color: Optional[str] = Field(default=None)
    max_drones: Optional[int] = Field(default=1)


class Connection(BaseModel):

    name: str
    zone1: Zone
    zone2: Zone
    active: bool = Field(default=True)
    max_link_capacity: Optional[int] = Field(default=1)

    def move(self, Zone) -> Optional[Zone]:

        if Zone == self.zone1:
            return (self.zone2)
        elif Zone == self.zone2:
            return (self.zone1)
        else:
            return (None)


class Map(BaseModel):

    nb_drones: int = Field(ge=1)
    zones: list[Zone]
    connections: list[Connection]

    @model_validator(mode="after")
    def validator(self) -> Self:

        if len({zone.name for zone in self.zones}) < len(self.zones):
            raise ValueError("[ERROR] There are zones with the same name")
        if len({{connection.zone1.name, connection.zone2.name}
                for connection in self.connections}) < len(self.connections):
            raise ValueError("[ERROR] Every connection must be unique")
        path_to_end = False
        curr_zones = [zone for zone in self.zones if zone.start]
        max_moves = len(self.connections)
        while max_moves:
            if any(zone.end for zone in curr_zones):
                path_to_end = True
                break
            new_zones = []
            for zone in curr_zones:
                for connection in self.conncetions:
                    new_zone = connection.move(zone)
                    if new_zone:
                        new_zones.append(new_zone)
            curr_zones = new_zones
            max_moves -= 1
        if not path_to_end:
            raise ValueError("[ERROR] There is no path from start zone to end zone")
        return (self)


class MapCreater:

    def __init__(self, map_config: str) -> None:

        self.map_config = map_config

    def check_args(self) -> str:

        if not self.map_config.startswith("maps/"):
            raise ValueError("[ERROR] File must be inside 'maps' folder")
        if not self.map_config.endswith(".txt"):
            raise ValueError("[ERROR] File must be text format")

    def create_map_dict(self) -> None:

        @staticmethod
        def get_info(key_type: str, valid_keys: list[str], value: str,
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
                name, metadata = info.groups()
            info_dict["name"] = name
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
        zones = []
        connections = []
        start_zones = 0
        end_zones = 0
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
                    zone_info = get_info(
                        "zone", ["zone", "color", "max_drones"], value,
                        r"^([^\s\[\]\-]+)\s+([^\s\[\]]+)\s+([^\s\[\]]+)(?:\s+\[(.*?)\])?$",
                        "<name> <number> <number> [optional]")
                    if var == "start_hub":
                        start_zones += 1
                        zone_info["start"] = True
                    if var == "end_hub":
                        end_zones += 1
                        zone_info["end"] = True
                    zones.append(zone_info)
                elif var == "connection":
                    connection_info = get_info(
                        "connection", ["max_link_capacity"], value,
                        r"^([^-\s]+)\-([^-\s]+)(?:\s+\[(.*?)\])?$",
                        "<zone1-zone2> [optional]")
                    connections.append(connection_info)
                else:
                    raise ValueError(f"[ERROR] Unknown name '{line}'")
                line_count += 1
        if start_zones != 1 or end_zones != 1:
            raise ValueError("[ERROR] There must be only 1 start and end zone")
        map_dict["zones"] = zones
        map_dict["connections"] = connections
        return (map_dict)

    def create_map(map_dict: dict[str, Any]) -> Map:

        name_zone_dict = dict()
        for zone_dict in map_dict["zones"]:
            zone = Zone(**zone_dict)
            name_zone_dict[zone.name] = zone
        for connection_dict in map_dict["connections"]:
            zone1_name, zone2_name = connection_dict["name"].split("-")
            zone1 = name_zone_dict[zone1_name]
            zone2 = name_zone_dict[zone2_name]
            if zone1.zone_type == "blocked" or zone2.zone_type == "blocked":
                connection_dict["active"] = False
            connection_dict["zone1"] = zone1
            connection_dict["zone2"] = zone2
        return (Map(**map_dict))

