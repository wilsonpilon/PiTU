import os
import sqlite3
import customtkinter as ctk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from concurrent.futures import ThreadPoolExecutor
import matplotlib

# Configuração do tema CustomTkinter
ctk.set_appearance_mode("dark")  # "light" ou "dark"
ctk.set_default_color_theme("blue")  # Pode ser "green", "dark-blue", etc.

DB_FILE = "tamanhos.db"

def inicializar_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS subdirs")
    cur.execute("""
        CREATE TABLE subdirs (
            nome TEXT,
            tamanho INTEGER
        )
    """)
    conn.commit()
    conn.close()

def salvar_resultados_em_lote(dados):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.executemany("INSERT INTO subdirs (nome, tamanho) VALUES (?, ?)", dados)
    conn.commit()
    conn.close()

def obter_resultados():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT nome, tamanho FROM subdirs ORDER BY tamanho DESC")
    resultados = cur.fetchall()
    conn.close()
    return resultados

def formatar_tamanho(bytes):
    for unidade in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unidade}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def calcular_tamanho_subdir(caminho):
    tamanho = 0
    try:
        for raiz, _, arquivos in os.walk(caminho):
            for arquivo in arquivos:
                try:
                    tamanho += os.path.getsize(os.path.join(raiz, arquivo))
                except FileNotFoundError:
                    pass
    except PermissionError:
        pass
    return tamanho

def calcular_tamanhos():
    for item in lista.get_children():
        lista.delete(item)
    label_total.configure(text="")
    for widget in frame_grafico.winfo_children():
        widget.destroy()

    diretorio = filedialog.askdirectory(title="Selecione um diretório")
    if not diretorio:
        return

    inicializar_db()

    subdirs = [item for item in os.listdir(diretorio) if os.path.isdir(os.path.join(diretorio, item))]
    total = len(subdirs)

    barra.configure(maximum=total, value=0)

    tamanho_total = 0
    resultados_temp = []

    # Processamento paralelo
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futuros = {executor.submit(calcular_tamanho_subdir, os.path.join(diretorio, item)): item for item in subdirs}
        for i, futuro in enumerate(futuros, start=1):
            tamanho = futuro.result()
            nome = futuros[futuro]
            resultados_temp.append((nome, tamanho))
            tamanho_total += tamanho

            if i % 10 == 0 or i == total:
                barra.configure(value=i)
                janela.update_idletasks()

    salvar_resultados_em_lote(resultados_temp)

    resultados = obter_resultados()
    for nome, tamanho in resultados:
        lista.insert("", "end", values=(nome, formatar_tamanho(tamanho)))

    label_total.configure(text=f"Tamanho total: {formatar_tamanho(tamanho_total)}")

    # Prepara dados para gráfico (top 10 + Outros)
    top10 = resultados[:10]
    outros = resultados[10:]
    soma_outros = sum([r[1] for r in outros]) if outros else 0

    nomes = [r[0] for r in top10]
    tamanhos = [r[1] / (1024*1024) for r in top10]  # MB
    if soma_outros > 0:
        nomes.append("Outros")
        tamanhos.append(soma_outros / (1024*1024))

    if tamanhos:
        cmap = matplotlib.colormaps.get_cmap("coolwarm")
        norm = plt.Normalize(min(tamanhos), max(tamanhos))
        cores = [cmap(norm(valor)) for valor in tamanhos]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(nomes, tamanhos, color=cores)
        ax.set_xlabel("Tamanho (MB)")
        ax.set_title("Top 10 Subdiretórios + Outros")
        ax.invert_yaxis()

        for i, v in enumerate(tamanhos):
            ax.text(v + 1, i, f"{v:.2f} MB", va='center', fontsize=8)

        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

# Interface com CustomTkinter
janela = ctk.CTk()
janela.title("Calculador de Tamanho de Subdiretórios (CustomTkinter)")
janela.geometry("800x750")

botao = ctk.CTkButton(janela, text="Selecionar Diretório", command=calcular_tamanhos)
botao.pack(pady=10)

barra = ttk.Progressbar(janela, orient="horizontal", length=400, mode="determinate")
barra.pack(pady=10)

# Tabela (Treeview ainda é do ttk)
colunas = ("Subdiretório", "Tamanho")
lista = ttk.Treeview(janela, columns=colunas, show="headings", height=10)
lista.heading("Subdiretório", text="Subdiretório")
lista.heading("Tamanho", text="Tamanho")
lista.pack(expand=True, fill="both", padx=10, pady=10)

label_total = ctk.CTkLabel(janela, text="", font=("Arial", 16))
label_total.pack(pady=10)

frame_grafico = ctk.CTkFrame(janela)
frame_grafico.pack(expand=True, fill="both", padx=10, pady=10)

janela.mainloop()
