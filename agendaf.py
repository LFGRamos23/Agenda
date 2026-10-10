import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button, messagebox
from tkcalendar import Calendar
import json
from datetime import datetime
import os
import pystray
from PIL import Image, ImageDraw


# ==========================================================
# ARQUIVO ONDE AS TAREFAS SERÃO SALVAS
# ==========================================================

# No Windows, salva os dados dentro da pasta APPDATA.
if os.getenv("APPDATA"):
    PASTA_DADOS = os.path.join(os.getenv("APPDATA"), "AgendaInteligente")
else:
    PASTA_DADOS = os.path.join(os.path.expanduser("~"), ".agenda_inteligente")

os.makedirs(PASTA_DADOS, exist_ok=True)
ARQUIVO = os.path.join(PASTA_DADOS, "tarefas.json")


# ==========================================================
# CARREGAR E SALVAR TAREFAS
# ==========================================================

def carregar_tarefas():
    """Carrega as tarefas armazenadas no arquivo JSON."""
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def salvar_tarefas(tarefas):
    """Salva todas as tarefas no arquivo JSON."""
    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(tarefas, arquivo, indent=4, ensure_ascii=False)


# ==========================================================
# POP-UP DE LEMBRETE
# ==========================================================

def mostrar_popup(root, titulo, mensagem):
    """Mostra uma janela de lembrete na frente das outras janelas."""
    popup = Toplevel(root)
    popup.title("Lembrete")
    popup.geometry("360x180")

    Label(popup, text=titulo, font=("Arial", 14, "bold")).pack(pady=10)
    Label(popup, text=mensagem, font=("Arial", 11), wraplength=320).pack(pady=10)
    Button(popup, text="OK", command=popup.destroy, width=10).pack(pady=10)

    # Coloca temporariamente o aviso na frente de outras janelas.
    popup.lift()
    popup.attributes("-topmost", True)
    popup.after(1000, lambda: popup.attributes("-topmost", False))
    popup.bell()


# ==========================================================
# ÍCONE DA BANDEJA DO WINDOWS
# ==========================================================

def criar_icone():
    """Cria um ícone simples de agenda para a bandeja do sistema."""
    imagem = Image.new("RGB", (64, 64), "white")
    desenho = ImageDraw.Draw(imagem)

    desenho.rectangle((12, 10, 52, 54), outline="black", width=4)
    desenho.line((20, 22, 44, 22), fill="black", width=3)
    desenho.line((20, 32, 44, 32), fill="black", width=3)
    desenho.line((20, 42, 38, 42), fill="black", width=3)

    return imagem


# ==========================================================
# CLASSE PRINCIPAL
# ==========================================================

class AgendaApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Agenda Inteligente")
        self.root.geometry("450x520")

        # Clicar no X minimiza a aplicação em vez de encerrá-la.
        self.root.protocol("WM_DELETE_WINDOW", self.minimizar_para_bandeja)

        # Título da aplicação.
        Label(root, text="Agenda Inteligente",
              font=("Arial", 18, "bold")).pack(pady=10)

        Label(root, text="Organize suas tarefas e compromissos",
              font=("Arial", 10)).pack()

        # Calendário principal.
        self.cal = Calendar(
            root,
            selectmode="day",
            date_pattern="dd/mm/yyyy"
        )
        self.cal.pack(pady=20)

        # Cor usada nos dias que possuem tarefas.
        self.cal.tag_config(
            "tarefa",
            background="lightblue",
            foreground="black"
        )

        # Botões principais.
        Button(
            root,
            text="Adicionar tarefa",
            command=self.adicionar,
            width=25
        ).pack(pady=5)

        Button(
            root,
            text="Ver tarefas do dia",
            command=self.ver_tarefas,
            width=25
        ).pack(pady=5)

        Button(
            root,
            text="Minimizar para bandeja",
            command=self.minimizar_para_bandeja,
            width=25
        ).pack(pady=5)

        # Mostra um pequeno resumo das tarefas.
        self.label_resumo = Label(root, text="", font=("Arial", 10, "bold"))
        self.label_resumo.pack(pady=15)

        self.tray_icon = None

        # Inicializações.
        self.iniciar_bandeja()
        self.atualizar_marcacoes()
        self.atualizar_resumo()
        self.checar_alertas()


    # ======================================================
    # BANDEJA DO SISTEMA
    # ======================================================

    def iniciar_bandeja(self):
        """Cria o ícone e o menu da bandeja."""

        menu = pystray.Menu(
            pystray.MenuItem(
                "Abrir agenda",
                self.abrir_pela_bandeja,
                default=True
            ),
            pystray.MenuItem(
                "Sair",
                self.sair_pela_bandeja
            )
        )

        self.tray_icon = pystray.Icon(
            "AgendaInteligente",
            criar_icone(),
            "Agenda Inteligente",
            menu
        )

        self.tray_icon.run_detached()


    def abrir_pela_bandeja(self, icon, item):
        """Abre a janela através do ícone da bandeja."""
        self.root.after(0, self.mostrar_janela)


    def mostrar_janela(self):
        """Exibe novamente a janela principal."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()


    def minimizar_para_bandeja(self):
        """Esconde a janela, mas mantém o programa funcionando."""
        self.root.withdraw()


    def sair_pela_bandeja(self, icon, item):
        """Encerra completamente o aplicativo."""
        icon.stop()
        self.root.after(0, self.root.destroy)


    # ======================================================
    # ADICIONAR TAREFA
    # ======================================================

    def adicionar(self):
        """Abre uma janela para cadastrar uma nova tarefa."""

        data = self.cal.get_date()

        janela = Toplevel(self.root)
        janela.title(f"Adicionar tarefa - {data}")
        janela.geometry("350x250")

        Label(janela, text="Descrição:").pack(pady=5)

        entrada_texto = Entry(janela, width=35)
        entrada_texto.pack()

        Label(janela, text="Horário:").pack(pady=10)

        # Campos separados para hora e minuto.
        frame_hora = tk.Frame(janela)
        frame_hora.pack()

        entrada_hora_hh = Entry(frame_hora, width=3, justify="center")
        entrada_hora_hh.pack(side="left")

        Label(frame_hora, text=":").pack(side="left")

        entrada_hora_mm = Entry(frame_hora, width=3, justify="center")
        entrada_hora_mm.pack(side="left")


        def salvar():
            """Valida os campos e salva a nova tarefa."""

            texto = entrada_texto.get().strip()
            hh = entrada_hora_hh.get().strip()
            mm = entrada_hora_mm.get().strip()

            # Impede campos vazios.
            if texto == "" or hh == "" or mm == "":
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return

            # Validação do horário digitado.
            try:
                hora = f"{int(hh):02d}:{int(mm):02d}"
                datetime.strptime(hora, "%H:%M")
            except ValueError:
                messagebox.showerror(
                    "Erro",
                    "Horário inválido!\nUse 00–23 para hora e 00–59 para minutos."
                )
                return

            tarefas = carregar_tarefas()

            # Cria uma lista para a data caso ainda não exista.
            if data not in tarefas:
                tarefas[data] = []

            tarefas[data].append({
                "texto": texto,
                "horario": f"{data} {hora}",
                "notificado": False,
                "concluida": False
            })

            salvar_tarefas(tarefas)
            self.atualizar_marcacoes()
            self.atualizar_resumo()

            messagebox.showinfo("Agenda", "Tarefa salva com sucesso!")
            janela.destroy()


        Button(
            janela,
            text="Salvar",
            command=salvar,
            width=15
        ).pack(pady=20)


    # ======================================================
    # VER TAREFAS DO DIA
    # ======================================================

    def ver_tarefas(self):
        """Mostra todas as tarefas cadastradas para o dia escolhido."""

        data = self.cal.get_date()
        tarefas = carregar_tarefas()

        janela = Toplevel(self.root)
        janela.title(f"Tarefas de {data}")
        janela.geometry("500x400")

        lista = tarefas.get(data, [])

        if len(lista) == 0:
            Label(
                janela,
                text="Nenhuma tarefa para este dia."
            ).pack(pady=20)
            return

        for indice, tarefa in enumerate(lista):

            # Cada tarefa fica dentro de seu próprio frame.
            frame = tk.Frame(
                janela,
                bd=1,
                relief="solid",
                padx=10,
                pady=8
            )
            frame.pack(fill="x", padx=10, pady=5)

            if tarefa.get("concluida", False):
                status = "CONCLUÍDA"
            else:
                status = "PENDENTE"

            Label(
                frame,
                text=tarefa["texto"],
                font=("Arial", 11, "bold")
            ).pack(anchor="w")

            Label(
                frame,
                text=f"{tarefa['horario']} | {status}"
            ).pack(anchor="w")

            frame_botoes = tk.Frame(frame)
            frame_botoes.pack(anchor="w", pady=5)

            # Tarefas já concluídas não precisam do botão Concluir.
            if not tarefa.get("concluida", False):

                Button(
                    frame_botoes,
                    text="Concluir",
                    command=lambda i=indice:
                    self.concluir_tarefa(data, i, janela)
                ).pack(side="left", padx=2)

            Button(
                frame_botoes,
                text="Excluir",
                command=lambda i=indice:
                self.excluir_tarefa(data, i, janela)
            ).pack(side="left", padx=2)


    # ======================================================
    # CONCLUIR TAREFA
    # ======================================================

    def concluir_tarefa(self, data, indice, janela):
        """Marca uma tarefa como concluída."""

        tarefas = carregar_tarefas()

        if data in tarefas:
            if indice < len(tarefas[data]):
                tarefas[data][indice]["concluida"] = True
                salvar_tarefas(tarefas)

        self.atualizar_marcacoes()
        self.atualizar_resumo()

        janela.destroy()
        self.ver_tarefas()


    # ======================================================
    # EXCLUIR TAREFA
    # ======================================================

    def excluir_tarefa(self, data, indice, janela):
        """Exclui uma tarefa depois da confirmação do usuário."""

        resposta = messagebox.askyesno(
            "Excluir",
            "Deseja realmente excluir esta tarefa?",
            parent=janela
        )

        if not resposta:
            return

        tarefas = carregar_tarefas()

        if data in tarefas:

            if indice < len(tarefas[data]):
                tarefas[data].pop(indice)

            # Remove a data caso ela fique sem nenhuma tarefa.
            if len(tarefas[data]) == 0:
                del tarefas[data]

        salvar_tarefas(tarefas)

        self.atualizar_marcacoes()
        self.atualizar_resumo()

        janela.destroy()
        self.ver_tarefas()


    # ======================================================
    # MARCAÇÕES NO CALENDÁRIO
    # ======================================================

    def atualizar_marcacoes(self):
        """Destaca no calendário os dias com tarefas pendentes."""

        self.cal.calevent_remove("all")
        tarefas = carregar_tarefas()

        for data in tarefas:

            lista_pendentes = []

            for tarefa in tarefas[data]:
                if not tarefa.get("concluida", False):
                    lista_pendentes.append(tarefa)

            if len(lista_pendentes) == 0:
                continue

            try:
                data_objeto = datetime.strptime(
                    data,
                    "%d/%m/%Y"
                ).date()
            except ValueError:
                continue

            texto_evento = ""

            for tarefa in lista_pendentes:
                horario = tarefa["horario"][-5:]

                texto_evento += (
                    horario
                    + " - "
                    + tarefa["texto"]
                    + "\n"
                )

            self.cal.calevent_create(
                data_objeto,
                texto_evento,
                "tarefa"
            )


    # ======================================================
    # RESUMO DAS TAREFAS
    # ======================================================

    def atualizar_resumo(self):
        """Conta quantas tarefas pendentes existem."""

        tarefas = carregar_tarefas()

        total_pendentes = 0
        tarefas_hoje = 0

        hoje = datetime.now().strftime("%d/%m/%Y")

        for data in tarefas:

            for tarefa in tarefas[data]:

                if not tarefa.get("concluida", False):

                    total_pendentes += 1

                    if data == hoje:
                        tarefas_hoje += 1

        self.label_resumo.config(
            text=(
                f"Tarefas pendentes: {total_pendentes}\n"
                f"Tarefas de hoje: {tarefas_hoje}"
            )
        )


    # ======================================================
    # NOTIFICAÇÕES
    # ======================================================

    def notificar_tarefa(self, tarefa):
        """Envia notificação do sistema e também abre o pop-up."""

        mensagem = (
            tarefa["texto"]
            + "\nHorário: "
            + tarefa["horario"]
        )

        # Notificação nativa do sistema operacional.
        try:
            if self.tray_icon and self.tray_icon.HAS_NOTIFICATION:
                self.tray_icon.notify(
                    mensagem,
                    "Agenda Inteligente"
                )
        except Exception:
            pass

        # Pop-up interno do programa.
        mostrar_popup(
            self.root,
            "Lembrete!",
            mensagem
        )


    # ======================================================
    # VERIFICAÇÃO DOS ALERTAS
    # ======================================================

    def checar_alertas(self):
        """Verifica periodicamente se chegou o horário de alguma tarefa."""

        tarefas = carregar_tarefas()
        agora = datetime.now()
        alterou = False

        for data in tarefas:

            for tarefa in tarefas[data]:

                # Ignora tarefas concluídas.
                if tarefa.get("concluida", False):
                    continue

                # Impede a mesma notificação de aparecer novamente.
                if tarefa.get("notificado", False):
                    continue

                try:
                    horario_tarefa = datetime.strptime(
                        tarefa["horario"],
                        "%d/%m/%Y %H:%M"
                    )
                except ValueError:
                    continue

                # Se o horário chegou ou passou, envia o lembrete.
                if horario_tarefa <= agora:

                    self.notificar_tarefa(tarefa)
                    tarefa["notificado"] = True
                    alterou = True

        if alterou:
            salvar_tarefas(tarefas)

        self.atualizar_resumo()

        # Executa esta função novamente depois de 15 segundos.
        self.root.after(15000, self.checar_alertas)


# ==========================================================
# INICIAR O PROGRAMA
# ==========================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AgendaApp(root)
    root.mainloop()