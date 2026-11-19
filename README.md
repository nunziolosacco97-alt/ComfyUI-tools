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
