# Verdetti sui modelli

**Finalisti:** Z-Image Turbo, MiniMax H3 Image, P-H3-Image, MOSS-Image, FLUX.2 [dev]. Test finale con 3 seed (101, 202, 303) per ciascuno: 15 immagini, tutte soddisfacenti.

## Esito dei 3 seed

- **FLUX.2 [dev]** (Turbo, 8 passi, ~185 s su Quadro RTX 5000) e **MOSS-Image + LoRA colore/profondità**: livello superiore agli altri.
- **Z-Image Turbo** (profondità 0.8, fine 0.8): resa preferita nei test iniziali, ~30 s a immagine.
- **MiniMax H3 Image**: asfalto molto bello, ma con l'avanzare dei seed la resa è diventata più plastica e l'auto ne esce rovinata. Da usare con cautela.
- **P-H3-Image**: la scena è scarna col prompt breve; migliora con un prompt ricco (variante `p_h3_rich`).

## Note per modello

- Z-Image: con vincoli più forti (1.0 + linee) diventa piatto e deforma la figura.
- H3 Image: richiede indizi nella clay (strada scura, marciapiede chiaro, figura con punte e tacchi).
- MOSS: leggero banding sulla vernice; tendeva a scarpe da uomo, risolto nel prompt v9.
- FLUX.2: inventava manichini, insegne e strisce di strada; il prompt v9 usa divieti in positivo.

## Scartati

SDXL RealVisXL (aspetto CG), LTX Layout-to-Render (45 min a immagine), Qwen-Image-Edit 2511 e Qwen-Image 2.1 (ambiente povero, persona sbagliata), MiniMax H3 video con linee forti, Klein, HunyuanImage 3.0 (non entra in 16 GB).

## Lezioni

Nome nuovo per ogni test; almeno 3 seed; non vincolare troppo la guida; un solo lancio alla volta su ComfyUI; versioni int8/fp8 per la memoria; non aggiornare/riavviare ComfyUI durante un lotto.
