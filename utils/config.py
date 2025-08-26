import os
from datetime import datetime

import yaml


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
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        config_path = os.path.join(self.config_dir, f"{self.config_type}.yaml")

        if os.path.isfile(config_path):
            with open(config_path) as yaml_file:
                print(f"Loading from: {config_path}")
                self.data = yaml.load(yaml_file, Loader=yaml.SafeLoader)
        else:
            print(f"No existing {self.config_type} file found. Using default settings.")
            self.save_config()

    def save_config(self):
        config_path = os.path.join(self.config_dir, f"{self.config_type}.yaml")
        with open(config_path, "w") as yaml_file:
            yaml.dump(self.data, yaml_file)

    def backup_and_update_config(self):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        backup_path = os.path.join(
            self.config_dir, f"{self.config_type}_{timestamp}.yaml"
        )

        original_path = os.path.join(self.config_dir, f"{self.config_type}.yaml")
        if os.path.exists(original_path):
            os.rename(original_path, backup_path)

        self.save_config()


if __name__ == "__main__":
    config = YamlConfig("config")
    color_config = YamlConfig("color")

    config.read_config()
    color_config.read_config()

    print(config.data)
    print(color_config.data)
