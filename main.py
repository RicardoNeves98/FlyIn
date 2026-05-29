from argparse import ArgumentParser
from parsing import ParsingFile, Zone, Connection, Map
from algorithm import Algorithm

def main() -> None:

    arg_parser = ArgumentParser()
    arg_parser.add_argument("map_config")
    args = arg_parser.parse_args()
    parsing_file = ParsingFile(args.map_config)
    
    parsing_file.check_args()
    map_dict = parsing_file.create_map_dict()
    drone_map = Map(**map_dict)

#    algorithm = Algorithm(drone_map)
#    move_dict = algorithm.explore_zones(drone_map["start_zone"])
#    best_move_reverse = [drone_map["end_zone"]]
#    while best_move_reverse[-1] != drone_map["start_zone"]:
#        next_zone = move_dict[best_move_reverse[-1]]
#        best_move_reverse.append(next_move)

if __name__ == "__main__":
    main()
