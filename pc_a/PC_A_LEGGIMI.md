# PC A: briefing completo (leggi tutto prima di fare qualsiasi cosa)

Questo file allinea il PC A con il PC B. Contiene gli obiettivi, cosa deve fare il PC A, cosa NON deve fare, lo stato dei risultati e i comandi.
Ultimo aggiornamento: 26 novembre 2026. Il lavoro finora è stato fatto da una sessione Claude sul PC B (Quadro RTX 5000, 16 GB, 68 GB RAM).

## 1. Obiettivo del progetto

Pipeline **solo immagini fisse**: Blender produce delle passate (clay, colore, profondità) di una scena con una McLaren 765LT (o un GMC Hummer EV) e un modello di intelligenza artificiale le trasforma in una **fotografia** credibile, senza deformare l'auto 3D.

Criteri di giudizio, in ordine di importanza:
1. **Fedeltà alla geometria di Blender**: stessa inquadratura, stessa posizione e forma dell'auto, stessa posizione della persona, stessa direzione delle ombre.
2. **Auto riconoscibile e credibile**: 765LT con alettone, presa d'aria, fari e cerchi corretti; vernice arancio papaya con riflessi veri, **non plasticosa** ("di pongo").
3. **Niente cose inventate**: scritte, insegne, loghi, manichini nelle vetrine, segni delle gomme che non seguono la curva.
4. Dettaglio fotografico (grana, texture di asfalto e pietra, pelle, tessuto).

Piano successivo: portare il risultato finale da SDR a HDR con LTX (PNG finale + EXR 16 bit lineare). Nano Banana su questo PC è un **confronto/riferimento**.

## 2. Cosa deve fare il PC A

- **Solo Nano Banana** (modello `gemini-nano-banana-2.1`, API di Google), sulle stesse passate Blender che usano gli altri modelli e con lo stesso testo di descrizione scena.
- Ordine: prima la scena `city` (McLaren con la donna che passa), poi le altre 7 scene. Prova refs 1, 2 e 3 a 1K, poi 2K/4K sulla variante migliore.
- Salvare i risultati in `out/` (lo script lo fa da solo) e riportarli: copiali sul PC B o in chat, oppure fai commit e push **solo** in `pc_a/results_nanobanana/`.
- Confrontare ogni risultato con quelli degli altri modelli in `results/base/<scena>/` secondo i 4 criteri sopra e riportare onestamente: dove è meglio, dove è peggio, cosa inventa.

## 3. Cosa NON deve fare il PC A

- **NON** installare né far girare ComfyUI o i modelli locali (Z-Image, MOSS, FLUX.2, P-H3, H3, SenseNova): li gestisce il PC B.
- **NON** modificare gli script in `scripts/`, i risultati degli altri modelli o i file in `scenes/` e `blender_demo/`.
- **NON** usare l'output di un altro modello come ingresso di Nano Banana: i modelli devono restare autonomi. Gli ingressi ammessi sono solo `beauty_clay`, `beauty_color`, `depth` di Blender.
- **NON** scrivere mai la chiave in file, commit, log o chat. Vive solo nella variabile di sistema `GEMINI_API_KEY`. Lo script non la stampa.
- **NON** fare push fuori da `pc_a/results_nanobanana/` e non fare force-push.
- Nano Banana è **online**: le immagini delle scene vengono inviate a Google. Va bene per questo confronto con scene di prova; non usarlo per materiale riservato.

## 4. Setup sul PC A (PowerShell)

`gh` non serve. Il repository è pubblico, basta Git:

```powershell
git clone https://github.com/nunziolosacco97-alt/ComfyUI-tools.git
cd ComfyUI-tools\pc_a
python -m pip install pillow
python nanobanana.py --check
python nanobanana.py city 2 1K --dry-run
```

- `--check` deve rispondere "GEMINI_API_KEY presente, lunghezza N". Dopo aver impostato una variabile di sistema serve **riaprire PowerShell** (o riavviare l'app).
- `--dry-run` costruisce la richiesta senza inviarla e senza costi.
- Se `python` non viene riconosciuto, prova `py` al posto di `python`; se manca anche quello, installa Python da python.org spuntando "Add python.exe to PATH".
- Se `git` non viene riconosciuto: `winget install --id Git.Git` e riapri PowerShell.

Primo test reale:

```powershell
python nanobanana.py city 2 1K
```

Poi `city 1 1K` e `city 3 1K`, poi le altre scene (`trk_A`, `trk_B`, `trk_C`, `hum_1` ... `hum_4`), poi `2K`/`4K`.

## 5. Contenuto della cartella `pc_a/`

| Percorso | Cosa contiene |
|---|---|
| `nanobanana.py` | Script autonomo per Nano Banana (nessuna dipendenza da ComfyUI) |
| `scenes/<scena>/` | `beauty_clay.png`, `beauty_color.png`, `depth.png` e `prompt.txt` per ognuna delle 8 scene |
| `blender_demo/` | Scena Blender demo `mclaren_scene_v2.blend` (città + McLaren + donna) e gli script `build_scene.py`, `render_passes.py`, `prep_inputs.py` che producono le passate |
| `results/base/<scena>/` | Risultati a risoluzione base (1280x768 circa) di Z-Image, FLUX.2, MOSS, P-H3, H3 per ogni scena; per `city` anche seed 202/303 e SenseNova |
| `results/4k_preview/` | Anteprime 1920x1152 dei render 4K (il 3840x2304 pieno resta sul PC B) |
| `../docs/risultati_4k/` | Fogli di confronto (originale / 4K / ritagli al 100%) |

Nota sul testo: `prompt.txt` è il prompt usato per FLUX.2 ("Edit the reference image: ..."). Parla di un'immagine di riferimento; con refs 2 o 3 Nano Banana riceve anche colore e profondità senza che il testo le nomini. In un secondo test puoi aggiungere una riga ("image 2 shows the real car colours and parts, image 3 is the depth map"): copia il testo in un file tuo, **senza cambiare l'originale**.

Scene: `city` = McLaren con donna che passa davanti a un colonnato (3 seed 101/202/303); `trk_A/B/C` = McLaren in pista; `hum_1..4` = GMC Hummer EV su cresta di montagna con Dolomiti.

## 6. Stato dei risultati sul PC B

Modelli offline finalisti, tutti con ricetta v10 e riferimenti Blender (clay + colore, tranne Z-Image e MOSS che usano la profondità):

| Modello | Cosa fa bene | Difetti noti |
|---|---|---|
| Z-Image Turbo | Veloce (circa 30 s a base, 6 min a 4K), fedele alla profondità | Ambiente povero; troppo denoise cancella i dettagli (0.25 è il valore giusto) |
| MOSS-Image | Fedele, buon volto a 4K con denoise 0.4 | Segni gomme sulla strada non seguono la curva; banding leggero |
| FLUX.2 [dev] | Ambiente più ricco, auto convincente | Manichini nelle vetrine, scritte inventate; licenza non commerciale |
| P-H3-Image | Scena ricca, 4K globale rapido (2-3 min) | Una seconda immagine rovina la composizione; segni gomme |
| MiniMax H3 Image | Asfalto molto bello; con 2ª ref l'auto non è plasticosa | Grana alta anche a denoise 0.25; segni gomme |
| SenseNova U1.6 (prova) | Resa pulita, 79 s con LoRA 8 step | Poco fedele al layout (donna ingrandita), auto generica e "di pongo", manca l'alettone; non finalista |

Render 4K (3840x2304) dentro il grafo del modello, senza upscaler esterno: l'originale è ingrandito, ricodificato a tile e rielaborato con **denoise parziale**. Denoise scelti: Z-Image, H3 e P-H3 0.25; MOSS e FLUX.2 0.4. Il 4K rende l'immagine più nitida ma **non corregge** i difetti dell'originale (segni gomme, scritte, manichini): vanno corretti alla fonte, nel prompt o nella clay (punto 4, non ancora fatto).

Lavori non finiti sul PC B (non toccarli dal PC A): seed 303 della scena `city` per FLUX.2 e MOSS, prove SenseNova a risoluzione maggiore e con prompt di texture, poi il punto 4 sui difetti. ComfyUI sul PC B era bloccato e va riavviato.

## 7. Cosa riportare dopo ogni test

Per ogni immagine di Nano Banana: scena, refs, size, tempo, e un giudizio sui 4 criteri confrontato con i modelli offline (stessa scena e stesso seed 101 per `city`). Segnala sempre se Nano Banana cambia inquadratura, sposta o ridimensiona persona o auto, inventa testo o oggetti, o ammorbidisce troppo la vernice. Se un risultato è peggiore degli altri dillo chiaramente: serve a scegliere, non a fare bella figura.
