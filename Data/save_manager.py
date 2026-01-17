import json, time, os
from logic import Market, Wallet, Bankrupt, History


class SaveManager:
    def __init__(self, market: Market, wallet: Wallet, bankrupt: Bankrupt, history: History) -> None:
        self.market = market
        self.wallet = wallet
        self.bankrupt = bankrupt
        self.history = history
        
        self.save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Saves"))
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save_game(self) -> None:
        """
        Salva i dati della partita corrente in uno dei 3 slot disponibili (save1.json, save2.json, save3.json).
        Se tutti e 3 esistono, sovrascrive quello col timestamp "SAVED" più vecchio.
        """
        data = {
            "market": {
                "current_price": self.market.current_price,
                "current_state": self.market.current_state,
                "gen_price": self.market.gen_price,
                "gen_state": self.market.gen_state,
                "pop_counter": self.market.pop_counter,
                "queue": self.market.queue
            },
            "wallet": {
                "balance": self.wallet.balance,
                "stock": self.wallet.stock
            },
            "bankrupt": {
                "in_danger": self.bankrupt.in_danger,
                "start_time": self.bankrupt.start_time
            },
            "history": self.history.history,
            "SAVED": time.time()
        }

        # Trova il file da sovrascrivere o creare
        files = ["save1.json", "save2.json", "save3.json"]
        target_file = None
        
        # 1. Se c'è uno slot libero, usalo
        for filename in files:
            path = os.path.join(self.save_dir, filename)
            if not os.path.exists(path):
                target_file = filename
                break
        
        # 2. Se tutti esistono, trova il più vecchio
        if target_file is None:
            oldest_time = float('inf')
            oldest_file = None
            
            for filename in files:
                path = os.path.join(self.save_dir, filename)
                try:
                    with open(path, "r") as f:
                        save_data = json.load(f)
                        timestamp = save_data.get("SAVED", 0)
                        if timestamp < oldest_time:
                            oldest_time = timestamp
                            oldest_file = filename
                except (json.JSONDecodeError, OSError):
                    # Se il file è corrotto, sovrascrivilo
                    oldest_file = filename
                    break
            
            target_file = oldest_file

        full_path = os.path.join(self.save_dir, target_file)
        try:
            with open(full_path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Partita salvata in {full_path}")
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
    
    def load_game(self) -> None:
        """
        Carica i dati della partita dal file .json più recente nella cartella Saves.
        """
        files = ["save1.json", "save2.json", "save3.json"]
        newest_time = -1
        newest_file = None

        # Trova il file più recente
        for filename in files:
            path = os.path.join(self.save_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        save_data = json.load(f)
                        timestamp = save_data.get("SAVED", 0)
                        if timestamp > newest_time:
                            newest_time = timestamp
                            newest_file = filename
                except (json.JSONDecodeError, OSError):
                    continue
        
        if newest_file is None:
            print("Nessun salvataggio valido trovato.")
            return

        full_path = os.path.join(self.save_dir, newest_file)
        print(f"Caricamento partita da {full_path}...")

        try:
            with open(full_path, "r") as f:
                data = json.load(f)
            
            self.market.current_price = data["market"]["current_price"]
            self.market.current_state = data["market"]["current_state"]
            self.market.gen_price = data["market"]["gen_price"]
            self.market.gen_state = data["market"]["gen_state"]
            self.market.pop_counter = data["market"]["pop_counter"]
            self.market.queue = data["market"]["queue"]
            
            self.wallet.balance = data["wallet"]["balance"]
            self.wallet.stock = data["wallet"]["stock"]
            
            self.bankrupt.in_danger = data["bankrupt"]["in_danger"]
            self.bankrupt.start_time = data["bankrupt"]["start_time"]
            
            self.history.history = data["history"]
            print("Partita caricata con successo.")

        except Exception as e:
            print(f"Errore durante il caricamento: {e}")