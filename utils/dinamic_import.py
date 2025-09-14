import importlib
import inspect
import os
import sys


def plugins_import(dir_plugins):
    imported_plugins = {}
    sys.path.insert(0, os.path.dirname(__file__))

    for file_name in os.listdir(dir_plugins):
        if file_name.endswith(".py") and file_name != "__init__.py":
            module_name = f"{os.path.basename(dir_plugins)}.{file_name[:-3]}"

            try:
                module = importlib.import_module(module_name)

                for _, module_type in inspect.getmembers(module, inspect.isclass):
                    if module_type.__module__ == module_name:
                        imported_plugins[module_name.split(".")[-1]] = module_type

            except ImportError as e:
                print(f"Error importing module {module_name}: {e}")

    return imported_plugins
