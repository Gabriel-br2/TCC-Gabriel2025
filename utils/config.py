import os
import sys
from datetime import datetime

import yaml

# https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class YamlConfig:
    def __init__(self, config_type, config_dir="config"):
        self.config_dir = os.path.expanduser(config_dir)
        self.config_type = config_type

        # Default configurations for different config types.
        default_configs = {
            "config": {
                "screen": {
                    "height": 600,
                    "width": 800,
                    "caption": "Projeto de TCC - Gabriel",
                }
            },
            "color": {
                "background": [255, 255, 255],
                "white": [255, 255, 255],
                "red": [255, 0, 0],
                "green": [0, 255, 0],
                "blue": [0, 0, 255],
            },
        }

        self.data = default_configs.get(
            config_type, {}
        )  # Load default config or empty dict if not found

    def read_config(self):
        #if not os.path.exists(self.config_dir):
        #    os.makedirs(self.config_dir)

        config_path = resource_path(os.path.join(self.config_dir, f"{self.config_type}.yaml"))

        with open(config_path) as yaml_file:
            print(f"Loading from: {config_path}")
            self.data = yaml.load(yaml_file, Loader=yaml.SafeLoader)

if __name__ == "__main__":
    config = YamlConfig("config")
    color_config = YamlConfig("color")

    config.read_config()
    color_config.read_config()

    print(config.data)
    print(color_config.data)
