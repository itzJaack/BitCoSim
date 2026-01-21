import customtkinter as ctk

    
class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, close_callback=None, initial_appearance="Sistema", initial_scaling="100%"):
        super().__init__(master, fg_color="transparent")
        self.close_callback = close_callback
        self.initial_appearance = initial_appearance
        self.initial_scaling = initial_scaling
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container
        self.container = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray95", "gray10"))
        self.container.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(self.container, text="IMPOSTAZIONI", font=("Roboto", 20, "bold")).pack(pady=20)


        self.tabview = ctk.CTkTabview(self.container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.tab_general = self.tabview.add("Generale")
        self.tab_about = self.tabview.add("Info")
        
        # --- TAB GENERALE ---
        self.setup_general_tab()
        
        # --- TAB INFO ---
        self.setup_about_tab()
        

        if self.close_callback:
            ctk.CTkButton(self.container, text="CHIUDI", command=self.close_callback, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(pady=10)

    def setup_general_tab(self):
        # Frame Aspetto
        frame_appearance = ctk.CTkFrame(self.tab_general, corner_radius=10, fg_color="transparent", border_width=1, border_color="gray50")
        frame_appearance.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_appearance, text="ASPETTO VISIVO", font=("Roboto", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        row1 = ctk.CTkFrame(frame_appearance, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="Tema Applicazione:", font=("Roboto", 14)).pack(side="left", padx=5)
        self.option_appearance = ctk.CTkOptionMenu(row1, values=["Sistema", "Chiaro", "Scuro"], command=self.change_appearance_mode)
        self.option_appearance.set(self.initial_appearance)
        self.option_appearance.pack(side="right", padx=5)
        
        # Scaling
        frame_scaling = ctk.CTkFrame(self.tab_general, corner_radius=10, fg_color="transparent", border_width=1, border_color="gray50")
        frame_scaling.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_scaling, text="DIMENSIONI UI", font=("Roboto", 12, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        
        row2 = ctk.CTkFrame(frame_scaling, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row2, text="Zoom Interfaccia:", font=("Roboto", 14)).pack(side="left", padx=5)
        self.option_scaling = ctk.CTkOptionMenu(row2, values=["80%", "90%", "100%", "110%", "120%"], command=self.change_scaling_event)
        self.option_scaling.set(self.initial_scaling)
        self.option_scaling.pack(side="right", padx=5)

    def setup_about_tab(self):
        ctk.CTkLabel(self.tab_about, text="BitCoSim", font=("Roboto", 24, "bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self.tab_about, text="v1.0.0", font=("Roboto", 12)).pack(pady=5)
        ctk.CTkLabel(self.tab_about, text="Il simulatore di mercato definitivo.\nSviluppato con Python & CustomTkinter.", font=("Roboto", 14)).pack(pady=20)

    def change_appearance_mode(self, new_appearance_mode: str):
        mode_map = {"Sistema": "System", "Chiaro": "Light", "Scuro": "Dark"}
        ctk.set_appearance_mode(mode_map.get(new_appearance_mode, "System"))

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
