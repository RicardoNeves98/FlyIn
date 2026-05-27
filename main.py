from argparse import ArgumentParser
from parsing import MapCreater, Zone, Connection, Map


def main() -> None:

    arg_parser = ArgumentParser()
    arg_parser.add_argument("map_config")
    args = arg_parser.parse_args()
    map_creater = MapCreater(args.map_config)
    try:
        map_creater.check_args()
        map_dict = map_creater.create_map_dict()
        drone_map = map_creater.create_map(map_dict)
    except Exception as message:
        print(message)


if __name__ == "__main__":
    main()
