"""McLaren 765LT static scene: rough urban volumes + fixed 50mm camera, HDRI sun, exports passes for ComfyUI
and 16-bit linear EXR (no view transform) for the VFX pipeline.
usage: blender -b "Test Mclaren.blend" --python build_scene.py -- OUTDIR [--nopasses]
Never saves over the original file: writes OUTDIR/../mclaren_scene.blend"""
import bpy, sys, os, math, mathutils
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
HDRI = os.environ.get("HDRI", r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\hdri\DaySkyHDRI063B_8K_HDR.exr")
SUN_AZ = math.radians(float(os.environ.get("SUN_AZ", "233")))   # where the sun should sit in the world (deg, atan2(y,x)); 233 = behind-left of the camera
HDR_STR = float(os.environ.get("HDR_STR", "1.0"))

# ---------- clean and orient the car ----------
if bpy.data.objects.get("Plane"): bpy.data.objects.remove(bpy.data.objects["Plane"], do_unlink=True)
root = bpy.data.objects["RootNode"]; root.rotation_mode = 'XYZ'; root.rotation_euler = (0, 0, math.radians(90))   # front (-Y in the file) -> +X (the glTF root uses quaternions)
car_objs = [o for o in bpy.data.objects if o.type == 'MESH']
car_names = {o.name for o in car_objs}

# ---------- environment volumes (rough shapes only) ----------
env_objs = []
def box(name, c, s, grp):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.name = name; o.scale = s; o["grp"] = grp
    env_objs.append(o); return o
def cone(name, c, r1, r2, h, grp):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=c); o = bpy.context.object; o.name = name; o["grp"] = grp; env_objs.append(o); return o
box("ground", (0, 0, -0.05), (240, 240, 0.1), "ground")
box("sidewalk", (0, 8.0, 0.07), (120, 5.0, 0.14), "ground2")
# colonnade building behind the car: stepped base, deep piers, heavy overhanging cornice, dark glazing behind
box("wall", (0, 14.0, 7.0), (90, 1.0, 14.0), "building")
for i, x in enumerate((-22, -15, -8, -1, 6)):
    box("pier%d" % i, (x, 9.6, 3.9), (1.9, 2.0, 7.8), "building")
box("cornice", (-8, 10.4, 8.4), (40, 4.8, 1.6), "building")
box("glass_l", (-4, 13.2, 3.2), (36, 0.2, 6.4), "glass")
box("bigpier", (12.0, 9.8, 5.4), (4.2, 3.4, 10.8), "building")
box("upper_l", (-6, 13.0, 13.0), (44, 3.0, 8.0), "building")
box("glass_r", (21.0, 13.2, 3.2), (12, 0.2, 5.4), "glass")
box("bld_r", (26.0, 11.5, 8.0), (8, 4, 16.0), "building")
# tall block off-frame to the camera-left: it only throws a long diagonal shadow across the foreground
box("fg_block", (0.5, -9.5, 5.0), (3.2, 2.2, 10.0), "fg")

# ---------- camera: 50 mm ----------
cam_d = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam_d.lens = 50; cam_d.sensor_width = 36
cam.location = (6.4, -6.6, 1.0)
tgt = Vector((0.2, 0.0, 0.50)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 768, 100
# foreground pedestrian volume inside the right of the frame (the AI will dress and blur it)
_a0 = math.atan2(tgt.y - cam.location.y, tgt.x - cam.location.x) - math.radians(float(os.environ.get("PED_ANG", "15.5")))
_pd = float(os.environ.get("PED_DIST", "3.6")); _pp = (cam.location.x + _pd * math.cos(_a0), cam.location.y + _pd * math.sin(_a0))
cone("fg_person", (_pp[0], _pp[1], 0.78), 0.33, 0.20, 1.56, "fg")
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(_pp[0], _pp[1], 1.72)); _h = bpy.context.object; _h.name = "fg_head"; _h["grp"] = "fg"; env_objs.append(_h)

# ---------- HDRI with a real sun (EEVEE extracts the sun and casts shadows from it) ----------
for o in [o for o in bpy.data.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
img = bpy.data.images.load(HDRI, check_existing=True); img.colorspace_settings.name = 'Linear Rec.709' if 'Linear Rec.709' in [c.identifier for c in img.colorspace_settings.bl_rna.properties['name'].enum_items] else img.colorspace_settings.name
w_, h_ = img.size; tmp = img.copy(); tmp.scale(2048, 1024); px = np.empty(2048 * 1024 * 4, np.float32); tmp.pixels.foreach_get(px); px = px.reshape(1024, 2048, 4)
lum = px[..., :3].mean(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
u = (ix + 0.5) / 2048; v = (iy + 0.5) / 1024                       # image rows start at the bottom in Blender
az_tex = math.atan2(0, 1)  # placeholder, overwritten below
phi = (u - 0.5) * 2 * math.pi; theta = (v - 0.5) * math.pi
d_tex = Vector((math.cos(theta) * -math.cos(phi), math.cos(theta) * math.sin(phi), math.sin(theta)))   # Blender equirect: u = atan2(y,-x)/2pi + .5
az_tex = math.atan2(d_tex.y, d_tex.x); el_deg = math.degrees(theta)
print("HDRI sun: u=%.3f v=%.3f az=%.1f el=%.1f peak=%.1f" % (u, v, math.degrees(az_tex), el_deg, lum.max()))
bpy.data.images.remove(tmp)
W = bpy.data.worlds.get("World") or bpy.data.worlds.new("World"); sc.world = W; W.use_nodes = True
nt = W.node_tree; nt.nodes.clear()
et = nt.nodes.new("ShaderNodeTexEnvironment"); et.image = img; mp = nt.nodes.new("ShaderNodeMapping"); tc = nt.nodes.new("ShaderNodeTexCoord")
bg = nt.nodes.new("ShaderNodeBackground"); wo = nt.nodes.new("ShaderNodeOutputWorld")
mp.inputs["Rotation"].default_value = (0, 0, az_tex - SUN_AZ); bg.inputs[1].default_value = HDR_STR
nt.links.new(tc.outputs["Generated"], mp.inputs[0]); nt.links.new(mp.outputs[0], et.inputs[0]); nt.links.new(et.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], wo.inputs[0])
W.use_sun_shadow = True; W.sun_threshold = 8.0; W.sun_angle = math.radians(1.5); W.sun_shadow_maximum_resolution = 0.001

# ---------- helpers ----------
sc.render.engine = 'BLENDER_EEVEE'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
sc.render.film_transparent = False
def mat_diffuse(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; return m
def mat_emit(name, build):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree; n.nodes.clear()
    out = n.nodes.new("ShaderNodeOutputMaterial"); em = n.nodes.new("ShaderNodeEmission"); build(n, em); n.links.new(em.outputs[0], out.inputs[0]); return m
def flat(name, rgb):
    def b(n, em): em.inputs["Color"].default_value = (*rgb, 1)
    return mat_emit(name, b)
GRP_COL = {"ground": (0.35, 0.35, 0.35), "ground2": (0.55, 0.55, 0.55), "building": (0.78, 0.47, 0.20), "glass": (0.12, 0.24, 0.63), "fg": (1.0, 0.5, 0.0)}
CLAY = {"ground": (0.28, 0.27, 0.26), "ground2": (0.40, 0.38, 0.36), "building": (0.55, 0.52, 0.47), "glass": (0.03, 0.04, 0.05), "fg": (0.08, 0.08, 0.08)}
for o in env_objs: o.data.materials.clear(); o.data.materials.append(mat_diffuse("clay_" + o["grp"], CLAY[o["grp"]]))

def car_group(o):
    n = o.name.lower(); ms = " ".join(s.material.name.lower() for s in o.material_slots if s.material)
    if "paint" in n or "car paint" in ms: return "paint"
    if "window" in ms or "light" in n: return "glass"
    if "callip" in ms: return "caliper"
    if "wheel" in ms or n.startswith("polysurface"): return "wheel"
    return "other"
CAR_COL = {"paint": (1, 0, 0), "glass": (0, 0, 1), "wheel": (0, 1, 0), "caliper": (1, 0, 1), "other": (1, 1, 0)}
store = {o.name: [s.material for s in o.material_slots] for o in bpy.data.objects if o.type == 'MESH'}
def restore():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for s, m in zip(o.material_slots, store[o.name]): s.material = m
def set_all(mat):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for s in o.material_slots: s.material = mat
def render(name, samples=16, filt=1.5, view="Standard", fmt="PNG", ext=".png"):
    sc.eevee.taa_render_samples = samples; sc.render.filter_size = filt; sc.view_settings.view_transform = view
    sc.render.image_settings.file_format = fmt
    sc.render.filepath = os.path.join(OUT, name + ext); bpy.ops.render.render(write_still=True); print("RENDERED", name)

sc.view_settings.look = "None"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT), "mclaren_scene.blend"), copy=True)
if "--nopasses" in argv: sys.exit(0)

# 1) beauty with real car materials (placeholder look) and clay environment
render("beauty_color", 64, 1.5, "AgX")
# 2) clay beauty (all grey) = shapes + shadows for the AI
clay = mat_diffuse("clay_all", (0.5, 0.5, 0.5)); set_all(clay); render("beauty_clay", 64, 1.5, "AgX"); restore()
# 3) depth: near=4m -> white, far=30m -> black (camera distance)
def build_depth(n, em):
    ci = n.nodes.new("ShaderNodeCameraData"); mr = n.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 4.0; mr.inputs["From Max"].default_value = 30.0; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; mr.clamp = True
    n.links.new(ci.outputs["View Z Depth"], mr.inputs["Value"]); c = n.nodes.new("ShaderNodeCombineColor")
    for k in range(3): n.links.new(mr.outputs[0], c.inputs[k])
    n.links.new(c.outputs[0], em.inputs["Color"])
W.use_nodes = True; bg.inputs[1].default_value = 0.0      # black world for the data passes
set_all(mat_emit("depth", build_depth)); render("depth", 1, 0.0); restore()
# 4) normals in camera space
def build_nrm(n, em):
    g = n.nodes.new("ShaderNodeNewGeometry"); vt = n.nodes.new("ShaderNodeVectorTransform"); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    ma = n.nodes.new("ShaderNodeVectorMath"); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = (0.5, 0.5, 0.5); ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    n.links.new(g.outputs["Normal"], vt.inputs[0]); n.links.new(vt.outputs[0], ma.inputs[0]); n.links.new(ma.outputs[0], em.inputs["Color"])
set_all(mat_emit("nrm", build_nrm)); render("normal", 1, 0.0); restore()
# 5) flat ID colours (sky = pale blue)
bg.inputs[0].default_value = (0.53, 0.81, 0.92, 1); bg.inputs[1].default_value = 1.0
for l in list(nt.links):
    if l.to_node == bg and l.to_socket == bg.inputs[0]: nt.links.remove(l)
cm = {k: flat("id_" + k, v) for k, v in CAR_COL.items()}; em_ = {k: flat("idenv_" + k, v) for k, v in GRP_COL.items()}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = cm[car_group(o)] if o.name in car_names else em_[o["grp"]]
    for s in o.material_slots: s.material = m
render("id", 1, 0.0); restore()
# back to the HDRI world
nt.links.new(et.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = HDR_STR
# 6) car only, real materials, transparent, environment as holdout (occluders still cut it)
for o in env_objs: o.is_holdout = True
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
render("car_rgba", 64, 1.5, "AgX")
# 7) VFX exports: 16-bit half float, scene-linear, NO view transform (multilayer EXR: combined, Z, normal, cryptomatte)
vl = bpy.context.view_layer; vl.use_pass_combined = True; vl.use_pass_z = True; vl.use_pass_normal = True
for a in ("use_pass_cryptomatte_object", "use_pass_cryptomatte_material", "use_pass_cryptomatte_asset"):
    if hasattr(vl, a): setattr(vl, a, True)
sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'ZIP'; sc.render.image_settings.color_mode = 'RGBA'
render("car_rgba_linear", 64, 1.5, "Raw", "OPEN_EXR_MULTILAYER", ".exr")            # car with alpha, transparent background
for o in env_objs: o.is_holdout = False
sc.render.film_transparent = False
render("beauty_linear", 64, 1.5, "Raw", "OPEN_EXR_MULTILAYER", ".exr")                # whole scene
print("ALLDONE")
