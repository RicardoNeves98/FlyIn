from typing import Any
from parsing import Map
from math import hypot
import time
import pygame


class Drone:

    def __init__(self, number: int, position: tuple[int | float, int | float],
                 solution: list[str]) -> None:

        self.drone_num = number
        self.in_zone = True
        self.position = position
        self.solution = solution
        self.direction = (0, 0)
        self.speed: float = 0
        self.finished = False

    def get_next_zone(
            self, next_move: str, zones: dict[str, Any],
            zones_pixel: dict[str, Any]) -> str:

        x_pos, y_pos = self.position
        next_zone = next_move
        if next_move not in zones.keys():
            self.in_zone = True
            zone1, zone2 = next_move.split("-")
            next_zone = zone2
            if self.position == zones_pixel[zone2]:
                next_zone = zone1
        elif zones[next_zone].zone == "restricted":
            self.in_zone = False
        else:
            self.in_zone = True
        return (next_zone)

    def prepare_next_move(
            self, zones: dict[str, Any], zones_pixel: dict[str, Any],
            moves_num: int) -> str:

        if not self.solution:
            self.finished = True
            self.speed = 0
            return ("")
        next_move = self.solution.pop()
        if next_move == "waiting":
            self.in_zone = True
            self.speed = 0
            return ("")
        next_zone = self.get_next_zone(next_move, zones, zones_pixel)
        x_pos, y_pos = self.position
        x_next, y_next = zones_pixel[next_zone]
        x_diff, y_diff = x_next - x_pos, y_next - y_pos
        path_size = hypot(x_diff, y_diff)
        x_unit = round(x_diff / path_size, 2)
        y_unit = round(y_diff / path_size, 2)
        self.direction = (x_unit, y_unit)
        if next_move not in zones.keys():
            path_size = path_size / 2
        self.speed = path_size / moves_num
        return (f"D{self.drone_num}-{next_move} ")

    def make_small_move(self) -> None:

        if self.speed:
            x_unit, y_unit = self.direction
            x_curr, y_curr = self.position
            x_curr += x_unit * self.speed
            y_curr += y_unit * self.speed
            self.position = (x_curr, y_curr)


class Animation:

    def __init__(self, map_info: Map, scale: int, screen_space: int,
                 solution: list[list[str]]) -> None:

        self.zones = map_info.zones
        self.zones_connected = map_info.zones_connected
        self.connections = map_info.connections
        self.start_zone = map_info.start_zone
        self.end_zone = map_info.end_zone
        self.scale = scale
        self.radius = self.scale * 0.25
        self.screen_space = screen_space
        self.colors: dict[str, tuple[int, int, int, int]] = {
            "blue": (0, 0, 255, 255), "green": (0, 255, 0, 255),
            "yellow": (255, 255, 0, 255), "orange": (255, 165, 0, 255),
            "cyan": (0, 255, 255, 255), "purple": (128, 0, 128, 255),
            "brown": (165, 42, 42, 255), "lime": (170, 255, 0, 255),
            "magenta": (255, 0, 255, 255), "gold": (255, 215, 0, 255),
            "black": (0, 0, 0, 255), "maroon": (128, 0, 0, 255),
            "darkred": (139, 0, 0, 255), "crimson": (220, 20, 60, 255),
            "violet": (238, 130, 238, 255), "rainbow": (120, 81, 169, 255),
            "red": (255, 0, 0, 255)}
        self.screen_info, self.zones_pixel = self.get_image_info()
        self.drones = [
                Drone(i + 1, self.zones_pixel[self.start_zone], solution[i])
                for i in range(map_info.nb_drones)]
        self.moves_num = 1000

    def get_image_info(self) -> tuple[dict[str, Any], dict[str, Any]]:

        screen_info, zones_info = dict(), dict()
        x_values = [zone.pos[0] for zone in self.zones.values()]
        y_values = [zone.pos[1] for zone in self.zones.values()]
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)

        for zone_name, zone in self.zones.items():
            x_pos, y_pos = zone.pos
            x_pixel = (self.screen_space + self.radius +
                       (x_pos - x_min) * self.scale)
            y_pixel = (self.screen_space + self.radius +
                       (y_max - y_pos) * self.scale)
            zones_info[zone_name] = (x_pixel, y_pixel)

        screen_info["width"] = round(2 * self.radius + (x_max - x_min) *
                                     self.scale + 2 * self.screen_space)
        screen_info["height"] = round(2 * self.radius + (y_max - y_min) *
                                      self.scale + 2 * self.screen_space)
        return ((screen_info, zones_info))

    def draw_background(self, screen_size: tuple[int, int]) -> pygame.Surface:

        background = pygame.Surface(screen_size)
        background.fill(pygame.Color(120, 120, 120))
        used_connections = []
        for zone_name, zone in self.zones.items():
            start = self.zones_pixel[zone_name]
            for dest_zone in self.zones_connected[zone_name]:
                connection = zone_name + "-" + dest_zone
                if connection not in self.connections.keys():
                    connection = dest_zone + "-" + zone_name
                if connection not in used_connections:
                    end = self.zones_pixel[dest_zone]
                    pygame.draw.line(
                        background, pygame.Color("black"), start, end, 3)
                    used_connections.append(connection)
            pygame.draw.circle(
                background, self.colors[zone.color], start, self.radius)
        return (background)

    def start_visuals(self, map_name: str) -> None:

        pygame.init()
        pygame.display.set_caption(f"Drone Simulation ({map_name})")
        screen = pygame.display.set_mode((
                self.screen_info["width"], self.screen_info["height"]))
        background = self.draw_background(screen.get_size())
        pygame.display.flip()

        running = True
        stop_animation = False
        count = 0
        turn_number = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        stop_animation = not stop_animation
            if not stop_animation:
                if not count % self.moves_num:
                    message = ""
                    running = False
                    for drone in self.drones:
                        if not drone.finished:
                            running = True
                            if drone.in_zone:
                                x_pos, y_pos = drone.position
                                drone.position = (round(x_pos), round(y_pos))
                            message += drone.prepare_next_move(
                                self.zones, self.zones_pixel, self.moves_num)
                    if turn_number:
                        time.sleep(1)
                    turn_number += 1
                    if message:
                        print(f"Turn {turn_number}:", message)
                screen.blit(background, (0, 0))
                for drone in self.drones:
                    drone.make_small_move()
                    pygame.draw.circle(
                        screen, pygame.Color("black"), drone.position, 10)
                pygame.display.flip()
                count += 1
