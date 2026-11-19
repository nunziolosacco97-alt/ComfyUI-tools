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

## Secondo giro: ricetta v10 (varianti sullo stesso set di 3 seed)

Dopo che le nuove varianti di H3 (riferimento carrozzeria) e MOSS (griglia fissata nel prompt, mappa colore) sono piaciute, la stessa ricetta è stata provata sugli altri modelli: 24 immagini, seed 101/202/303, script `*_v10.py` (generati da `mk_v10.py`).

La ricetta ha due ingredienti: (1) descrizione dell'auto più precisa ("papaya orange profondo, saturo, lucido, non giallo; stessa griglia, presa d'aria, fari, splitter, ruote e alettone del riferimento") con termini negativi aggiuntivi dove il modello li supporta; (2) una seconda immagine di riferimento per la carrozzeria.

| Modello | Varianti | Esito (giudizio a occhio sui fogli contatti) |
|---|---|---|
| MOSS-Image | v10: colore + profondità, fine controllo 0.8 / 1.0 | Scelta: **fine 1.0** (griglia e presa d'aria più fedeli al Blender). |
| MiniMax H3 Image | D/E: seconda ref = risultato FLUX / Z-Image; F/G: D/E più frase sulla griglia | La seconda ref risolve l'aspetto plasticoso dell'auto (D/E scelti). F/G quasi uguali a D/E: la frase sulla griglia aggiunge poco; sui seed 101 la vernice vira al rosso. |
| Z-Image Turbo | A: solo nuovo prompt; B: profondità 1.0 + linee 0.4 | A quasi identica alla v6, vernice un po' più lucida. B ha geometria più stretta, persona un po' più piatta: differenza marginale. |
| FLUX.2 [dev] | A: nuovo prompt; B: in più il render a colori come seconda ReferenceLatent | Poca differenza. Restano i manichini nelle vetrine in tutti e 3 i seed (anche nella base): i divieti nel prompt non bastano. B non porta un guadagno visibile. |
| P-H3-Image | A: nuovo prompt; B: in più il risultato FLUX come seconda immagine | A leggermente più lucida della base. B **peggiora**: la composizione deriva (camera, auto più grande, persona minuscola, cordolo rotto). Da non usare. |

Lezione: cambiare solo le parole sposta poco; una seconda immagine di riferimento sposta molto, ma solo i modelli progettati per le reference multiple la gestiscono (H3 Image sì, P-H3 no).
