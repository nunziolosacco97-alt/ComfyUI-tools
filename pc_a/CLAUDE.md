# Istruzioni per Claude Code sul PC A

Sei sul **PC A** di un progetto a due PC. Prima di fare qualsiasi cosa leggi per intero `PC_A_LEGGIMI.md` in questa cartella (obiettivi, criteri, regole, stato, comandi). Rispondi in italiano.

## Compito
Solo **Nano Banana** (`gemini-nano-banana-2.1`, API Google) con `nanobanana.py`, sulle passate Blender in `scenes/`, come confronto con i modelli offline del PC B (risultati in `results/base/`). Parti dalla scena `city`: `--check`, `--dry-run`, poi `python nanobanana.py city 2 1K`, poi refs 1 e 3. Le altre 7 scene e 2K/4K solo dopo l'ok dell'utente.

## Regole (non derogabili)
- La chiave sta solo nella variabile di sistema `GEMINI_API_KEY`. Non scriverla, stamparla, loggarla o metterla in file, commit o chat. Controllala solo con `--check`.
- Non installare né lanciare ComfyUI o modelli locali: li gestisce il PC B.
- Non modificare `scenes/`, `blender_demo/`, `results/`, `../scripts/` né i file degli altri modelli. Scrivi solo in `out/` (e, con permesso, in `results_nanobanana/`).
- Ingressi ammessi: solo `beauty_clay`, `beauty_color`, `depth` di Blender. Mai l'output di un altro modello.
- Nessun commit o push senza il permesso dell'utente. Mai force-push.
- Nano Banana è online: le immagini vanno a Google. Usa solo le scene di questo repo.
- Se un comando fallisce, riporta l'errore (senza la chiave) e fermati invece di improvvisare.

## Come riportare
Per ogni immagine: scena, refs, size, tempo, e giudizio sui 4 criteri (geometria di Blender, auto 765LT credibile e non plasticosa, niente scritte o manichini inventati, dettaglio) confrontato con i modelli offline sullo stesso seed 101. Di' chiaramente dove Nano Banana è peggio.

All'inizio della prima risposta riassumi in 5 righe obiettivi e regole, poi parti dal compito.
