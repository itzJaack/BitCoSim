@echo off
setlocal enabledelayedexpansion
title BitCoSim - Inizializzazione

:: Definizione codici colore ANSI per l'output
for /f "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set ESC=%%b
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "WHITE=%ESC%[97m"
set "RESET=%ESC%[0m"

:: Intestazione iniziale
echo %WHITE%==========================================%RESET%
echo %WHITE%            PREPARAZIONE GIOCO            %RESET%
echo %WHITE%==========================================%RESET%
echo.

:: Verifica se Python è installato nel sistema
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%[!] Python non trovato. Assicurati che sia installato e aggiunto al PATH.%RESET%
    pause
    exit /b 1
)

:: Installazione delle dipendenze Python necessarie
echo %WHITE%[1/3]%RESET% Verifica installazione librerie...
python -m pip install customtkinter pillow matplotlib requests >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[!] Errore durante l'installazione delle librerie.%RESET%
    echo %YELLOW%[!] Controlla la connessione internet o i permessi di sistema.%RESET%
) else (
    echo %GREEN%[OK] Librerie verificate.%RESET%
)
echo.

:: Controllo presenza del file CSV per lo storico
echo %WHITE%[2/3]%RESET% Controllo integrita' file salvataggio...
if not exist "storico_partite.csv" (
    echo %YELLOW%[!] File dei salvataggi non trovato, verra' creato automaticamente all'avvio.%RESET%
) else (
    echo %GREEN%[OK] File dei salvataggi rilevato.%RESET%
)
echo.

:: Avvio del file Python principale
echo %WHITE%[3/3] Avvio applicazione in corso...%RESET%
echo %WHITE%-------------------------------------------%RESET%
if exist "BitCoSim.py" (
    python BitCoSim.py
    if !errorlevel! neq 0 (
        echo.
        echo %RED%[X] Il programma si e' interrotto con un errore.%RESET%
        pause
    )
) else (
    echo %RED%[!] Errore: BitCoSim.py non trovato nella directory corrente.%RESET%
    echo %RED%[!] Assicurati che il file si trovi nella stessa cartella di questo script bat.%RESET%
    pause
)