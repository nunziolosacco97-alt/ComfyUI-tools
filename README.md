# McLaren 765LT: scena Blender + ComfyUI

Pipeline solo-immagine: Blender produce passate grezze (clay, depth, maschere) di una scena fissa (camera 50 mm, 1280×768) e vari modelli locali in ComfyUI le trasformano in una foto. Questo repository contiene i **workflow dei 5 finalisti**, gli script usati per generarli e una guida di studio.

## Workflow dei finalisti (`workflows/`)

Formato **API di ComfyUI** (un nodo per voce, con `class_type` e `inputs`). Si inviano con `tools/run_workflow.py` oppure, nelle versioni recenti dell’interfaccia, trascinando il file JSON sul canvas (non verificato su tutte le versioni).

| File | Modello | Guida | Passi |
|---|---|---|---|
| `1_z_image_turbo_depth.json` | Z-Image Turbo | profondità (ControlNet) | 8, cfg 1 |
| `2_minimax_h3_image_edit.json` | MiniMax H3 Image | immagine di riferimento (clay) | 6, cfg 1 |
| `3_p_h3_image_edit.json` | P-H3-Image (Pruna) | riferimento + LoRA | 8 sigma, er_sde |
| `4_moss_image_depth.json` | MOSS-Image + LoRA | profondità | 25, cfg 3 |
| `5_flux2_dev_turbo_edit.json` | FLUX.2 [dev] + Turbo LoRA | riferimento (ReferenceLatent) | 8 |

Sono i grafi esatti dei test con seed 7. I file dei modelli (nomi nei nodi `UNETLoader`, `CLIPLoader`, `VAELoader`, `LoraLoaderModelOnly`) vanno scaricati a parte dalle pagine ufficiali: **qui non ci sono modelli né immagini**. Leggi le licenze (MiniMax H3 Community, FLUX.2 [dev] non commerciale).

## Uso

```bash
# ComfyUI acceso; clay e depth in ComfyUI/input/mcl13/ (beauty_clay.png, depth.png)
python tools/run_workflow.py workflows/1_z_image_turbo_depth.json 101
```

Gli script in `scripts/comfy/` (compresi `flux2_dev_v9.py`, `moss_v9.py`, `run_seeds2.sh`/`run_seeds3.sh` del lotto a 3 seed) sono la versione Python dei workflow (uno per modello, `cx.py` è l’helper). Variabili: `COMFY_SHARED` (cartella ComfyUI-Shared), `INF` (sottocartella di input, default `mcl3`). Con `DUMP_DIR=cartella` gli script esportano il JSON senza eseguirlo.

## Resto del repository

- `scripts/blender/`: `render_passes.py` (passate: clay, depth, normali, ID, maschere), `prep_inputs.py` (ridimensiona e prepara gli input), `build_scene.py` (scena iniziale, superata). Servono Blender 5.1 e la tua scena `.blend` (non inclusa).
- `docs/guida_slides/`: sorgente della guida di studio a diapositive (23 slide, in italiano).
- `docs/modelli.md`: verdetti sui modelli provati.

## Prossimi passi

Test a 3 seed completato, poi secondo giro con la ricetta v10 (vedi `docs/modelli.md`): MOSS v10 (fine 1.0) e H3 D/E in testa. Restano: armonizzazione auto/ambiente, poi LTX SDR→HDR per l’EXR 16 bit lineare.

## Render 4K nel grafo (senza upscaler esterno)

`scripts/comfy/hr_gen.py MODELLO SCENA VISTA MODO [denoise] [seed]` rifà il render a 3840x2304 dentro il grafo del modello: l'originale 1280x768 è ingrandito (lanczos), codificato con VAE a tile e rielaborato con denoise parziale (0.4) dallo stesso modello. Profondità, clay e colore sono ridimensionati, mai presi da un altro modello. Modi: `g` (passata globale) e `t` (tile sovrapposte, fusione con rampe lineari). Strategia usata: tile per Z-Image, MOSS, H3 e FLUX.2; globale per P-H3 (FLUX.2 globale manda in crash ComfyUI su 16 GB).

- `run_hr_all.sh` lancia tutte le viste (McLaren A, B, C; Hummer 1-4), `wait_view.sh` e `sheet_hr.py` costruiscono i fogli di confronto.
- `trk_gen.py` / `hum_gen.py`: generatori dei grafi per la pista McLaren e per l'Hummer in montagna; `stage_*.py` preparano gli input.
- Tempi per immagine: Z-Image 6 min, P-H3 3,5, MOSS 18, H3 17, FLUX.2 27.
- `docs/risultati_4k/`: fogli di confronto (originale | 4K | ritagli al 100%) e fogli degli originali. Le immagini a piena risoluzione non sono nel repository.

## Scena città (McLaren con la donna) e prove di denoise

- Scena `city` in `hr_gen.py` (input `mcl13`, ricette v10, seed 101/202/303): `sheet_city.py`, `run_hr_city.sh`, `run_city_seeds.sh SEED...`.
- Denoise 4K scelti: Z-Image, H3 e P-H3 a 0.25; MOSS e FLUX.2 a 0.4 (a 0.25 MOSS perde nitidezza sul volto, FLUX.2 resta uguale). Confronti in `docs/risultati_4k/den_*_city.jpg` (`cmp_den.py`) e `d25_*_tutte.jpg` (`sheet_d25.py`, `run_d25.sh`, `run_d_test.sh`).
- SenseNova U1.6 (8B, Apache 2.0, nodi nativi ComfyUI): `sensenova_v10.py SEED L|N [refs] [W H] [tex]`, riferimenti clay + colore Blender. Confronto in `docs/risultati_4k/sensenova_confronto.jpg`: bello ma poco fedele al layout, auto "di pongo"; prove a risoluzione più alta e prompt di texture in `run_sn_test.sh` (da eseguire).
- Nota: un job FLUX.2 può bloccare ComfyUI senza errore; serve un timeout per tile.

## PC A (Nano Banana)

La cartella `pc_a/` allinea il secondo PC: briefing in `pc_a/PC_A_LEGGIMI.md`, testo da incollare nella chat in `pc_a/PROMPT_PER_CHAT_PC_A.md`, script autonomo `pc_a/nanobanana.py` (legge la chiave solo da `GEMINI_API_KEY`), le passate Blender di 8 scene in `pc_a/scenes/`, la scena demo in `pc_a/blender_demo/` e i risultati degli altri modelli in `pc_a/results/`.
