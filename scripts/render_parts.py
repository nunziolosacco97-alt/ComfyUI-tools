"""Part-ID pass of the car, same camera as the layout: flat emission colours
  red   (1,0,0) = painted bodywork (nose, sidepods, engine cover, airbox)
  blue  (0,0,1) = front wing + rear wing (all faces)
  green (0,1,0) = halo / carbon bits around the cockpit
  black         = everything else (wheels, floor, suspension, helmet, ...)
usage: blender -b file.blend --python render_parts.py -- --out DIR\\ --start 35 --end 43 --pitch 8 --shifty -0.09"""
import sys, math, os
import bpy
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d=None, c=str): return c(argv[argv.index(n) + 1]) if n in argv else d
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
scene = bpy.context.scene
if arg("--end", None, int): scene.frame_end = arg("--end", None, int)
if arg("--start", None, int): scene.frame_start = arg("--start", None, int)
scene.render.use_compositing = False; scene.render.use_sequencer = False; scene.render.film_transparent = False
st = scene.render.image_settings
if hasattr(st, "media_type"): st.media_type = "IMAGE"
st.file_format = "PNG"; st.color_mode = "RGB"; st.color_depth = "8"
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
if hasattr(scene, "cycles"):
    try: scene.cycles.samples = 16; scene.cycles.use_denoising = False
    except Exception: pass
for vl in scene.view_layers:
    for k in dir(vl):
        if k.startswith("use_pass_") and k != "use_pass_combined":
            try: setattr(vl, k, False)
            except Exception: pass


def emit(name, col):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs["Surface"]); return m
MBLK, MRED, MBLU, MGRN = emit("P_BLACK", (0, 0, 0)), emit("P_RED", (1, 0, 0)), emit("P_WING", (0, 0, 1)), emit("P_HALO", (0, 1, 0))

for o in list(scene.objects):
    if o.name in ("NurbsPath.001", "Plane", "PROXY_CITY") or o.name.startswith("VISOR"): o.hide_render = True
car = bpy.data.objects["f1_2026_sf26"]; me = car.data
names = [m.name if m else "" for m in me.materials]
idx = []
for p in me.polygons:
    c = p.center; n = names[p.material_index] if p.material_index < len(names) else ""
    if c.z < -1.85: k = 2                                              # rear wing (car rear = local -Z)
    elif c.z > 0.9 and c.y < 0.45 and abs(c.x) > 0.25: k = 2   # front wing + forward lower bargeboards
    elif c.z > 1.75: k = 2 if ((c.y < 0.34 and abs(c.x) > 0.20) or abs(c.x) > 0.45) else 1       # front wing + endplates / nose cone (red)
    elif n == "sf25_paints": k = 1
    elif -0.30 < c.z < 0.65 and c.y > 0.78 and n.startswith(("sf25_carbon", "sf25_generics", "sf25_details", "sf25_decals")): k = 3
    else: k = 0
    idx.append(k)
me.materials.clear()
for m in (MBLK, MRED, MBLU, MGRN): me.materials.append(m)
for p, k in zip(me.polygons, idx): p.material_index = k
for o in scene.objects:
    if o.type == "MESH" and o is not car and not o.hide_render:
        o.data.materials.clear(); o.data.materials.append(MBLK)
w = bpy.data.worlds.new("PW"); w.use_nodes = True; wt = w.node_tree; wt.nodes.clear()
bg = wt.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (0, 0, 0, 1); bg.inputs["Strength"].default_value = 0.0
wo = wt.nodes.new("ShaderNodeOutputWorld"); wt.links.new(bg.outputs[0], wo.inputs["Surface"]); scene.world = w
if arg("--shifty", None, float) is not None: scene.camera.data.shift_y = arg("--shifty", 0.0, float)
if arg("--pitch", None, float) is not None: scene.camera.delta_rotation_euler.x = math.radians(arg("--pitch", 0.0, float))
scene.render.filepath = arg("--out") + "parts_"
bpy.ops.render.render(animation=True)
print("DONE")
