from argparse import ArgumentParser
from parsing import ParsingFile, Zone, Connection, Map
from algorithm import Algorithm

def main() -> None:

    arg_parser = ArgumentParser()
    arg_parser.add_argument("map_config")
    args = arg_parser.parse_args()
    parsing_file = ParsingFile(args.map_config)

    try:
        parsing_file.check_args()
        map_dict = parsing_file.create_map_dict()
        drone_map = Map(**map_dict)
    except Exception as message:
        print(message)

    algorithm = Algorithm(drone_map)
    print(algorithm.explore_zones(algorithm.start_zone))

if __name__ == "__main__":
    main()
