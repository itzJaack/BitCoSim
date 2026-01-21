from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import os
import tkinter as tk
import sys
import threading
import requests

# Aggiungi la directory corrente al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Patch per DebugInterface
if not hasattr(sys, "debug"):
    sys.debug = sys.stdout

from Libraries.logic import Market, Wallet, History, Bankrupt
from Libraries.settings import SettingsFrame
from Libraries.debug import DebugInterface
from Data.save_manager import SaveManager
from Data.settings_manager import SettingsManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BitCoSimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BitCoSim - Cryptocurrency Simulator")
        
        # Centra la finestra sullo schermo
        width = 1100
        height = 750
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Gestione chiusura window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Stati del Gioco ---
        self.game_running = False
        self.paused = False
        self.is_bankrupt = False

        # --- Logica del Gioco ---
        self.market = Market()
        self.wallet = Wallet(balance=125000)
        self.history = History(self.wallet, self.market)
        self.bankrupt = Bankrupt(self.wallet, self.market)
        self.save_manager = SaveManager(self.market, self.wallet, self.bankrupt, self.history)
        self.settings_manager = SettingsManager()
        
        self.current_pct_change = 0.0
        self.current_scaling_str = "100%"

        # Applica settings salvati
        self.apply_settings()

        # --- Dati per il Grafico ---
        self.graph_data = [] 
        self.max_data_points = 30 
        self.tick_interval = 1000

        # --- Layout Grigilia (Globale) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Start Menu (inizialmente visibile)
        self.build_start_menu()
        
        # 2. Game UI (inizialmente nascosta, ma costruita)
        self.build_game_ui()
        
        # 3. Finestre Secondarie (Debug rimane esterna, Settings integrata)
        self.debug_interface = DebugInterface(self, self.wallet, self.market, self.save_manager, self.bankrupt)

        # --- Binding Tasti ---
        self.bind("<Escape>", self.toggle_pause)
        self.bind("<F7>", self.toggle_debug)
        
        # Avvia loop salvataggio automatico (indipendente dal loop di gioco)
        self.after(600000, self.auto_save_loop) # 10 minuti

    def build_start_menu(self):
        self.start_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "#2b2b2b"))
        self.start_frame.grid(row=0, column=0, sticky="nsew")
        self.start_frame.grid_columnconfigure(0, weight=1)
        self.start_frame.grid_rowconfigure((0, 6), weight=1)

        ctk.CTkLabel(self.start_frame, text="BitCoSim", font=("Roboto Medium", 60)).grid(row=1, column=0, pady=(20, 10))
        ctk.CTkLabel(self.start_frame, text="Simula. Investi. Domina.", font=("Roboto", 18, "italic"), text_color=("gray50", "gray70")).grid(row=2, column=0, pady=5)
        
        # Stats rapide
        stats_frame = ctk.CTkFrame(self.start_frame, fg_color="transparent")
        stats_frame.grid(row=3, column=0, pady=30)
        
        self.lbl_start_price = ctk.CTkLabel(stats_frame, text="BTC PRICE: Loading...", font=("Consolas", 14), text_color="#4CAF50")
        self.lbl_start_price.pack(side="left", padx=15)
        
        self.lbl_start_cap = ctk.CTkLabel(stats_frame, text="MARKET CAP: Loading...", font=("Consolas", 14), text_color="#2196F3")
        self.lbl_start_cap.pack(side="left", padx=15)

        # Avvia fetch dati in background
        threading.Thread(target=self.fetch_live_data, daemon=True).start()

        btn_frame = ctk.CTkFrame(self.start_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, pady=20)
        
        ctk.CTkButton(btn_frame, text="NUOVA PARTITA", command=self.start_game, width=220, height=50, font=("Roboto", 16, "bold"), fg_color="#1E88E5", hover_color="#1565C0").pack(pady=10)
        ctk.CTkButton(btn_frame, text="CARICA PARTITA", command=self.load_and_start, width=220, height=50, font=("Roboto", 16, "bold"), fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=10)
        
        ctk.CTkLabel(self.start_frame, text="v1.0.0 | Creato da BitCoSim Team", font=("Roboto", 10), text_color="gray50").grid(row=5, column=0, pady=20)

    def fetch_live_data(self):
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_market_cap=true")
            data = response.json()
            
            price = data['bitcoin']['usd']
            cap = data['bitcoin']['usd_market_cap']
            
            # Format Market Cap (Billion/Trillion)
            if cap >= 1_000_000_000_000:
                cap_formatted = f"${cap/1_000_000_000_000:.2f}T"
            else:
                cap_formatted = f"${cap/1_000_000_000:.2f}B"
                
            # Update UI in main thread safely (using after usually preferred but ctk often handles this, 
            # for safety we can use after or direct config if simple)
            # Update UI in main thread safely
            self.after(0, lambda: self.update_start_labels(price, cap_formatted))
            
            # Se siamo nel menu, aggiorna il prezzo di partenza del mercato
            if not self.game_running:
                self.market.start_price = price
                self.market.current_price = price
                self.market.gen_price = price
            
        except Exception as e:
            sys.debug.write(f"[NETWORK] Errore fetch dati: {e}\n")
            self.after(0, lambda: self.update_start_labels(42_500, "$850B")) # Fallback
            if not self.game_running:
                self.market.start_price = 42_500
                self.market.current_price = 42_500
                self.market.gen_price = 42_500

    def update_start_labels(self, price, cap):
        if hasattr(self, 'lbl_start_price'):
            self.lbl_start_price.configure(text=f"BTC PRICE: ${price:,.0f}")
        if hasattr(self, 'lbl_start_cap'):
            self.lbl_start_cap.configure(text=f"MARKET CAP: {cap}")

    def build_game_ui(self):
        # Container principale gioco
        self.game_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray92", "#1a1a1a"))
        self.game_container.grid(row=0, column=0, sticky="nsew")

        self.game_container.grid_columnconfigure(1, weight=1)
        self.game_container.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self.game_container, width=250, corner_radius=0, fg_color=("gray85", "#2b2b2b"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) # Forza larghezza fissa

        # Sidebar Header
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="BitCoSim", font=ctk.CTkFont(family="Roboto", size=24, weight="bold"))
        self.logo_label.pack(pady=(30, 20), padx=20, anchor="w")

        # Sezione info
        self.info_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=("gray80", "#333333"))
        self.info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.info_frame, text="PORTAFOGLIO", font=("Roboto", 12)).pack(pady=(10,0), padx=10, anchor="w")
        initial_balance = self.format_large_number(self.wallet.balance)
        self.lbl_balance = ctk.CTkLabel(self.info_frame, text=f"${initial_balance}", font=("Roboto", 20, "bold"), text_color="#4CAF50")
        self.lbl_balance.pack(pady=(0,5), padx=10, anchor="w")
        
        self.lbl_stocks = ctk.CTkLabel(self.info_frame, text=f"Azioni: {self.wallet.stock:.2f}", font=("Roboto", 13))
        self.lbl_stocks.pack(pady=(0,10), padx=10, anchor="w")

        # Sezione Mercato (Sidebar)
        self.market_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=("gray80", "#333333"))
        self.market_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.market_frame, text="PREZZO ATTUALE", font=("Roboto", 12)).pack(pady=(10,0), padx=10, anchor="w")
        self.lbl_price = ctk.CTkLabel(self.market_frame, text=f"${self.market.current_price:,.2f}", font=("Roboto", 20, "bold"), text_color="#2196F3")
        self.lbl_price.pack(pady=(0,0), padx=10, anchor="w")
        
        self.lbl_pct = ctk.CTkLabel(self.market_frame, text="+0.00%", font=("Roboto", 12, "bold"), text_color="gray")
        self.lbl_pct.pack(pady=(0,10), padx=10, anchor="w")

        # Trading
        ctk.CTkLabel(self.sidebar_frame, text="Trading Rapido", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")

        self.entry_amount = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Quantità", height=35)
        self.entry_amount.pack(fill="x", padx=15, pady=(5, 5))

        self.max_btn_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.max_btn_container.pack(fill="x", padx=15, pady=0)
        
        self.btn_max_sell = ctk.CTkButton(self.max_btn_container, text="Max Sell", height=30, 
                                     fg_color=("gray75", "#333333"), 
                                     hover_color=("gray70", "#444444"),
                                     text_color=("black", "white"),
                                     font=("Roboto", 10, "bold"), command=self.set_max_sell_amount)
        self.btn_max_sell.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_max_buy = ctk.CTkButton(self.max_btn_container, text="Max Buy", height=30, 
                                     fg_color=("gray75", "#333333"), 
                                     hover_color=("gray70", "#444444"),
                                     text_color=("black", "white"),
                                     font=("Roboto", 10, "bold"), command=self.set_max_buy_amount)
        self.btn_max_buy.pack(side="right", fill="x", expand=True, padx=(2, 0))

        self.btn_buy = ctk.CTkButton(self.sidebar_frame, text="ACQUISTA", 
                                     fg_color=("gray85", "#2b2b2b"), text_color=("black", "white"),
                                     border_color="#2E7D32", border_width=2,
                                     hover_color=("#F2F2F2", "#1B5E20"), font=("Roboto", 14, "bold"), 
                                     height=40, command=self.buy_action)
        self.btn_buy.pack(fill="x", padx=15, pady=8)

        self.btn_sell = ctk.CTkButton(self.sidebar_frame, text="VENDI", 
                                      fg_color=("gray85", "#2b2b2b"), text_color=("black", "white"),
                                      border_color="#C62828", border_width=2,
                                      hover_color=("#F2F2F2", "#B71C1C"), font=("Roboto", 14, "bold"), 
                                      height=40, command=self.sell_action)
        self.btn_sell.pack(fill="x", padx=15, pady=8)
        
        self.lbl_msg = ctk.CTkLabel(self.sidebar_frame, text="", text_color=("orange", "yellow"), font=("Roboto", 11))
        self.lbl_msg.pack(pady=5)

        # Bottom Sidebar
        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Impostazioni", command=self.toggle_pause, fg_color="transparent", border_width=2, text_color=("gray10", "gray90"))

        # --- Main Content ---
        self.main_content = ctk.CTkFrame(self.game_container, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Top Bar (Main)
        self.top_bar = ctk.CTkFrame(self.main_content, height=50, corner_radius=10, fg_color=("white", "#2b2b2b"))
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(self.top_bar, text="PANORAMICA MERCATO", font=("Roboto", 16, "bold")).pack(side="left", padx=20, pady=10)
        
        # Alert Frame
        self.bankrupt_alert_frame = ctk.CTkFrame(self.top_bar, fg_color="#B00020", corner_radius=5)
        self.lbl_bankrupt_timer = ctk.CTkLabel(self.bankrupt_alert_frame, text="RISCHIO BANCAROTTA: 00s", text_color="white", font=("Roboto", 14, "bold"))
        self.lbl_bankrupt_timer.pack(padx=10, pady=2)

        # Grafico
        self.graph_frame = ctk.CTkFrame(self.main_content, corner_radius=10, fg_color=("white", "#2b2b2b"))
        self.graph_frame.grid(row=1, column=0, sticky="nsew")
        
        self.init_graph()
        
        # Menu Pausa (overlay) - Costruito MA nascosto
        self.pause_overlay = ctk.CTkFrame(self.game_container, fg_color=("gray95", "gray10"), corner_radius=20, border_width=2, border_color="gray50")
        
        # Contenuto Default Pausa
        self.pause_menu_content = ctk.CTkFrame(self.pause_overlay, fg_color="transparent")
        self.pause_menu_content.pack(expand=True, fill="both")

        ctk.CTkLabel(self.pause_menu_content, text="GIOCO IN PAUSA", font=("Roboto", 30, "bold")).pack(pady=30, padx=80)
        ctk.CTkButton(self.pause_menu_content, text="RIPRENDI", command=self.toggle_pause, width=200, height=45).pack(pady=10)
        ctk.CTkButton(self.pause_menu_content, text="IMPOSTAZIONI", command=self.show_settings_in_pause, width=200, height=45).pack(pady=10)
        ctk.CTkButton(self.pause_menu_content, text="MENU PRINCIPALE", command=self.return_to_main_menu, width=200, height=45, fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=10)
        ctk.CTkButton(self.pause_menu_content, text="SALVA ED ESCI", command=self.on_closing, width=200, height=45, fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=(10, 30))
 
        # Menu Game Over (overlay nascosto)
        self.game_over_overlay = ctk.CTkFrame(self.game_container, fg_color=("gray95", "gray10"), corner_radius=20, border_width=2, border_color="#B71C1C")
        ctk.CTkLabel(self.game_over_overlay, text="BANCAROTTA!", font=("Roboto", 35, "bold"), text_color="#D32F2F").pack(pady=(40, 10), padx=80)
        ctk.CTkLabel(self.game_over_overlay, text="Hai perso tutto il tuo patrimonio.", font=("Roboto", 16), text_color="gray50").pack(pady=(0, 30))
        ctk.CTkButton(self.game_over_overlay, text="MENU PRINCIPALE", command=self.return_to_main_menu, width=200, height=45, fg_color="#D32F2F", hover_color="#B71C1C").pack(pady=20)
 
        self.game_container.grid_remove() # Nascondi UI gioco

    def show_game_over_screen(self):
        self.paused = True
        if self.pause_overlay.winfo_viewable():
            self.pause_overlay.place_forget()
        self.game_over_overlay.place(relx=0.5, rely=0.5, anchor="center")

    def return_to_main_menu(self):
        self.paused = True
        self.game_running = False
        self.pause_overlay.place_forget()
        self.game_over_overlay.place_forget()
        self.game_container.grid_remove()
        self.start_frame.grid()

    def init_graph(self):
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        mode = ctk.get_appearance_mode()
        is_light = mode == "Light"
        
        bg_color = '#EBEBEB' if is_light else '#212121'
        if is_light:
            text_color = 'black'
            spine_color = '#333333'
            grid_color = '#CCCCCC'
        else:
            text_color = 'gray'
            spine_color = '#444444'
            grid_color = '#333333'
        
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        self.ax.tick_params(colors=text_color)
        for spine in self.ax.spines.values():
            spine.set_color(spine_color)
            
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.grid(True, color=grid_color, linestyle='--')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=2, pady=2)

    def update_graph(self):
        self.ax.clear()
        
        mode = ctk.get_appearance_mode()
        is_light = mode == "Light"
        
        bg_color = '#EBEBEB' if is_light else '#212121'
        if is_light:
            text_color = 'black'
            spine_color = '#333333'
            grid_color = '#CCCCCC'
            title_color = 'black'
        else:
            text_color = 'gray'
            spine_color = '#444444'
            grid_color = '#333333'
            title_color = 'white'
            
        self.ax.set_facecolor(bg_color)
        self.figure.patch.set_facecolor(bg_color)
        self.ax.tick_params(colors=text_color)
        
        # Colore Linea
        line_color = '#29B6F6' # Light Blue
        if self.bankrupt.in_danger:
            line_color = '#EF5350' # Red
            
        self.ax.plot(self.graph_data, color=line_color, marker='o', markersize=3, linewidth=2)
        self.ax.fill_between(range(len(self.graph_data)), self.graph_data, alpha=0.1, color=line_color)
        
        self.ax.set_xlim(0, self.max_data_points - 1)
        self.ax.margins(x=0)
        
        self.ax.set_title(f'Andamento Prezzo ({self.market.current_state})', color=title_color, pad=20)
        self.ax.grid(True, color=grid_color, linestyle='--')
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(spine_color)
        self.ax.spines['bottom'].set_color(spine_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        
        self.figure.tight_layout()
        self.canvas.draw()

    # --- Azioni ---
    def start_game(self, reset_state=True):
        if reset_state:
            # Reset logica di gioco se necessario
            self.market.reset()
            self.wallet.reset()
            self.history.reset()
            self.bankrupt.reset()
            self.graph_data = [] # Reset dati grafico visivi
        
        self.start_frame.grid_remove()
        self.game_container.grid()
        self.game_running = True
        self.paused = False
        
        # Force redraw once visible
        self.update_graph() 
        self.update_game_loop()

    def load_and_start(self):
        if self.save_manager.load_game():
            if self.history.history:
                self.graph_data = [h[2] for h in self.history.history[-self.max_data_points:]]
            self.start_game(reset_state=False)
        else:
            # Opzionale: mostra un messaggio se non c'è salvataggio
            pass

    def buy_action(self):
        try:
            amount_str = self.entry_amount.get().replace(',', '.')
            amount = float(amount_str)
            
            # Controllo multipli di 0.25 (usando arrotondamento per sicurezza floating point)
            if not (round(amount / 0.25, 8)).is_integer():
                self.lbl_msg.configure(text="Solo multipli di 0.25!", text_color="#EF5350")
                return

            cost = amount * self.market.current_price
            if self.wallet.buy_stock(amount, self.market.current_price):
                self.lbl_msg.configure(text=f"Acquistati {amount} BTC", text_color="#2E7D32")
                self.update_ui_labels()
            else:
                self.lbl_msg.configure(text="Fondi insufficienti!", text_color="#EF5350")
        except ValueError:
            self.lbl_msg.configure(text="Inserisci un numero valido", text_color="#EF5350")

    def sell_action(self):
        try:
            amount_str = self.entry_amount.get().replace(',', '.')
            amount = float(amount_str)
            gain = amount * self.market.current_price
            if self.wallet.sell_stock(amount, self.market.current_price):
                self.lbl_msg.configure(text=f"Venduti {amount} BTC", text_color="#C62828")
                self.update_ui_labels()
            else:
                self.lbl_msg.configure(text="Azioni insufficienti!", text_color="#EF5350")
        except ValueError:
            self.lbl_msg.configure(text="Inserisci un numero valido", text_color="#EF5350")

    def set_max_sell_amount(self):
        self.entry_amount.delete(0, tk.END)
        # Anche per la vendita, potremmo voler suggerire il massimo arrotondato ai 0.25 
        # se l'utente ha frazioni strane, ma per ora mettiamo tutto quello che ha.
        self.entry_amount.insert(0, f"{self.wallet.stock:.2f}")

    def set_max_buy_amount(self):
        if self.market.current_price <= 0: return
        
        # Massimo acquistabile basato sul saldo
        max_possible = self.wallet.balance / self.market.current_price
        
        # Arrotonda per difetto al multiplo di 0.25 più vicino
        max_rounded = (max_possible // 0.25) * 0.25
        
        self.entry_amount.delete(0, tk.END)
        self.entry_amount.insert(0, f"{max_rounded:.2f}")
            
    def update_ui_labels(self):
        formatted_balance = self.format_large_number(self.wallet.balance)
        self.lbl_balance.configure(text=f"${formatted_balance}")
        
        # Formattazione Prezzo
        formatted_price = self.format_large_number(self.market.current_price)
        self.lbl_price.configure(text=f"${formatted_price}")
        
        # Percentuale
        pct_color = "#66BB6A" if self.current_pct_change >= 0 else "#EF5350"
        sign = "+" if self.current_pct_change >= 0 else ""
        self.lbl_pct.configure(text=f"{sign}{self.current_pct_change:.2f}%", text_color=pct_color)
        
        self.lbl_stocks.configure(text=f"Azioni: {self.wallet.stock:.2f}")

    def format_large_number(self, num):
        if num >= 1_000_000_000_000_000:
            return f"{num/1_000_000_000_000_000:.2f}Qa"
        elif num >= 1_000_000_000_000:
            return f"{num/1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:
            return f"{num/1_000_000_000:.2f}Mrd"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.2f}Mln"
        else:
            return f"{num:,.2f}"

    def toggle_pause(self, event=None):
        if not self.game_running: return
        
        self.paused = not self.paused
        if self.paused:
            self.pause_menu_content.pack(expand=True, fill="both")
            if hasattr(self, "settings_frame") and self.settings_frame.winfo_ismapped():
                self.settings_frame.pack_forget()

            self.pause_overlay.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.pause_overlay.place_forget()
            self.update_game_loop()

    def show_settings_in_pause(self):
        # Nascondi menu pausa
        self.pause_menu_content.pack_forget()
        
        # Mostra frame settings (crealo se non esiste)
        if not hasattr(self, "settings_frame"):
            app_mode = ctk.get_appearance_mode()
            # Mappa inversa per ctk -> UI menu
            rev_map = {"System": "Sistema", "Light": "Chiaro", "Dark": "Scuro"}
            
            # Per lo scaling, usiamo il valore salvato nell'app
            scale_val = self.current_scaling_str
            
            self.settings_frame = SettingsFrame(
                self.pause_overlay, 
                close_callback=self.hide_settings_in_pause,
                initial_appearance=rev_map.get(app_mode, "Sistema"),
                initial_scaling=scale_val
            )
        
        self.settings_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def hide_settings_in_pause(self):
        if hasattr(self, "settings_frame"):
            self.settings_frame.pack_forget()
        self.pause_menu_content.pack(expand=True, fill="both")

    def toggle_debug(self, event=None):
        self.debug_interface.toggle()

    def open_settings(self):
        pass
    
    def auto_save_loop(self):
        if self.game_running and not self.paused:
            self.save_manager.save_game()
        self.after(600000, self.auto_save_loop)

    def apply_settings(self):
        data = self.settings_manager.load_settings()
        if data:
            if "appearance_mode" in data:
                mode_map = {"Sistema": "System", "Chiaro": "Light", "Scuro": "Dark", "System": "System", "Light": "Light", "Dark": "Dark"}
                mode = data["appearance_mode"]
                ctk.set_appearance_mode(mode_map.get(mode, "System"))
            if "ui_scaling" in data:
                scaling = data["ui_scaling"]
                self.current_scaling_str = scaling if isinstance(scaling, str) else f"{int(scaling*100)}%"
                
                if isinstance(scaling, str):
                    scaling_float = int(scaling.replace("%", "")) / 100
                else:
                    scaling_float = scaling
                ctk.set_widget_scaling(scaling_float)

    def on_closing(self):
        if self.game_running:
            self.save_manager.save_game()
        
        # Salva impostazioni correnti
        # Se il frame settings esiste, prendi i valori da lì, altrimenti usa i globali
        curr_appearance = ctk.get_appearance_mode()
        # Usa il valore tracciato se il frame non esiste
        curr_scaling = self.current_scaling_str
        if hasattr(self, "settings_frame"):
            curr_appearance = self.settings_frame.option_appearance.get()
            curr_scaling = self.settings_frame.option_scaling.get()
        
        self.settings_manager.save_settings(curr_appearance, curr_scaling)
        self.destroy()

    # --- Game Loop ---
    def update_game_loop(self):
        if not self.game_running or self.paused:
            return

        # 1. Update Stato Market e Logica Bancarotta
        old_price = self.market.current_price
        self.market.update_market()
        
        if old_price > 0:
            self.current_pct_change = ((self.market.current_price - old_price) / old_price) * 100
        else:
            self.current_pct_change = 0.0
            
        self.history.save_history()
        
        # Logica di rischio bancarotta
        # Logica di rischio bancarotta (passando il tempo trascorso in secondi = tick_interval / 1000)
        # Nota: tick_interval è in ms
        delta_seconds = self.tick_interval / 1000.0
        game_over = self.bankrupt.update_risk(delta_seconds) 
        
        if self.bankrupt.in_danger:
            # Mostra Alert
            if not self.bankrupt_alert_frame.winfo_viewable():
                self.bankrupt_alert_frame.pack(side="right", padx=20)
            
            remaining = self.bankrupt.get_time()
            self.lbl_bankrupt_timer.configure(text=f"RISCHIO BANCAROTTA: {remaining}s")
            
            # Se siamo in pericolo e game over -> Fine
            # Se siamo in pericolo e game over -> Fine
            if game_over:
                self.lbl_bankrupt_timer.configure(text="BANCAROTTA!")
                self.update_ui_labels()
                self.show_game_over_screen()
                return
        else:
            # Nascondi Alert se non c'è più pericolo
            if self.bankrupt_alert_frame.winfo_viewable():
                self.bankrupt_alert_frame.pack_forget()

        # 3. Grafico Data Update
        self.graph_data.append(self.market.current_price)
        
        # Gestione Velocità
        is_graph_full = len(self.graph_data) > self.max_data_points
        if is_graph_full:
            self.graph_data.pop(0)
            if self.bankrupt.in_danger:
                self.tick_interval = 1000 # Mantieni responsivo (1s) anche in pericolo
            else:
                self.tick_interval = 1000
        else:
            self.tick_interval = 1000 

        # 4. Update UI
        self.update_graph()
        self.update_ui_labels()

        # 5. Loop
        self.after(self.tick_interval, self.update_game_loop)

if __name__ == "__main__":
    app = BitCoSimApp()                                                                                           
    app.mainloop()                                                                               