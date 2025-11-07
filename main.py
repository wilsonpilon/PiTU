import customtkinter as ctk
import sqlite3
import importlib
import os
from tkinter import messagebox

# Configurações do banco de dados
DATABASE_FILE = "app_config.db"

def create_config_db():
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()
    # Exemplo: pode expandir para novas opções ou utilitários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utility TEXT UNIQUE,
            options TEXT
        )
    """)
    con.commit()
    con.close()

def get_utility_config(utility_name):
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()
    cur.execute("SELECT options FROM configs WHERE utility = ?", (utility_name,))
    row = cur.fetchone()
    con.close()
    if row:
        return row[0]
    return ""

def set_utility_config(utility_name, options):
    con = sqlite3.connect(DATABASE_FILE)
    cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO configs (id, utility, options) VALUES ((SELECT id FROM configs WHERE utility = ?), ?, ?)", (utility_name, utility_name, options))
    con.commit()
    con.close()

# Função para execução dos utilitários
def run_utility(module_name):
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "main"):
            module.main()
        else:
            messagebox.showinfo("Erro", f"O utilitário '{module_name}' não possui uma função main()")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao executar o utilitário '{module_name}': {str(e)}")

def get_utilities():
    # Só "tamanho" por enquanto, mas pode expandir depois listando a pasta
    utils = []
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(utils_dir):
        if f.endswith(".py") and f not in ["main.py", "__init__.py"]:
            nome = f.replace(".py", "")
            utils.append(nome)
    return utils

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("pyTools Frontend")
        self.geometry("400x250")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.label_title = ctk.CTkLabel(self, text="Utilitários disponíveis", font=ctk.CTkFont(size=18, weight="bold"))
        self.label_title.pack(pady=(20,0))

        self.utility_option = ctk.StringVar(value="")
        self.utilities = get_utilities()
        self.optionmenu = ctk.CTkOptionMenu(self, variable=self.utility_option, values=self.utilities)
        self.optionmenu.pack(pady=10)

        self.btn_run = ctk.CTkButton(self, text="Executar utilitário", command=self.run_selected)
        self.btn_run.pack(pady=10)

        self.btn_options = ctk.CTkButton(self, text="Configurações", command=self.open_options)
        self.btn_options.pack(pady=5)

    def run_selected(self):
        utility = self.utility_option.get()
        if utility:
            run_utility(utility)
        else:
            messagebox.showinfo("Aviso", "Selecione um utilitário.")

    def open_options(self):
        utility = self.utility_option.get()
        if not utility:
            messagebox.showinfo("Aviso", "Selecione um utilitário para configurar.")
            return
        OptionsWindow(self, utility)

class OptionsWindow(ctk.CTkToplevel):
    def __init__(self, parent, utility_name):
        super().__init__(parent)
        self.title(f"Configurações - {utility_name}")
        self.geometry("350x180")
        self.utility_name = utility_name

        self.label = ctk.CTkLabel(self, text=f"Configurações para {utility_name}")
        self.label.pack(pady=10)

        prev_value = get_utility_config(utility_name)
        self.txt_options = ctk.CTkEntry(self, width=250)
        self.txt_options.insert(0, prev_value)
        self.txt_options.pack(pady=10)

        self.btn_save = ctk.CTkButton(self, text="Salvar", command=self.save)
        self.btn_save.pack(pady=10)

    def save(self):
        value = self.txt_options.get()
        set_utility_config(self.utility_name, value)
        messagebox.showinfo("Configuração", "Opções salvas com sucesso!")
        self.destroy()

if __name__ == "__main__":
    create_config_db()
    app = App()
    app.mainloop()