import json, time, os
from Libraries.settings import SettingsWindow

class SettingsManager:
    def __init__(self, settings_window: SettingsWindow) -> None:
        self.settings_window = settings_window
        
        # Cartella Saves (condivisa con save_manager)
        self.save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Saves"))
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        self.settings_file = os.path.join(self.save_dir, "settings.json")

    def save_settings(self) -> None:
        """
        Salva le impostazioni correnti (Appearance, UI Scaling) su file JSON.
        """
        data = {
            "appearance_mode": self.settings_window.option_appearance.get(),
            "ui_scaling": self.settings_window.option_scaling.get(),
            "SAVED": time.time()
        }
        
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Impostazioni salvate in {self.settings_file}")
        except Exception as e:
            print(f"Errore durante il salvataggio delle impostazioni: {e}")

    def load_settings(self) -> None:
        """
        Carica le impostazioni da file JSON e le applica alla finestra delle impostazioni.
        """
        if not os.path.exists(self.settings_file):
            print("Nessun file impostazioni trovato.")
            return

        print(f"Caricamento impostazioni da {self.settings_file}...")
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            
            # Applica Modalità Aspetto
            if "appearance_mode" in data:
                mode = data["appearance_mode"]
                self.settings_window.option_appearance.set(mode)
                self.settings_window.change_appearance_mode(mode)
            
            # Applica Scaling UI
            if "ui_scaling" in data:
                scaling = data["ui_scaling"]
                self.settings_window.option_scaling.set(scaling)
                self.settings_window.change_scaling_event(scaling)
            
            print("Impostazioni caricate con successo.")

        except Exception as e:
            print(f"Errore durante il caricamento delle impostazioni: {e}")
