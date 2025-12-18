import importlib
import inspect
import os
import sys

def plugins_import(dir_plugins_name):
    imported_plugins = {}
    
    # 1. Determina onde estamos rodando
    if getattr(sys, 'frozen', False):
        # Se for EXE, estamos na pasta temporária _MEIPASS
        base_path = os.path.dirname(sys.executable)#sys._MEIPASS
        # Mas queremos permitir plugins externos? 
        # Se você usou a solução do passo 1 (congelados), use sys._MEIPASS.
        # Se quer plugins editáveis externos, use os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    # Monta o caminho completo da pasta de plugins
    plugin_path = os.path.join(base_path, dir_plugins_name)
    
    # Verifica se a pasta existe
    print(plugin_path)
    if not os.path.exists(plugin_path):
        print(f"AVISO: Pasta de plugins não encontrada em {plugin_path}")
        return {}

    # Adiciona o diretório PAI ao sys.path para que o import funcione
    # Ex: se o plugin é 'plugins.meu_plugin', precisamos que a pasta onde 'plugins' está seja visível
    sys.path.insert(0, base_path) 

    print(f"Carregando plugins de: {plugin_path}")

    for file_name in os.listdir(plugin_path):
        if file_name.endswith(".py") and file_name != "__init__.py":
            # Constrói o nome do módulo: ex "plugins.meu_agente"
            # Importante: dir_plugins_name deve ser o nome do pacote python (ex: "plugins")
            module_name = f"{dir_plugins_name}.{file_name[:-3]}"

            try:
                # Tenta importar
                module = importlib.import_module(module_name)

                for _, module_type in inspect.getmembers(module, inspect.isclass):
                    # Verifica se a classe foi definida NESSE arquivo (evita importar classes importadas)
                    if module_type.__module__ == module_name:
                        print(f"Plugin carregado: {module_name}")
                        imported_plugins[module_name.split(".")[-1]] = module_type

            except ImportError as e:
                print(f"ERRO ao importar plugin {module_name}: {e}")
            except Exception as e:
                print(f"ERRO genérico no plugin {module_name}: {e}")

    return imported_plugins