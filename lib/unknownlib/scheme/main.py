from .element import *
from . import log
from argparse import ArgumentParser
import yaml

parser = ArgumentParser()
parser.add_argument("cfg_file")


def main():
    
    args = parser.parse_args()
    cfg_file = args.cfg_file
    log.info(f"parsing {cfg_file}")
    with open(cfg_file, "r") as f:
        config = yaml.safe_load(f)

    manager = ElementManager()
    for name, params in config.items():
        manager.create_element(name, params)

    manager.init_elements()
        
    scheduler = manager.get_element_by_type(Scheduler)
    for time_ in scheduler.schedule():
        manager.calc_elements(time_)

    manager.done_elements()

        
if __name__ == "__main__":

    main()