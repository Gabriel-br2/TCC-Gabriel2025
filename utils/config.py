import os
import yaml
from datetime import datetime

class ConfigYaml:
    def __init__(self, data, path = '~/Documents/class/TCC-Gabriel2025/config'):
        # Default config File
        self.path = os.path.expanduser(path)
        self.dataType = data

        config =   {'screen': {
                        'height'     : 600,
                        'width'      : 800,
                        'caption'    : "Projeto de TCC - Gabriel"
                        }
                    }
        
        color =    {"background" : [255, 255, 255],
                        "white"  : [255, 255, 255],
                        "red"    : [255, 0, 0],
                        "green"  : [0, 255, 0],
                        "blue"   : [0, 0, 255]}

        if data == "config": self.data = config
        elif data == "color": self.data = color

    def read_config(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        if os.path.isfile(self.path + f'/{self.dataType}.yaml'):
            with open(self.path + f'/{self.dataType}.yaml','r') as yfile:

                print(self.path + f'/{self.dataType}.yaml')
                data = yaml.load(yfile, Loader=yaml.loader.SafeLoader)         
            self.data = data

        else:
            print(f'No {self.dataType} file. Loading default.')
            with open(self.path + f'/{self.dataType}.yaml','w') as yfile:
                yaml.dump(self.data, yfile) 

    def update_config(self):
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        os.rename(self.path + f'/{self.dataType}.yaml',f'config/{self.dataType}_%s.yaml'%timestamp)
        with open(self.path + f'/{self.dataType}.yaml','w') as yfile:
            yaml.dump(self.data,yfile)

if __name__ == "__main__":
    cfg   = ConfigYaml("config")
    color = ConfigYaml("color")

    cfg.read_config()
    color.read_config()

    print(cfg.data)
    print(color.data)