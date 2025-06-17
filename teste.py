import os


def listar_arquivos(diretorio):
    return [f.split(".")[0] for f in os.listdir(diretorio)]


# Exemplo de uso:
diretorio = "objects"
print(listar_arquivos(diretorio))
