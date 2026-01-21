import random, time


class Market:
    """
    Gestisce la simulazione del mercato finanziario utilizzando l'algoritmo della catena di Markov 
    [ogni stato ha una probabilità di transizione che viene scelta in base allo stato corrente e non rispetto agli stati passati].
    Include un buffer per generare passi futuri in batch.
    """
    def __init__(self, start_price: float = 40000) -> None: 
        self.start_price = start_price
        self.current_price = start_price
        self.states = ["BEAR", "BULL", "STAGNANT"]
        self.current_state = "STAGNANT"

        # Definizione delle probabilità di transizione tra gli stati del mercato
        self.matrix = {
            "BEAR": {"BEAR": 0.6, "BULL": 0.1, "STAGNANT": 0.3},
            "BULL": {"BEAR": 0.1, "BULL": 0.6, "STAGNANT": 0.3},
            "STAGNANT": {"BEAR": 0.3, "BULL": 0.3, "STAGNANT": 0.4}
        }

        self.queue = []
        self.gen_price = self.current_price
        self.gen_state = self.current_state
        self.pop_counter = 0
        
        self.generate_steps(10)

    def reset(self):
        self.current_price = self.start_price
        self.current_state = "STAGNANT"
        self.queue = []
        self.pop_counter = 0
        self.gen_price = self.start_price
        self.gen_state = "STAGNANT"
        self.generate_steps(10)
    
    def get_next_state(self, current_state: str) -> str:
        probabilities = self.matrix[current_state]
        weights = [probabilities[s] for s in self.states]
        return random.choices(self.states, weights=weights)[0]

    def get_next_price(self, current_price: float, state: str) -> float:
        match state:
            case "BEAR":
                return current_price * random.uniform(0.95, 0.99)
            case "BULL":
                return current_price * random.uniform(1.01, 1.05)
            case "STAGNANT":
                return current_price * random.uniform(0.99, 1.01)
        return current_price

    def generate_steps(self, n: int) -> None:
        # Genera n nuovi passi e li aggiunge alla coda.
        for _ in range(n):
            self.gen_state = self.get_next_state(self.gen_state)
            self.gen_price = self.get_next_price(self.gen_price, self.gen_state)
            self.queue.append((self.gen_state, self.gen_price))

    def update_market(self) -> None:
        """
        Aggiorna il mercato consumando un passo dalla coda.
        Ogni 5 passi consumati, ne genera altri 10.
        """
        if not self.queue:
            self.generate_steps(10) # Check se la coda è vuota

        next_state, next_price = self.queue.pop(0)
        self.current_state = next_state
        self.current_price = next_price

        self.pop_counter += 1
        if self.pop_counter % 5 == 0:
            self.generate_steps(5)

class Wallet:
    # Rappresenta il portafoglio dell'utente contenente liquidità e azioni.
    def __init__(self, balance: float = 125000, stock: float = 0) -> None:
        self.balance = balance
        self.stock = stock

    def reset(self):
        self.balance = 125000 # Default start
        self.stock = 0

    def buy_stock(self, amount: float, price: float) -> bool:
        # Acquista una quantità di azioni se i fondi sono sufficienti.
        if self.balance >= amount * price:
            self.balance -= amount * price
            self.stock += amount
            return True
        return False

    def sell_stock(self, amount: float, price: float) -> bool:
        # Vende una quantità di azioni se possedute nel portafoglio.
        if amount <= self.stock:
            self.balance += amount * price
            self.stock -= amount
            return True
        return False

class Bankrupt:
    def __init__(self, wallet: Wallet, market: Market, grace_period: int = 30) -> None:
        self.wallet = wallet
        self.market = market
        self.grace_period = grace_period
        self.start_time = None 
        self.in_danger = False
        self.forced_danger = False
        self.time_spent_in_danger = 0.0

    def reset(self):
        self.forced_danger = False
        self.in_danger = False
        self.time_spent_in_danger = 0.0

    def update_risk(self, delta_time: float) -> bool:
        net_worth = self.wallet.balance + (self.wallet.stock * self.market.current_price)
        limit = self.market.start_price * 0.01
        
        if net_worth <= limit or self.forced_danger:
            self.in_danger = True
            
            # Incrementa il tempo passato in pericolo usando il delta time (solo quando il gioco corre)
            self.time_spent_in_danger += delta_time
            
            if self.time_spent_in_danger >= self.grace_period:
                # BANCAROTTA DEFINITIVA: Tempo scaduto
                self.wallet.balance = 0
                self.wallet.stock = 0
                self.market.current_price = 0   
                self.forced_danger = False # Reset flag
                return True
        else:
            self.in_danger = False
            self.time_spent_in_danger = 0.0 # Reset timer se si recupera
            
        return False

    def get_time(self) -> int:
        if not self.in_danger:
            return self.grace_period
        return max(0, int(self.grace_period - self.time_spent_in_danger))


class History:
    # Memorizza lo storico dei dati finanziari nel tempo per poter sviluppare il grafico.
    def __init__(self, wallet: Wallet, market: Market) -> None: 
        self.wallet = wallet
        self.market = market
        self.history = []

    def reset(self):
        self.history = []
    
    def save_history(self) -> None:
        self.history.append((self.wallet.balance, self.wallet.stock, self.market.current_price))    
    
    def get_history(self) -> list:
        return self.history