import json, time, os

class SettingsManager:
    def __init__(self) -> None:
        # Cartella Saves (condivisa con save_manager)
        self.save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Saves"))
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.settings_file = os.path.join(self.save_dir, "settings.json")

    def save_settings(self, appearance_mode, ui_scaling) -> None:
        """
        Salva le impostazioni correnti (Appearance, UI Scaling) su file JSON.
        """
        data = {
            "appearance_mode": appearance_mode,
            "ui_scaling": ui_scaling,
            "SAVED": time.time()
        }
        
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Impostazioni salvate in {self.settings_file}")
        except Exception as e:
            print(f"Errore durante il salvataggio delle impostazioni: {e}")

    def load_settings(self) -> dict:
        """
        Carica le impostazioni da file JSON e le restituisce.
        """
        if not os.path.exists(self.settings_file):
            print("Nessun file impostazioni trovato.")
            return None

        print(f"Caricamento impostazioni da {self.settings_file}...")
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            print("Impostazioni caricate con successo.")
            return data
        except Exception as e:
            print(f"Errore durante il caricamento delle impostazioni: {e}")
            return None
