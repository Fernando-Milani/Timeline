import os

# Lista de arquivos a serem lidos
arquivos = [
    "pages/index.html",
    "pages/style.css",
    "pages/script.js",
    "tools/event_manager.py",
    "tools/periods_manager.py",
    "tools/validate_data.py"
]

# Nome do arquivo de saída
arquivo_saida = "saida.txt"

with open(arquivo_saida, "w", encoding="utf-8") as saida:
    for caminho in arquivos:
        if os.path.exists(caminho):
            saida.write(f"Nome do arquivo: {caminho}\n")
            saida.write("-" * 40 + "\n")
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
                saida.write(conteudo + "\n")
            saida.write("\n\n")  # Separador entre arquivos
        else:
            saida.write(f"Nome do arquivo: {caminho}\n")
            saida.write("Arquivo não encontrado.\n\n")

print(f"Conteúdo dos arquivos foi salvo em '{arquivo_saida}'.")