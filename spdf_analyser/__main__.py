from pathlib import Path
from sys import argv, modules

from .analysis.analyse import analyse


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"Invalid parameters given. Try \"py -m {modules[__name__].__spec__.name} <filepath> [<config_filepath>] [<output_filepath>]\"")
        exit()

    path = Path(argv[1])
    if not path.exists():
        print(f"Invalid path given (\"{path.absolute()}\"). Try a valid path")
        exit()
    
    config_path = None
    if len(argv) > 2:
        config_path = Path(argv[2])
        
        if not config_path.exists():
            print(f"Invalid config path given (\"{path.absolute()}\"). Try a valid config path")
            exit()
    
    output_path = None
    if len(argv) > 3:
        output_path = Path(argv[3])

    analyse(path, config_path, output_path)