"""Layout v2: only car + road are defined; everything off-road and the sky is one flat neutral grey so the model invents the environment."""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None, cast=str):
    return cast(argv[argv.index(name) + 1]) if name in argv else default


import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wheel_spin
spin = arg("--spin", None, float)
out = arg("--out", r"C:\Users\Internet\Desktop\TEST COMFYUI\render\layout" + "\\")
still = arg("--still", None, int)
end = arg("--end", None, int)

scene = bpy.context.scene
# DEDUP: remove objects already baked into the blend so they are not built twice
for _n in ("CIRCUIT_ENV", "VISOR"):
    _o = bpy.data.objects.get(_n)
    if _o: bpy.data.objects.remove(_o, do_unlink=True)
exec(open("C:/Users/Internet/Desktop/TEST COMFYUI/scripts/antenna_cut.py").read())
if end: scene.frame_end = end
if arg('--start', None, int): scene.frame_start = arg('--start', 1, int)
if spin: wheel_spin.apply(scene, spin)
scene.render.use_compositing = False
scene.render.use_sequencer = False
scene.render.film_transparent = False
st = scene.render.image_settings
if hasattr(st, "media_type"):
    st.media_type = "IMAGE"
st.file_format = "PNG"; st.color_mode = "RGB"; st.color_depth = "8"
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
for vl in scene.view_layers:
    for k in dir(vl):
        if k.startswith("use_pass_") and k != "use_pass_combined":
            try: setattr(vl, k, False)
            except Exception: pass


def mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    pb = m.node_tree.nodes.get("Principled BSDF")
    pb.inputs["Base Color"].default_value = (*color, 1)
    pb.inputs["Roughness"].default_value = rough
    for nm in ("Specular IOR Level", "Specular"):
        if nm in pb.inputs:
            pb.inputs[nm].default_value = 0.1
    return m


clay = mat("CLAY", (0.30, 0.30, 0.30))
road = mat("ROAD", (0.18, 0.18, 0.18), 0.9)
_g = arg("--ground", 0.17, float)
grass = mat("GRASS", (_g, _g, _g), 1.0)

for o in scene.objects:
    if o.type != "MESH":
        continue
    m = clay
    if o.name == "NurbsPath.001":
        m = road
    elif o.name == "Plane":
        m = grass
    o.data.materials.clear()
    o.data.materials.append(m)

# pale flat sky so the horizon is crisp
world = bpy.data.worlds.new("SEM_WORLD"); world.use_nodes = True
wt = world.node_tree; wt.nodes.clear()
bg = wt.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (0.55, 0.55, 0.55, 1); bg.inputs["Strength"].default_value = 1.0
wo = wt.nodes.new("ShaderNodeOutputWorld"); wt.links.new(bg.outputs[0], wo.inputs["Surface"])
scene.world = world

if "--nocity" in argv:
    _o = bpy.data.objects.get("PROXY_CITY")
    if _o: bpy.data.objects.remove(_o, do_unlink=True)
if "--circuit" in argv:
    import circuit_env; circuit_env.build(scene)
    _h = bpy.data.objects.get("Sphere")
    if _h:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12)
        v = bpy.context.active_object; v.name = "VISOR"; v.parent = bpy.data.objects["f1_2026_sf26"]
        v.location = (-0.009, 0.846 + 0.012, -0.033 - 0.13); v.scale = (0.100, 0.040, 0.050)
        v.data.materials.append(mat("VISOR", (0.02, 0.02, 0.02), 0.2))
if "--track" in argv:
    import proxy_city; proxy_city.build_track(scene)
    _h = bpy.data.objects.get("Sphere")
    if _h:   # helmet visor: dark flattened ellipsoid on the front (car forward = local -Z)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12)
        v = bpy.context.active_object; v.name = "VISOR"; v.parent = bpy.data.objects["f1_2026_sf26"]
        v.location = (-0.009, 0.846 + 0.012, -0.033 - 0.13); v.scale = (0.100, 0.040, 0.050)
        v.data.materials.append(mat("VISOR", (0.02, 0.02, 0.02), 0.2))
if "--city" in argv:
    import proxy_city; proxy_city.build(scene)
if arg("--pct", None, int): scene.render.resolution_percentage = arg("--pct", 100, int)
if arg("--shifty", None, float) is not None:
    scene.camera.data.shift_y = arg("--shifty", 0.0, float)
if arg("--pitch", None, float) is not None:
    import math as _m; scene.camera.delta_rotation_euler.x = _m.radians(arg("--pitch", 0.0, float))
if "--mblur" in argv:   # real camera motion blur (camera is parented to the car -> car sharp, environment streaks with parallax)
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = arg("--shutter", 0.5, float)
    print("MOTION BLUR ON shutter", scene.render.motion_blur_shutter)
print("SEMANTIC ->", out)
if still:
    scene.frame_set(still)
    scene.render.filepath = out + "sem_still_%04d.png" % still
    bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = out + "sem_"
    bpy.ops.render.render(animation=True)
print("DONE")
