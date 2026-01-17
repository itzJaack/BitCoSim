from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import os
import tkinter as tk
import sys

# Aggiungi la directory corrente al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Patch per DebugInterface
if not hasattr(sys, "debug"):
    sys.debug = sys.stdout

from Libraries.logic import Market, Wallet, History, Bankrupt
from Libraries.settings import SettingsFrame
from Libraries.debug import DebugInterface
from Data.save_manager import SaveManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BitCoSimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configurazione Finestra ---
        self.title("BitCoSim - Cryptocurrency Simulator")
        self.geometry("1100x700")
        
        # Gestione chiusura window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Stati del Gioco ---
        self.game_running = False
        self.paused = False
        self.is_bankrupt = False

        # --- Logica del Gioco ---
        self.market = Market()
        self.wallet = Wallet(balance=10000)
        self.history = History(self.wallet, self.market)
        self.bankrupt = Bankrupt(self.wallet, self.market)
        self.save_manager = SaveManager(self.market, self.wallet, self.bankrupt, self.history)

        # --- Dati per il Grafico ---
        self.graph_data = [] 
        self.max_data_points = 30 
        self.tick_interval = 1000 # Inizio veloce (1s)

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
        
        ctk.CTkLabel(stats_frame, text="BTC PRICE: $42,500", font=("Consolas", 14), text_color="#4CAF50").pack(side="left", padx=15)
        ctk.CTkLabel(stats_frame, text="MARKET CAP: $850B", font=("Consolas", 14), text_color="#2196F3").pack(side="left", padx=15)

        btn_frame = ctk.CTkFrame(self.start_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, pady=20)
        
        ctk.CTkButton(btn_frame, text="NUOVA PARTITA", command=self.start_game, width=220, height=50, font=("Roboto", 16, "bold"), fg_color="#1E88E5", hover_color="#1565C0").pack(pady=10)
        ctk.CTkButton(btn_frame, text="CARICA PARTITA", command=self.load_and_start, width=220, height=50, font=("Roboto", 16, "bold"), fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=10)
        
        ctk.CTkLabel(self.start_frame, text="v1.0.0 | Creato da BitCoSim Team", font=("Roboto", 10), text_color="gray50").grid(row=5, column=0, pady=20)

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
        self.lbl_balance = ctk.CTkLabel(self.info_frame, text=f"${self.wallet.balance:,.2f}", font=("Roboto", 20, "bold"), text_color="#4CAF50")
        self.lbl_balance.pack(pady=(0,5), padx=10, anchor="w")
        
        self.lbl_stocks = ctk.CTkLabel(self.info_frame, text=f"Azioni: {self.wallet.stock:.4f}", font=("Roboto", 13))
        self.lbl_stocks.pack(pady=(0,10), padx=10, anchor="w")

        # Sezione Mercato (Sidebar)
        self.market_frame = ctk.CTkFrame(self.sidebar_frame, fg_color=("gray80", "#333333"))
        self.market_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.market_frame, text="PREZZO ATTUALE", font=("Roboto", 12)).pack(pady=(10,0), padx=10, anchor="w")
        self.lbl_price = ctk.CTkLabel(self.market_frame, text=f"${self.market.current_price:,.2f}", font=("Roboto", 20, "bold"), text_color="#2196F3")
        self.lbl_price.pack(pady=(0,10), padx=10, anchor="w")

        # Trading
        ctk.CTkLabel(self.sidebar_frame, text="Trading Rapido", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")

        self.entry_amount = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Quantità")
        self.entry_amount.pack(fill="x", padx=15, pady=5)

        self.btn_buy = ctk.CTkButton(self.sidebar_frame, text="ACQUISTA", fg_color="#2E7D32", hover_color="#1B5E20", command=self.buy_action)
        self.btn_buy.pack(fill="x", padx=15, pady=5)

        self.btn_sell = ctk.CTkButton(self.sidebar_frame, text="VENDI", fg_color="#C62828", hover_color="#B71C1C", command=self.sell_action)
        self.btn_sell.pack(fill="x", padx=15, pady=5)
        
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
        ctk.CTkButton(self.pause_menu_content, text="SALVA ED ESCI", command=self.on_closing, width=200, height=45, fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=(10, 30))
 
        self.game_container.grid_remove() # Nascondi UI gioco

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
    def start_game(self):
        self.start_frame.grid_remove()
        self.game_container.grid()
        self.game_running = True
        
        # Force redraw once visible
        self.update_graph() 
        self.update_game_loop()

    def load_and_start(self):
        self.save_manager.load_game()
        if self.history.history:
            self.graph_data = [h[2] for h in self.history.history[-self.max_data_points:]]
        self.start_game()

    def buy_action(self):
        try:
            amount = float(self.entry_amount.get())
            cost = amount * self.market.current_price
            if self.wallet.buy_stock(amount, self.market.current_price):
                self.lbl_msg.configure(text=f"Acquistati {amount} BTC", text_color="#66BB6A")
                self.update_ui_labels()
                sys.debug.write(f"[TRADE] BUY {amount} @ ${self.market.current_price:.2f} | Tot: ${cost:.2f}\n")
            else:
                self.lbl_msg.configure(text="Fondi insufficienti!", text_color="#EF5350")
                sys.debug.write("[ERROR] BUY fallito: Fondi insufficienti\n")
        except ValueError:
            self.lbl_msg.configure(text="Inserisci un numero valido", text_color="#EF5350")

    def sell_action(self):
        try:
            amount = float(self.entry_amount.get())
            gain = amount * self.market.current_price
            if self.wallet.sell_stock(amount, self.market.current_price):
                self.lbl_msg.configure(text=f"Venduti {amount} BTC", text_color="#66BB6A")
                self.update_ui_labels()
                sys.debug.write(f"[TRADE] SELL {amount} @ ${self.market.current_price:.2f} | Tot: ${gain:.2f}\n")
            else:
                self.lbl_msg.configure(text="Azioni insufficienti!", text_color="#EF5350")
                sys.debug.write("[ERROR] SELL fallito: Azioni insufficienti\n")
        except ValueError:
            self.lbl_msg.configure(text="Inserisci un numero valido", text_color="#EF5350")
            
    def update_ui_labels(self):
        self.lbl_balance.configure(text=f"${self.wallet.balance:,.2f}")
        self.lbl_price.configure(text=f"${self.market.current_price:,.2f}")
        self.lbl_stocks.configure(text=f"Azioni: {self.wallet.stock:.4f}")

    def toggle_pause(self, event=None):
        if not self.game_running: return
        
        self.paused = not self.paused
        if self.paused:
            self.pause_menu_content.pack(expand=True, fill="both")
            if hasattr(self, "settings_frame") and self.settings_frame.winfo_ismapped():
                self.settings_frame.pack_forget()

            self.pause_overlay.place(relx=0.5, rely=0.5, anchor="center")
            sys.debug.write("[GAME] Stato: PAUSA\n")
        else:
            self.pause_overlay.place_forget()
            self.update_game_loop()
            sys.debug.write("[GAME] Stato: RIPRESA\n")

    def show_settings_in_pause(self):
        # Nascondi menu pausa
        self.pause_menu_content.pack_forget()
        
        # Mostra frame settings (crealo se non esiste)
        if not hasattr(self, "settings_frame"):
            self.settings_frame = SettingsFrame(self.pause_overlay, close_callback=self.hide_settings_in_pause)
        
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
            sys.debug.write("[SYSTEM] Auto-Save... ")
            self.save_manager.save_game()
            sys.debug.write("Completato.\n")
        self.after(600000, self.auto_save_loop)

    def on_closing(self):
        if self.game_running:
            self.save_manager.save_game()
            sys.debug.write("[SYSTEM] Chiusura e salvataggio.\n")
        self.destroy()

    # --- Game Loop ---
    def update_game_loop(self):
        if not self.game_running or self.paused:
            return

        # 1. Update Stato Market e Logica Bancarotta
        self.market.update_market()
        self.history.save_history()
        
        # Logica di rischio bancarotta
        game_over = self.bankrupt.update_risk() 
        
        if self.bankrupt.in_danger:
            # Mostra Alert
            if not self.bankrupt_alert_frame.winfo_viewable():
                self.bankrupt_alert_frame.pack(side="right", padx=20)
                sys.debug.write("[ALERT] Bancarotta imminente! Timer attivato.\n")
            
            remaining = self.bankrupt.get_time()
            self.lbl_bankrupt_timer.configure(text=f"RISCHIO BANCAROTTA: {remaining}s")
            
            # Se siamo in pericolo e game over -> Fine
            if game_over:
                self.lbl_bankrupt_timer.configure(text="BANCAROTTA!")
                sys.debug.write("[GAME OVER] Bancarotta confermata. Reset.\n")
                self.update_ui_labels()
        else:
            # Nascondi Alert se non c'è più pericolo
            if self.bankrupt_alert_frame.winfo_viewable():
                self.bankrupt_alert_frame.pack_forget()
                sys.debug.write("[ALERT] Percolo rientrato.\n")

        # 2. Log Debug
        sys.debug.write(f"[MARKET] ${self.market.current_price:.2f} ({self.market.current_state})\n")
        
        # 3. Grafico Data Update
        self.graph_data.append(self.market.current_price)
        
        # Gestione Velocità
        is_graph_full = len(self.graph_data) > self.max_data_points
        if is_graph_full:
            self.graph_data.pop(0)
            if self.bankrupt.in_danger:
                self.tick_interval = 5000 
            else:
                self.tick_interval = 10000 
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