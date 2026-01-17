import customtkinter as ctk
import sys

class ConsoleRedirector:
    """Reindirizza il debug a un widget di testo."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_debug = sys.debug

    def write(self, str):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", str)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except:
            pass
        self.original_debug.write(str) 

    def flush(self):
        self.original_debug.flush()

class DebugInterface(ctk.CTkToplevel):
    def __init__(self, master, wallet, market, save_manager, bankrupt=None):
        super().__init__(master)
        
        self.wallet = wallet
        self.market = market
        self.save_manager = save_manager
        self.bankrupt = bankrupt
        
        self.title("DEBUG CONSOLE")
        self.geometry("800x600")
        self.resizable(False, False)
        self.withdraw()
        
        self.attributes("-topmost", True)
        
        self.protocol("WM_DELETE_WINDOW", self.hide)
        
        self.create_widgets()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar Sinistra (Controlli) ---
        self.left_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_propagate(False)

        ctk.CTkLabel(self.left_frame, text="DEBUG TOOLS", font=("Roboto", 20, "bold")).pack(pady=20, padx=20, anchor="w")

        # Modifica Valori
        self.edit_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.edit_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(self.edit_frame, text="Saldo Portafoglio:", font=("Roboto", 12)).pack(anchor="w")
        self.entry_balance = ctk.CTkEntry(self.edit_frame)
        self.entry_balance.pack(fill="x", pady=(5, 15))
        self.entry_balance.insert(0, str(self.wallet.balance))
        
        ctk.CTkLabel(self.edit_frame, text="Prezzo Mercato:", font=("Roboto", 12)).pack(anchor="w")
        self.entry_price = ctk.CTkEntry(self.edit_frame)
        self.entry_price.pack(fill="x", pady=(5, 15))
        self.entry_price.insert(0, str(self.market.current_price))
        
        ctk.CTkButton(self.edit_frame, text="APPLICA MODIFICHE", command=self.update_data, fg_color="#F57C00", hover_color="#E65100").pack(fill="x", pady=10)

        # Actions
        ctk.CTkLabel(self.left_frame, text="AZIONI FORZATE", font=("Roboto", 14, "bold")).pack(pady=(20, 10), padx=20, anchor="w")
        
        ctk.CTkButton(self.left_frame, text="Refresh UI (Valori)", command=self.refresh_view, fg_color="#1976D2", hover_color="#0D47A1").pack(fill="x", padx=10, pady=5)
        
        if self.bankrupt:
            ctk.CTkButton(self.left_frame, text="⚠️ TRIGGER BANCAROTTA", command=self.trigger_bankrupt, fg_color="#D32F2F", hover_color="#B71C1C").pack(fill="x", padx=10, pady=20)


        # --- Area Centrale Destra (Console) ---
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.right_frame, text="System Log", font=("Roboto", 16, "bold")).pack(anchor="w", pady=5)
        
        self.console_text = ctk.CTkTextbox(self.right_frame, font=("Consolas", 12), fg_color="#1E1E1E", text_color="#00FF00")
        self.console_text.pack(fill="both", expand=True)
        self.console_text.configure(state="disabled")

        sys.debug = ConsoleRedirector(self.console_text)
        print("[DEBUG] Console inizializzata e pronta.")

    def update_data(self):
        try:
            new_balance = float(self.entry_balance.get())
            new_price = float(self.entry_price.get())
            
            self.wallet.balance = new_balance
            self.market.current_price = new_price
            
            print(f"[EDIT] Dati aggiornati forzatamente: Saldo=${new_balance}, Prezzo=${new_price}")
        except ValueError:
            print("[ERROR] Input non numerico rilevato.")

    def trigger_bankrupt(self):
        if self.bankrupt:
            import time
            self.bankrupt.in_danger = True
            self.bankrupt.start_time = time.time()
            self.bankrupt.grace_period = 30 
            
            print("[TRIGGER] Evento Bancarotta attivato manualmente!")

    def refresh_view(self):
        self.entry_balance.delete(0, "end")
        self.entry_balance.insert(0, str(self.wallet.balance))
        
        self.entry_price.delete(0, "end")
        self.entry_price.insert(0, str(self.market.current_price))
        print("[VIEW] Interfaccia sincronizzata con il gioco.")

    def toggle(self, event=None):
        if self.state() == "withdraw" or self.state() == "iconic" or not self.winfo_viewable():
            self.center_window()
            self.deiconify()
            self.lift()
            self.refresh_view()
        else:
            self.withdraw()
            
    def hide(self):
        self.withdraw()