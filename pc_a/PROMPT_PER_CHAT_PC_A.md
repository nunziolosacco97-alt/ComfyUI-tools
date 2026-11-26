Copia il testo qui sotto come primo messaggio nella nuova chat di Claude sul PC A. Non contiene la chiave.

---

Ciao. Sei sul PC A di un progetto a due PC. Prima di fare qualsiasi cosa clona il repository pubblico e leggi per intero `pc_a/PC_A_LEGGIMI.md` (briefing con obiettivi, regole, stato, comandi). Rispetta le regole di quel file.

Riassunto: pipeline di immagini fisse; Blender produce passate (clay, colore, profondità) di una McLaren 765LT o GMC Hummer EV e un modello AI le trasforma in una foto senza deformare l'auto. Sul PC B girano i modelli offline in ComfyUI (Z-Image, MOSS, FLUX.2, P-H3, H3). Il tuo compito su questo PC A è solo **Nano Banana** via API Google, come confronto con gli altri.

Cosa fare, in ordine:
1. Esegui in PowerShell: `git clone https://github.com/nunziolosacco97-alt/ComfyUI-tools.git` (non usare `gh`), poi `cd ComfyUI-tools\pc_a`.
2. Leggi `pc_a/PC_A_LEGGIMI.md`, poi installa Pillow (`python -m pip install pillow`; se `python` non c'è, prova `py`).
3. Controlla la chiave senza mostrarla: `python nanobanana.py --check`. La chiave è nella variabile di sistema `GEMINI_API_KEY` e non deve mai comparire in chat, file, commit o log.
4. Fai un `--dry-run` su `city`, poi il primo test vero: `python nanobanana.py city 2 1K`. Poi `city 1 1K` e `city 3 1K`.
5. Guarda i risultati in `out/` e confrontali con `results/base/city/` (stesso seed 101) secondo i 4 criteri del briefing: fedeltà alla geometria, auto 765LT credibile e non plasticosa, niente scritte o manichini inventati, dettaglio. Dimmi onestamente dove Nano Banana è meglio e dove è peggio.
6. Solo dopo il mio ok, passa alle altre 7 scene (`trk_A`, `trk_B`, `trk_C`, `hum_1`..`hum_4`) e a 2K/4K.

Non installare né lanciare ComfyUI o modelli locali, non modificare file fuori da `out/`, non usare output di altri modelli come ingresso e non fare push senza il mio permesso.

Prima di cominciare conferma di aver letto il briefing riassumendo in 5 righe obiettivi e regole, poi parti dal punto 1.
