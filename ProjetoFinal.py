import cv2
import numpy as np
import pyautogui
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import random

# ==========================================
# VARIÁVEIS GLOBAIS
# ==========================================
LARGURA_ECRA, ALTURA_ECRA = pyautogui.size()
camara = cv2.VideoCapture(0)

# Estado do Jogo
pokedex = [] # Agora vai guardar dicionários: {"nome": "Pikachu", "imagem": foto}
nome_pokemon_atual = ""
imagem_pequena = None
imagem_grande = None
timer_fuga = None
janela_captura = None
em_modo_captura = False

# ==========================================
# FASE 1: O MAPA E A POKÉDEX
# ==========================================
def abrir_pokedex():
    """Abre a Pokédex e mostra as imagens e nomes dos capturados."""
    janela_dex = tk.Toplevel(janela)
    janela_dex.title("Pokédex")
    janela_dex.geometry("350x500")
    janela_dex.configure(bg="#DC0A2D") # Cor vermelha da Pokédex
    
    tk.Label(janela_dex, text="Pokédex - Coleção", font=("Arial", 16, "bold"), bg="#DC0A2D", fg="white").pack(pady=10)
    
    # TRUQUE MÁGICO: Usar um widget Text para poder fazer Scroll facilmente com imagens!
    caixa_galeria = tk.Text(janela_dex, font=("Arial", 14, "bold"), bg="white", cursor="arrow")
    caixa_galeria.pack(padx=10, pady=10, expand=True, fill="both")
    
    if len(pokedex) == 0:
        caixa_galeria.insert(tk.END, "\n Ainda não apanhaste nenhum Pokémon...")
    else:
        for pokemon in pokedex:
            # 1. Inserir a imagem pequena na caixa
            caixa_galeria.image_create(tk.END, image=pokemon["imagem"])
            # 2. Escrever o nome à frente da imagem e dar um parágrafo
            caixa_galeria.insert(tk.END, f"  {pokemon['nome']}\n\n")
            
    # Bloquear a caixa de texto para o utilizador não conseguir apagar os Pokémons escrevendo por cima!
    caixa_galeria.config(state="disabled")

def procurar_novo_pokemon():
    """Procura um Pokémon aleatório e coloca-o no mapa principal."""
    global nome_pokemon_atual, imagem_pequena, imagem_grande, timer_fuga
    
    if timer_fuga is not None:
        janela.after_cancel(timer_fuga)

    btn_pokemon_mapa.place_forget()
    label_status.config(text="A procurar Pokémon na relva alta...")
    janela.update()

    id_poke = random.randint(1, 151)
    
    try:
        resposta = requests.get(f"https://pokeapi.co/api/v2/pokemon/{id_poke}")
        dados = resposta.json()
        nome_pokemon_atual = dados["name"].capitalize()
        
        # Imagem Pequena
        url_pequena = dados["sprites"]["front_default"]
        resp_peq = requests.get(url_pequena)
        img_peq = Image.open(BytesIO(resp_peq.content)).resize((100, 100))
        imagem_pequena = ImageTk.PhotoImage(img_peq)
        
        # Imagem Gigante HD
        url_grande = dados["sprites"]["other"]["official-artwork"]["front_default"]
        resp_grd = requests.get(url_grande)
        img_grd = Image.open(BytesIO(resp_grd.content)).resize((400, 400))
        imagem_grande = ImageTk.PhotoImage(img_grd)
        
        btn_pokemon_mapa.config(image=imagem_pequena, text=nome_pokemon_atual, compound="top")
        
        novo_x = random.randint(50, 600)
        novo_y = random.randint(150, 450)
        btn_pokemon_mapa.place(x=novo_x, y=novo_y)
        
        label_status.config(text=f"Um {nome_pokemon_atual} selvagem apareceu! Clica nele!")
        timer_fuga = janela.after(10000, pokemon_fugiu)
        
    except:
        label_status.config(text="Erro de Internet. A tentar novamente...")
        janela.after(2000, procurar_novo_pokemon)

def pokemon_fugiu():
    btn_pokemon_mapa.place_forget()
    label_status.config(text=f"Oh não! O {nome_pokemon_atual} fugiu!")
    janela.after(3000, procurar_novo_pokemon)

# ==========================================
# FASE 2: O ECRÃ DE CAPTURA (FULLSCREEN)
# ==========================================
def iniciar_captura():
    global janela_captura, em_modo_captura
    
    if timer_fuga is not None:
        janela.after_cancel(timer_fuga)
        
    em_modo_captura = True
    
    janela_captura = tk.Toplevel(janela)
    janela_captura.attributes('-fullscreen', True)
    janela_captura.configure(bg="#228B22")
    
    tk.Label(janela_captura, text=f"Apanha o {nome_pokemon_atual}!", font=("Arial", 30, "bold"), bg="#228B22", fg="white").pack(pady=20)
    
    label_imagem_hd = tk.Label(janela_captura, image=imagem_grande, bg="#228B22")
    label_imagem_hd.pack(expand=True)
    
    btn_fugir = tk.Button(janela_captura, text="🏃 Fugir da Batalha", font=("Arial", 16), bg="white", command=sair_da_captura)
    btn_fugir.pack(side="bottom", pady=50)
    
    rastrear_bola_captura()

def sair_da_captura():
    global em_modo_captura
    em_modo_captura = False
    janela_captura.destroy()
    procurar_novo_pokemon()

def capturou_com_sucesso():
    global em_modo_captura
    em_modo_captura = False
    
    # TRUQUE: Guardar o Nome e a Imagem Pequena num Dicionário!
    novo_registo = {
        "nome": nome_pokemon_atual,
        "imagem": imagem_pequena
    }
    pokedex.append(novo_registo)
    
    messagebox.showinfo("CAPTURA!", f"Lançamento Perfeito!\nApanhaste o {nome_pokemon_atual}!")
    label_pokedex.config(text=f"Total: {len(pokedex)} apanhados")
    
    janela_captura.destroy()
    procurar_novo_pokemon()

# ==========================================
# FASE 3: A VISÃO COMPUTACIONAL
# ==========================================
def rastrear_bola_captura():
    if not em_modo_captura:
        return 
        
    sucesso, frame = camara.read()
    if sucesso:
        frame = cv2.flip(frame, 1)
        altura_cam, largura_cam, _ = frame.shape
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mascara1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
        mascara2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
        mascara = mascara1 + mascara2

        contornos, _ = cv2.findContours(mascara, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contornos:
            maior_contorno = max(contornos, key=cv2.contourArea)
            area = cv2.contourArea(maior_contorno)

            if area > 500:
                momentos = cv2.moments(maior_contorno)
                if momentos["m00"] != 0:
                    centro_x = int(momentos["m10"] / momentos["m00"])
                    centro_y = int(momentos["m01"] / momentos["m00"])

                    rato_x = int((centro_x / largura_cam) * LARGURA_ECRA)
                    rato_y = int((centro_y / altura_cam) * ALTURA_ECRA)
                    pyautogui.moveTo(rato_x, rato_y)

                    na_zona_central = (LARGURA_ECRA/4 < rato_x < LARGURA_ECRA*0.75) and (ALTURA_ECRA/4 < rato_y < ALTURA_ECRA*0.75)
                    
                    if na_zona_central and area > 30000:
                        cv2.destroyAllWindows()
                        capturou_com_sucesso()
                        return 
                        
                    cv2.circle(frame, (centro_x, centro_y), 15, (0, 255, 0), -1)

        cv2.imshow("Mira da Pokébola", frame)
    janela_captura.after(15, rastrear_bola_captura)

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
janela = tk.Tk()
janela.title("🌍 Mundo Pokémon")
janela.geometry("800x600")
janela.configure(bg="#87CEEB")

# Menu Superior
frame_top = tk.Frame(janela, bg="#87CEEB")
frame_top.pack(pady=10)

label_pokedex = tk.Label(frame_top, text="Total: 0 apanhados", font=("Arial", 14, "bold"), bg="#87CEEB")
label_pokedex.grid(row=0, column=0, padx=20)

btn_pokedex = tk.Button(frame_top, text="📱 Abrir Pokédex", font=("Arial", 12, "bold"), bg="red", fg="white", command=abrir_pokedex)
btn_pokedex.grid(row=0, column=1, padx=20)

label_status = tk.Label(janela, text="Bem-vindo! A procurar...", font=("Arial", 16), bg="#87CEEB")
label_status.pack(pady=10)

# O Pokémon no mapa
btn_pokemon_mapa = tk.Button(janela, bg="white", borderwidth=2, cursor="hand2", command=iniciar_captura)

procurar_novo_pokemon()
janela.mainloop()