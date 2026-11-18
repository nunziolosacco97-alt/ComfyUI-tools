# Verdetti sui modelli (un seed per modello, seed 7, salvo dove indicato)

**Finalisti:** Z-Image Turbo, MiniMax H3 Image, P-H3-Image, MOSS-Image, FLUX.2 [dev]. Seed 101/202/303 in corso.

- **Z-Image Turbo** (ControlNet profondità 0.8, fine 0.8, senza linee): resa preferita; con vincoli più forti (1.0 + linee) diventa piatto e deforma la figura.
- **MiniMax H3 Image**: apprezzato quanto Z-Image; richiede indizi nella clay (strada scura, marciapiede chiaro, figura con punte e tacchi).
- **P-H3-Image**: la scena è scarna col prompt breve; migliora con un prompt ricco di dettagli.
- **MOSS-Image + LoRA colore/profondità**: resa fotografica ricca, leggero banding sulla vernice, tendeva a scarpe da uomo.
- **FLUX.2 [dev]** (Turbo, 8 passi, ~190–205 s su Quadro RTX 5000): molto bello ma inventava manichini, insegne e strisce di strada; prompt v9 con divieti in positivo.

**Scartati:** SDXL RealVisXL (aspetto CG), LTX Layout-to-Render (45 min a immagine, non piaciuto), Qwen-Image-Edit 2511 e Qwen-Image 2.1 (ambiente povero, persona sbagliata), MiniMax H3 video con linee forti, Klein, HunyuanImage 3.0 (non entra in 16 GB).

**Lezioni:** nome nuovo per ogni test; almeno 3 seed; non vincolare troppo la guida; un solo lancio alla volta su ComfyUI; versioni int8/fp8 per la memoria.
