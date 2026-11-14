# CLAUDE.md — Render fotorealistico di uno shot F1 da Blender con ComfyUI (offline)

> **AGGIORNAMENTO (novembre 2026) — metodo attuale: "circuito" (frame 39 di prova).** Le sezioni 3-5 sotto sono la storia del vecchio metodo (cartella `Test_controls`, scena `Test.blend`). Il lavoro attuale è nella cartella `TEST COMFYUI` (`scripts\`, `ref\`, `blender\Test_circuito.blend` non nel repo).
>
> Pipeline per un frame: `scripts\run_pipeline.sh <tag>` → Blender (`render_roadcar.py --circuit`, 9 frame di layout grigio con terreno, colline e foresta da `circuit_env.py`, motion blur reale) → `run_frame39.sh` → `run_f39.py` (LTX-2.5 distillato GGUF Q4_K_M + IC-LoRA layout-to-render, CFG 1, clip da 9 frame a 1536x896, si prende il frame centrale e si scala a 1280x768) → `finish_frame3.py` (Kontext ffclean, maschera auto BiRefNet, ali/halo in carbonio con maschere parti da `render_parts.py`, panning blur, grana/nitidezza asfalto, `grade.py`, `haze()`, `skyfix()`).
> Variabili utili: `LTX_SEED` (default 7; 11 usato nelle ultime), `TREE_SIDE=1 TREE_FRAME=39 TREE_XMAX=0.5` (alberi solo a sinistra), `NOSKYDEEP=1`, `FF_NOFR2=1`, `FF_ERODE`. Il prompt LTX in `run_f39.py` pesa molto sui colori ("warm"/"turquoise" sbagliano il cielo). Esempio: `LTX_SEED=11 TREE_SIDE=1 TREE_FRAME=39 TREE_XMAX=0.5 NOSKYDEEP=1 bash run_pipeline.sh e32` (~15-25 min, finisce con ALLDONE nel log `/tmp/<tag>.out`).
> Percorsi PC B: Python ComfyUI `...\ComfyUI-Installs\c\ComfyUI\.venv\Scripts\python.exe` sempre con `-I`; Blender 5.1.2 EEVEE. I `patch_v*.py` sono stati one-shot e non sono nel repo. Look desiderato: rosso uniforme lucido, carbonio nero, cielo blu profondo con cumuli, colline verdi con foschia azzurra, foresta solo a sinistra come massa scura bassa (ref `ref\stile_6…`), asfalto nitido, panning forte su cordoli, nessun logo leggibile.
> Prossimo: animazione a blocchi (adattare `run_chain.py` al metodo circuito), poi progetto Defender 1:1 su PC A.


> Leggi questo file per intero prima di fare qualsiasi cosa. Descrive obiettivo, stato, pipeline, regole, errori già fatti e prossimi passi.
> L'utente parla **italiano**: rispondi in italiano. Sii diretto e concreto, dai una raccomandazione, non un elenco di opzioni.

## 1. Obiettivo

Trasformare uno shot F1 "grezzo" fatto in Blender (monoposto stile Ferrari SF-26, rosso/bianco, **#44**, camera parentata alla macchina, **180 frame, 24 fps, 1920x1080**) in un render **fotorealistico**, che somigli a una foto di panning reale (riferimento: Hamilton/Ferrari, macchina nitida, sfondo con motion blur orizzontale, ombra naturale).

Vincoli:
- **Tutto locale/offline** con ComfyUI (niente API a pagamento o cloud).
- La **strada deve seguire la macchina** (il bordo pista deve essere quello della scena Blender).
- L'**ombra deve essere naturale**: l'utente ha rifiutato l'ombra di Blender ("terribile"). Si usa **solo l'ombra generata dal modello AI**.
- I **loghi/sponsor** vanno aggiunti come **decal** composti sopra (già renderizzato il layer decal).
- **Output pensato per DaVinci Resolve**: serve la fase di post per il color grade, quindi in uscita servono **16 bit / EXR / HDR** (float), non solo PNG 8 bit. Non ancora implementato.
- Poco sfarfallio (flicker) tra i frame.

## 2. Due macchine

- **PC B** (questo, dove è stato fatto il lavoro finora): Windows 11, GPU **Quadro RTX 5000 16 GB (Turing)**, 64 GB RAM, ComfyUI Desktop 0.44.
- **PC A**: dove l'utente userà il repo. Il repo serve a portare tutto lì. Non assumere stessi percorsi, stessa GPU o stessi modelli: verifica prima.
- Repo: https://github.com/nunziolosacco97-alt/ComfyUI-tools — **non ancora caricato**. L'utente ha detto: carica tutto solo quando si arriva alle fasi definitive, e **solo dopo la sua richiesta/conferma**. Non fare push di tua iniziativa. Nel repo NON vanno i modelli (decine di GB), né frame/video generati, né il `.blend`; solo script, workflow JSON e questo file. Un `.gitignore` per `*.safetensors`, `*.gguf`, `*.png`, `*.mp4`, `*.blend` va creato prima del primo commit.

## 3. Percorsi su PC B (da adattare su PC A)

- Script e workflow: `C:\Users\Internet\Desktop\Test_controls\`
- ComfyUI API: `http://127.0.0.1:8188`
- Python di ComfyUI (usare questo, con `-I`): `C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Installs\c\ComfyUI\.venv\Scripts\python.exe`
- Modelli: `C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared\models` (`unet`, `loras`, `text_encoders`, `vae`, ...); input: `...\ComfyUI-Shared\input`; output: `...\ComfyUI-Shared\output`
- Blender: `C:\Users\Internet\Documents\Blender\blender-5.1.2-windows-x64\blender.exe`; scena `C:\Users\Internet\Desktop\Test.blend` (**non viene mai salvata dagli script**: gli script modificano la scena in memoria e fanno render in batch con `-b`).
- Cartelle di lavoro sul Desktop: `Test_sem` (render semantici), `Test_masks` (maschere macchina), `Test_final` (frame finiti), `Test_comp`, `Test_shadows`, `Test_decals`, `Test_ltx` (test LTX).
- Il server ComfyUI Desktop a volte non parte da solo: serve aprire `Comfy Desktop.lnk` e aspettare qualche minuto (il log è in `ComfyUI-Installs\c\logs\comfyui.log`). Se l'utente chiude l'app durante una generazione, il job muore: rilancia e rigenera i frame mancanti. Non dare la colpa all'utente.

## 4. Pipeline A — frame singoli con Wan 2.2 Fun Control (funziona, è il riferimento di qualità)

1. `render_semantic.py` (Blender, `-b`): renderizza la sequenza **semantica**: macchina grigio argilla, ROAD scuro, GRASS verde, cielo pallido → `Desktop\Test_sem\sem_0001..0180.png`. Dà al modello il vero bordo strada. Oggetti nella scena: strada `NurbsPath.001`, terreno `Plane`.
2. `run_semantic_stills.py <frame...>` (usa `wan22_fun_control_single_semantic.json`): Wan 2.2 Fun Control A14B (High/Low noise GGUF Q4_K_M), `Wan22FunControlToVideo` con ref_image `f1_reference_clean.png`, **senza LoRA**, 20 step, cfg 3, uni_pc, KSamplerAdvanced diviso 0–10 / 10–fine, 848x480, seed **21 fisso** (stesso seed per tutti i frame, riduce il flicker), ~105–130 s/frame. Output `output\sem\fXXXX_*.png`.
3. `run_car_masks.py`: maschere macchina con BiRefNet → `Test_masks\mask_XXXX.png`.
4. `pan_blur_region.py <plate> <car_mask> <sem_render> <out> [length=50]`: motion blur orizzontale **solo sullo sfondo fuori pista** (erba/cielo, dal render semantico), con margine da bordo strada e macchina. Il blur su tutto lo sfondo creava aloni su ruote/muso.
5. `finish_range.ps1 -a N -b M`: maschere + blur → `Test_final\final_XXXX.png` (frame 80, 85–103 fatti). `temporal_bg.py <first> <last>`: smoothing temporale dello sfondo (pesi 1,2,3,2,1) → `smooth_XXXX.png`.
6. Upscale a 1920x1080 sulle immagini finali.

Cose provate e scartate (non rifarle):
- **Ombra di Blender** (ratio, mask, soft, contact shadow): dava doppia ombra/ombra galleggiante → scartata. Si usa solo l'ombra del modello. (File `contact_shadow.py`, `soft_shadow.py`, `comp_shadow*.py`, `render_shadow_layer.py` restano solo come archivio.)
- **Clip video Wan** da 33 e 17 frame: strisce, kerb sbagliati, asfalto marrone a bande, deriva verso look plastico → peggio degli still.
- Seed 22/23 sul frame 88: peggio del 21.

Limiti noti: alone leggero sull'asfalto davanti al muso; frame 81–84 e oltre il 103 non generati.

## 5. Pipeline B — LTX-2.5 Layout-to-Render (test riuscito, promettente per il video)

Script: `run_ltx_l2r.py` (`--seed`, `--style 1/0`, `--ic 1.0`, `--tag`, `--w`, `--h`, `--n`). Workflow costruito in codice (non c'è JSON esportato).

Modelli in `models/` (tre sono **gated su Hugging Face**: li scarica l'utente dopo aver accettato la licenza; non scaricarli tu):
- `unet/ltx-2.5-22b-distilled-Q4_K_M.gguf` (13,6 GB, da unsloth/LTX-2.5-GGUF, caricato con `UnetLoaderGGUF`)
- `loras/ltx-2.5-22b-ic-lora-layout-to-render-1.0.safetensors` (1,2 GB)
- `text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors` (24,5 GB; esiste variante int8 convrot più leggera)
- `vae/ltx-2.5-video-vae-conv-bf16.safetensors` (1,35 GB)

Catena nodi: `UnetLoaderGGUF` → `LoraLoaderModelOnly` (IC-LoRA) ; `CLIPLoader` type `ltxv` (Gemma) ; `LTXVConditioning` 24 fps ; `LoadVideo` (layout grigio .mp4 in `input`) → `GetVideoComponents` ; `EmptyLTXVLatentVideo` ; `GetICLoRAParameters` (input `iclora_model` = **uscita del LoraLoader**, non il nome file) → `LTXVAddGuide` (layout come guida, frame_idx 0, strength 1.0, `iclora_parameters`) ; frame di stile (`style_85.png`, il frame 85 finito) via `LTXVImgToVideoInplace` strength 0.9 ; `RandomNoise` + `KSamplerSelect euler` + `ManualSigmas` distillato `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0` + `CFGGuider` **cfg 1.0** + `SamplerCustomAdvanced` ; `LTXVCropGuides` ; `VAEDecodeTiled` (tile 512, temporal 32) → `SaveImage` in `output\ltx\`.

Regole LTX: frame = **8n+1** (65, 97, 121); larghezza/altezza **multipli di 64**; senza audio latent funziona (video-only), il file Audio VAE non è stato necessario.

Risultati sul PC B:
- 97 frame a 1024x576 → **OOM** sui 16 GB.
- **65 frame a 768x448** (frame 84–148 dello shot) → OK, ma **5993 s (~100 min)**. Qualità fotorealistica buona, macchina e ombra coerenti, nessuna stria evidente. 768x448 è leggermente schiacciato rispetto a 16:9.
- File: `Desktop\Test_ltx\ltx_b_24fps.mp4`, `ltx_b_sheet.png`, `layout_65_768.mp4`.

## 5b. Pacchetti da scaricare e dove metterli (checklist per PC A)

Percorso base su PC B: `C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared\models\` (su PC A: la cartella `models` di ComfyUI; le sottocartelle sono quelle standard). Dopo aver spostato i file serve riavviare ComfyUI. Le cartelle che mancano vanno create.

| File | Cartella in `models/` | Dimensione | Origine / note |
|---|---|---|---|
| `Wan2.2-Fun-A14B-Control_HighNoise-Q4_K_M.gguf` | `unet` | ~9 GB | GGUF di Wan 2.2 Fun Control (High noise), per la pipeline A |
| `Wan2.2-Fun-A14B-Control_LowNoise-Q4_K_M.gguf` | `unet` | ~9 GB | idem (Low noise) |
| VAE e text encoder di Wan 2.1/2.2 (`wan_2.1_vae.safetensors`, `umt5_xxl_fp8_e4m3fn_scaled.safetensors`) | `vae`, `text_encoders` | — | usati da `wan22_fun_control_single_semantic.json` |
| BiRefNet (modello rimozione sfondo) | quello richiesto dal nodo `LoadBackgroundRemovalModel` | — | maschere macchina |
| `ltx-2.5-22b-distilled-Q4_K_M.gguf` | `unet` | 13,6 GB | libero, da unsloth/LTX-2.5-GGUF |
| `ltx-2.5-22b-ic-lora-layout-to-render-1.0.safetensors` | `loras` | 1,2 GB | **gated**, Lightricks/LTX-2.5-22b-IC-LoRA-Layout-To-Render |
| `ltx-2.5-22b-ic-lora-sdr-to-hdr-1.0.safetensors` | `loras` | 1,2 GB | **gated**, Lightricks/LTX-2.5-22b-IC-LoRA-SDR-To-HDR |
| `ltx-2.5-22b-ic-lora-alpha-gen-0.9.safetensors` | `loras` | 1,2 GB | **gated**, Lightricks/LTX-2.5-22b-IC-LoRA-Alpha-Gen (Beta) |
| `ltx-2.5-22b-ic-lora-sdr-to-hdr-scene-emb.safetensors` | `embeddings` (creare la cartella) | 12 MB | embedding di scena per l'SDR→HDR; lo legge il nodo `LTXVLoadConditioning` di ComfyUI-LTXVideo da `models/embeddings` |
| `gemma4-12b-with-proj-ltx-2.5-bf16.safetensors` | `text_encoders` | 24,5 GB | **gated**; esiste la variante `...comfy-int8-convrot` più leggera |
| `ltx-2.5-video-vae-conv-bf16.safetensors` | `vae` | 1,35 GB | **gated**, Lightricks/LTX-2.5 |

Custom node (in `ComfyUI\custom_nodes\`, non in `models`):
- `ComfyUI-GGUF` (già presente): `UnetLoaderGGUF`.
- `ComfyUI-LTXVideo` (repo ufficiale `https://github.com/Lightricks/ComfyUI-LTXVideo`, `git clone --depth 1`): nodi HDR/EXR/alpha (`LTXVLoadEXRSequence`, `LTXVVAEForceFloat32`, `LTXVHDRDecodePostprocess`, `LTXVSaveHLG`, loader embeddings). Workflow di esempio in `example_workflows/2.5/` (es. `LTX-2.5_ICLoRA_SDR_to_HDR_Distilled.json`, `LTX-2.5_V2V_TiledFusion_SDR_to_HDR.json`).
- Dipendenze Python da installare nel venv di ComfyUI: `pip install colour-science openimageio diffusers` (le altre — einops, kornia, transformers, huggingface_hub — erano già presenti; `ninja` non serve installarlo se non si compila nulla).
- Nodi nativi di ComfyUI già disponibili: `ImageSDRToHDR` (espansione Lottes → Rec.2020 HLG), `ImageColorSpace`, `SaveImageAdvanced` (formato `exr`, input `sRGB`/`HDR`/`linear`/`linear ACEScg`). Non sono il LoRA di LTX: sono conversioni matematiche.

Note HDR/alpha da documentazione LTX: il loader EXR di ComfyUI tiene solo i primi 3 canali, quindi l'alpha non passa in EXR e va salvata a parte. L'IC-LoRA SDR→HDR lavora in ACEScct. I file gated li scarica l'utente dopo aver accettato la licenza su Hugging Face; poi li si sposta nelle cartelle sopra.

## 5c. Flusso colore deciso con l'utente

PNG 8 bit sRGB come riferimento visivo → IC-LoRA SDR→HDR di LTX → EXR scene-linear (senza color output/tonemap applicato) per il grade in DaVinci Resolve. Alpha (AlphaGen) a parte, se serve.

## 6. Problema aperto principale: lo shot è "statico" (risolto con il nuovo shot, vedi 6b)

I frame dell'output LTX cambiano pochissimo. Misurato: anche il layout grigio cambia pochissimo (differenza media 0,7–2,5 su 255 in 64 frame; frame 84 vs 180: 3,1). Causa: **camera parentata alla macchina + strada ed erba uniformi** → niente riferimenti che scorrono. Non è un difetto di LTX: segue il layout.

Soluzione concordata (in corso, la fa l'utente in Blender): dare **più dinamica alla macchina** (movimento più marcato, ruote ferme per ora). Altre idee proposte, da fare se serve: kerb a righe, linee bianche, pali, alberi e cartelli lungo il bordo pista, rotazione ruote, leggero movimento/vibrazione camera; in alternativa parallasse dello sfondo in compositing (meno credibile). Dopo che l'utente ha rifatto lo shot: **rigenerare** `Test_sem` (`render_semantic.py`), rifare il layout video, rilanciare LTX e/o Wan.

### 6b. Nuovo shot dinamico (11/11/2026)

L'utente ha rifatto lo shot in `Test.blend` (macchina con movimento più marcato, ruote ancora ferme). Render semantico nuovo in `Desktop\Test_sem2\sem_0001..0180.png` (la differenza tra frame 1 e 180 è ~51, contro ~3 del vecchio). Vista tre quarti frontale, orizzonte inclinato, bordo pista che entra ed esce. Il vecchio frame di stile 85 (vista laterale) **non va più usato** come primo fotogramma: per LTX serve un nuovo frame di stile generato con la pipeline A sul nuovo shot (`run_semantic_stills.py` ora legge `Test_sem2` e salva in `output\sem2\`). Blocchi LTX da 65 o 97 frame (l'utente accetta tempi lunghi).

## 7. Prossimi passi (in ordine)

1. Aspettare lo shot Blender più dinamico dell'utente, poi rigenerare i render semantici e ripetere il test LTX (confrontare con gli still Wan).
2. Estendere a tutto lo shot a blocchi (65 frame con 768x448) oppure testare risoluzione più alta con offloading/int8; upscale finale a 1920x1080.
3. Comporre i **decal** (`render_decal_layer.py` → `Test_decals\decal_0001..0180.png`; `comp_decals.py` esiste) sopra i frame.
4. Uscita **16 bit/EXR** per DaVinci (non ancora affrontata: i PNG attuali sono 8 bit; LTX può usare VAE float32).
5. Ripulire l'alone davanti al muso; frame 81–84 e >103 per la pipeline A.
6. Quando l'utente lo chiede: `.gitignore`, commit e push su `nunziolosacco97-alt/ComfyUI-tools` (script, JSON, CLAUDE.md, README breve con come ricreare l'ambiente su PC A).
7. **Per dopo (non adesso): MiniMax H3** Ref2Video (file Comfy-Org/MiniMax-H3 non scaricati; la licenza escludeva EU/UK/Korea/US e la compatibilità con GPU Turing è incerta → verificare prima).

## 8. Regole di lavoro con questo utente

- Prima di scaricare file grossi o gated: **chiedi** (nome, fonte, dimensione). I file gated li scarica lui; tu li sposti nelle cartelle giuste.
- Non salvare mai `Test.blend`; non sovrascrivere i suoi file senza guardare.
- Non inventare risultati: guarda sempre le immagini/frame prima di dire che funziona; dichiara errori e OOM com'erano.
- Usa il Python del venv di ComfyUI con `-I`. `ffmpeg` non c'è: per gli mp4 usa PyAV (libx264) nel venv.
- Job lunghi (>2 min) in background. Non lanciare due job ComfyUI insieme su 16 GB.
- Non fare push né pubblicare nulla senza richiesta esplicita.

## Riferimenti di stile (cartella ../ref) — 13/11/2026
Tutto il lavoro vive in `Desktop\TEST COMFYUI` (blender, scripts, ref, frames, render, archivio). Unico file Blender: `blender\Test_circuito.blend` (circuito + camera pitch 8° / shift_y -0.09 + motion blur shutter 0.5 già inclusi).
Reference dell'utente (`stile_*.jpg`): foto pubblicitarie auto (Porsche/BMW DTM), look cinematico:
- stile_2 e stile_3 (BMW bianca) = RIFERIMENTO PRINCIPALE per ambiente e cielo: cielo blu profondo con grandi cumuli bianchi, dolci colline erbose verdi con file di alberi scuri, cordoli rosso/bianchi, asfalto con panning motion blur orizzontale molto forte in primo piano, contrasto alto, grading teal-blu.
- stile_1: dusk verde-azzurro, colline basse desertiche lontane, cordoli rossi sfocati in primo piano.
- stile_4: nuvole scure drammatiche con raggi di sole, colline coltivate, alberi, muretti lontani.
- stile_5: dusk blu, tribune a tenda bianca, cordoli molto sfocati in primo piano.
Regole utente: niente cubi di sfondo (usare colline/prati/alberi), motion blur DIREZIONALE (non blur gaussiano), auto sempre nitida; tracce di gomma solo se realistiche (tolte per ora); ali+halo neri, muso rosso (maschere parti da render_parts.py); mai cancellare file senza chiedere.
