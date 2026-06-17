from argparse import ArgumentParser
from parsing import ParsingFile, Map
from algorithm import Algorithm
from visuals import Animation
from pydantic import ValidationError


def main() -> None:

    arg_parser = ArgumentParser()
    arg_parser.add_argument("map_config")
    args = arg_parser.parse_args()
    parsing_file = ParsingFile(args.map_config)

    try:
        parsing_file.check_args()
        map_dict = parsing_file.create_map_dict()
        map_info = Map(**map_dict)
    except ValidationError as e:
        for error in e.errors():
            print(f"[ERROR] {error['msg']}")
    except ValueError as message:
        print(message)

    algorithm = Algorithm(map_info)
    solution = algorithm.get_fleet_solution()
    animation = Animation(map_info, 200, 50, solution)
    animation.start_visuals(args.map_config)


if __name__ == "__main__":
    main()
