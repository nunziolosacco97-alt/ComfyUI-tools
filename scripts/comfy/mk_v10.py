CAR = "a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing"
NEGADD = ", yellow car, matte paint, different front bumper, redesigned grille"
HEAD = 'CAR = %r\nPROMPT = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)\n' % CAR
# ---- Z-Image: A = prompt only (as v6), B = depth 1.0 end 1.0 + lines 0.4
s = open("zimage.py").read().replace("from cx import *\n", "from cx import *\n" + HEAD, 1).replace('"zimage_v6_sidewalk_%s_s%d_d%g_e%g_l%g"', '"zimage_v10_%s_s%d_d%g_e%g_l%g"')
open("zimage_v10.py", "w").write(s)
# ---- FLUX.2: arg3 var A (wording) / B (wording + colour render as 2nd reference)
s = open("flux2_dev_v9.py").read().replace("from cx import *\n", "from cx import *\n" + HEAD, 1)
s = s.replace("turbo = int(sys.argv[2]) if len(sys.argv) > 2 else 1", "turbo = int(sys.argv[2]) if len(sys.argv) > 2 else 1; var = sys.argv[3] if len(sys.argv) > 3 else 'A'")
s = s.replace('model = ["12", 0]\n', 'if var == "B": EDIT += "A second reference image shows the real car with its true colour and parts: copy the paint colour, the front grille, the air intake and all car parts exactly from it. "\nmodel = ["12", 0]\n', 1)
s = s.replace('if turbo:\n    g["88"]', 'cond = ["39", 0]\nif var == "B":\n    g["45b"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}}\n    g["41b"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["45b", 0], "upscale_method": "area", "megapixels": 1.0, "resolution_steps": 1}}\n    g["40b"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["41b", 0], "vae": ["10", 0]}}\n    g["39b"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["39", 0], "latent": ["40b", 0]}}; cond = ["39b", 0]\nif turbo:\n    g["88"]')
s = s.replace('"conditioning": ["39", 0]}}\ng["48"]', '"conditioning": cond}}\ng["48"]').replace('"flux2dev_v9_%s_s%d" % ("turbo" if turbo else "full", seed)', '"flux2dev_v10%s_%s_s%d" % (var, "turbo" if turbo else "full", seed)')
open("flux2_dev_v10.py", "w").write(s)
# ---- P-H3-Image: A wording only, B wording + FLUX body as 2nd ref
s = open("p_h3_rich.py").read()
s = s.replace("from cx import *\n", "from cx import *\n" + HEAD, 1).replace("seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7", "seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; var = sys.argv[2] if len(sys.argv) > 2 else 'A'", 1)
s = s.replace('A papaya orange McLaren 765LT is parked', 'A " + CAR + " is parked')
s = s.replace('g = {\n', 'if var == "B": REQ = "Edit Picture 1: " + REQ + " Picture 2 is a real photograph of the same car: copy its paint colour, body surfaces, reflections, grille, air intake and wheels onto the car of picture 1, keeping position and shape from picture 1."\ng = {\n', 1)
s = s.replace('run(g, "ph3image_v8_rich_s%d" % seed)', 'if var == "B":\n    g["27"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/ref_flux_s%d.png" % seed}}\n    g["28"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["27", 0], "upscale_method": "lanczos", "megapixels": 0.95, "resolution_steps": 32}}\n    g["9"]["inputs"]["images.image_2"] = ["28", 0]\nrun(g, "ph3image_v10%s_s%d" % (var, seed))')
open("p_h3_v10.py", "w").write(s)
# ---- MiniMax H3 Image: F = FLUX ref + wording, G = Z-Image ref + wording
s = open("minimax_img_v8.py").read().replace("from cx import *\n", "from cx import *\n" + HEAD, 1)
s = s.replace('if var in ("D","E"): EDIT +=', 'if var in ("F","G"): EDIT += "The car must keep its exact design from picture 1: same front grille, same front air intake, same headlights and wheels. "\nif var in ("D","E","F","G"): EDIT +=', 1)
s = s.replace('if var in ("D","E"): nref = 2', 'if var in ("D","E","F","G"): nref = 2').replace('if var == "D" else ("ref_zimage_s%d.png" % seed) if var == "E"', 'if var in ("D","F") else ("ref_zimage_s%d.png" % seed) if var in ("E","G")').replace('"h3image_v8%s_%dref_s%d"', '"h3image_v10%s_%dref_s%d"')
open("minimax_img_v10.py", "w").write(s)
