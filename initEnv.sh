#!/bin/bash
# Navega até o diretório do projeto
cd "$(dirname "$0")"

# Ativa o ambiente virtual
echo "Ambiente virtual ativado!"
source ~/envs/TCC/bin/activate

cd "$(dirname "$0")"

echo "Instalando Dependencias"
pip install -r requirements.txt

echo "Ambiente Pronto para uso"