import re
from pydantic import BaseModel, Field, model_validator
from typing import Any, Optional, Literal
from typing_extensions import Self


class Zone(BaseModel):

    """Represents a zone in the map used for drone routing."""

    name: str
    pos: tuple[int, int]
    zone: Optional[Literal["normal", "blocked",
                           "priority", "restricted"]] = Field(default="normal")
    weight: int = Field(default=1)
    color: str
    max_drones: Optional[int] = Field(default=1)

    @model_validator(mode="after")
    def get_weight(self) -> Self:

        """Adjust zone weight based on zone type.

        Returns:
            The validated Zone instance with updated weight.
        """

        if self.zone == "restricted":
            self.weight = 2
        elif self.zone == "blocked":
            self.weight = 0

        return (self)


class Connection(BaseModel):

    """Represents a connection between two zones."""

    name: str
    zone1: str
    zone2: str
    max_link_capacity: Optional[int] = Field(default=1)


class Map(BaseModel):

    """Represents the full map configuration for drone routing."""

    nb_drones: int = Field(ge=1)
    zones: dict[str, Zone]
    zones_connected: dict[str, list[str]]
    connections: dict[str, Connection]
    nb_connections: int = Field(ge=1)
    start_zone: str
    end_zone: str

    @model_validator(mode="before")
    def get_neighbors(cls, map_dict: dict[str, Any]) -> dict[str, Any]:

        """Build adjacency list from raw connection data.

        Args:
            map_dict: Raw dictionary parsed from input file before validation.

        Returns:
            Updated dictionary containing:
            - zones_connected (adjacency list)
            - nb_connections (validated connection count)

        Raises:
            ValueError: If a connection references unknown zones or if
                duplicate connections exist between the same zones.
        """

        zone_names_set = set(map_dict["zones"].keys())
        zones_connected: dict[str, list[str]] = dict()
        connections_set = set()
        nb_connections = len(map_dict["connections"])
        for zone_name in zone_names_set:
            zones_connected[zone_name] = list()
        for connection in map_dict["connections"].values():
            connection_set = frozenset({
                connection["zone1"], connection["zone2"]})
            if not connection_set <= zone_names_set:
                raise ValueError("[ERROR] Connection '{connection}' "
                                 "links unknown zones")
            zone1_name, zone2_name = connection_set
            zones_connected[zone1_name].append(zone2_name)
            zones_connected[zone2_name].append(zone1_name)
            connections_set.add(connection_set)
        if len(connections_set) < nb_connections:
            raise ValueError("[ERROR] There are multiple connections "
                             "with the same zones")
        map_dict["zones_connected"] = zones_connected
        map_dict["nb_connections"] = nb_connections
        return (map_dict)

    @model_validator(mode="after")
    def check_path(self) -> Self:

        """Verify that a path exists between start and end zones.

        Returns:
            The validated Map instance.

        Raises:
            ValueError: If no path exists.
        """

        path_to_end = False
        curr_zones = [self.start_zone]
        visited_zones = curr_zones
        max_moves = self.nb_connections
        while max_moves:
            new_zones = []
            for zone in curr_zones:
                new_zones.extend(self.zones_connected[zone])
            new_zones = [zone for zone in new_zones if
                         zone not in visited_zones]
            curr_zones = new_zones
            visited_zones.extend(new_zones)
            if any(self.end_zone == zone for zone in curr_zones):
                path_to_end = True
                break
            max_moves -= 1
        if not path_to_end:
            raise ValueError("[ERROR] There is no path from "
                             "start zone to end zone")
        return (self)


class ParsingFile:

    """Parses a map configuration file into a structured Map dictionary.

    This class is responsible for:
    - Reading raw text configuration files
    - Extracting zones, connections, and metadata
    - Validating file structure
    - Producing a dictionary compatible with the Map model
    """

    def __init__(self, map_config: str) -> None:

        """Store configuration file path.

        Args:
            map_config: Path to the input map configuration file.
        """

        self.map_config = map_config

    def check_args(self) -> None:

        """Validate configuration file path and format.

        Raises:
            ValueError: If file path or format is invalid.
        """

        if not self.map_config.startswith("maps/"):
            raise ValueError("[ERROR] File must be inside 'maps' folder")
        if not self.map_config.endswith(".txt"):
            raise ValueError("[ERROR] File must be text format")

    def create_map_dict(self) -> dict[str, Any]:

        """Parse configuration file into a structured dictionary.

        This method:
        - Reads the input file line by line
        - Extracts zones, connections, start/end hubs
        - Applies default values for important missing metadata
        - Validates naming consistency and duplicates

        Returns:
            Dictionary containing: zones, connections, start_zone,
            end_zone and nb_drones

        Raises:
            ValueError: If file format is invalid or inconsistent.
        """

        def read_info(key_type: str, valid_keys: list[str], value: str,
                      pattern: str, shape: str) -> dict[str, Any]:

            """Parse a single zone or connection definition line.

            This helper:
            - Applies regex parsing
            - Extracts structured fields
            - Applies default metadata
            - Validates allowed metadata keys

            Args:
                key_type: Type of element ("zone" or "connection").
                valid_keys: Allowed metadata fields for this element type.
                value: Raw string content from file.
                pattern: Regex pattern used for parsing.
                shape: Expected format description for error messages.

            Returns:
                Dictionary containing parsed structured data.

            Raises:
                ValueError: If format or metadata is invalid.
            """

            info_dict: dict[str, Any] = dict()
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
            link_cap_miss = not metadata or "max_link_capacity" not in metadata
            if link_cap_miss and key_type == "connection":
                info_dict["max_link_capacity"] = 1
            if metadata:
                metadata_list = metadata.split()
                for data in metadata_list:
                    key, value = data.split("=")
                    if key in valid_keys:
                        info_dict[key] = value
                    else:
                        raise ValueError(f"[ERROR] '{key}' is not "
                                         f"valid metadata")
            if "color" not in info_dict.keys() and key_type == "zone":
                info_dict["color"] = "blue"
            return (info_dict)

        start_zones = 0
        end_zones = 0
        map_dict: dict[str, Any] = dict()
        map_dict["zones"] = dict()
        map_dict["connections"] = dict()
        zone_pattern = (
            r"^([^\s\[\]\-]+)\s+([^\s\[\]]+)\s+([^\s\[\]]+)"
            r"(?:\s+\[(.*?)\])?$"
        )
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
                        zone_pattern, "<name> <number> <number> [optional]")
                    if var == "start_hub":
                        start_zones += 1
                        map_dict["start_zone"] = zone_info["name"]
                    elif var == "end_hub":
                        end_zones += 1
                        map_dict["end_zone"] = zone_info["name"]
                    if zone_info["name"] in map_dict["zones"].keys():
                        raise ValueError("[ERROR] Different zones cant "
                                         "have the same name")
                    map_dict["zones"][zone_info["name"]] = zone_info
                elif var == "connection":
                    connection_info = read_info(
                        "connection", ["max_link_capacity"], value,
                        r"^([^-\s]+)\-([^-\s]+)(?:\s+\[(.*?)\])?$",
                        "<zone1-zone2> [optional]")
                    map_dict["connections"][connection_info[
                        "name"]] = connection_info
                else:
                    raise ValueError(f"[ERROR] Unknown name '{line}'")
                line_count += 1
        if (start_zones != 1 and end_zones != 1):
            raise ValueError("[ERROR] There has to be at least "
                             "one start and end zones")
        return (map_dict)
