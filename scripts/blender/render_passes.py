"""Works on the USER's scene (mclaren_scene.blend, keeps all their edits), fixes the lighting, tunes EEVEE for realism and
renders the passes for ComfyUI. Saves the result as mclaren_scene_v2.blend (never overwrites the user's file).
usage: blender -b mclaren_scene.blend --python render_passes.py -- OUTDIR
env: RES_SCALE (default 2 -> 2560x1536, then ComfyUI inputs are downscaled to 1280x768), SAMPLES (default 256), SUN_AZ (deg), HDR_STR"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "."
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
RES = int(os.environ.get("RES_SCALE", "2")); SAMPLES = int(os.environ.get("SAMPLES", "256"))
SUN_AZ = math.radians(float(os.environ.get("SUN_AZ", "233"))); HDR_STR = float(os.environ.get("HDR_STR", "1.0")); CLAMP = 20.0
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1280, 768; sc.render.resolution_percentage = 100 * RES

# ---------- world: HDRI with the sun taken out + a real sun lamp that has exactly the sun's energy ----------
W = sc.world; nt = W.node_tree
et = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexEnvironment"); bg = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBackground")
mp = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMapping")
BAKED = os.environ.get("BAKED", "0") == "1"      # BAKED=1: render a scene that already contains the mannequin, the building fix and the sun (mclaren_scene_v2.blend edited by hand): change nothing
if not BAKED:
    img = et.image; tmp = img.copy(); tmp.scale(2048, 1024); px = np.empty(2048 * 1024 * 4, np.float32); tmp.pixels.foreach_get(px); px = px.reshape(1024, 2048, 4)[..., :3]; bpy.data.images.remove(tmp)
    lum = px.mean(-1); iy, ix = np.unravel_index(np.argmax(lum), lum.shape)
    v_ = (np.arange(1024) + 0.5) / 1024; lat = (v_ - 0.5) * math.pi; dom = (2 * math.pi / 2048) * (math.pi / 1024) * np.cos(lat)[:, None]
    excess = np.clip(px - CLAMP, 0, None); E = (excess * dom[..., None]).sum((0, 1))            # irradiance of the removed sun (RGB)
    lat_s = lat[iy]; phi = ((ix + 0.5) / 2048 - 0.5) * 2 * math.pi
    d_tex = Vector((math.cos(lat_s) * -math.cos(phi), math.cos(lat_s) * math.sin(phi), math.sin(lat_s))); az_tex = math.atan2(d_tex.y, d_tex.x)
    mp.inputs["Rotation"].default_value = (0, 0, az_tex - SUN_AZ)
    az_w = SUN_AZ; el = lat_s
    sun_dir = Vector((math.cos(el) * math.cos(az_w), math.cos(el) * math.sin(az_w), math.sin(el)))   # where the sun is
    print("SUN el=%.1f az=%.1f E=%s" % (math.degrees(el), math.degrees(az_w), tuple(round(float(x), 2) for x in E)))
    # env -> min(clamp) -> background
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'MINIMUM'; vm.inputs[1].default_value = (CLAMP, CLAMP, CLAMP)
    for l in list(nt.links):
        if l.to_node == bg and l.to_socket == bg.inputs[0]: nt.links.remove(l)
    nt.links.new(et.outputs[0], vm.inputs[0]); nt.links.new(vm.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = HDR_STR
    W.use_sun_shadow = False
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT']: bpy.data.objects.remove(o, do_unlink=True)
    ld = bpy.data.lights.new("sun_hdri", 'SUN'); Em = float(E.mean()) * HDR_STR; ld.energy = Em
    col = (E / max(E.max(), 1e-6)); ld.color = tuple(float(x) for x in col); ld.angle = math.radians(0.55)
    sun = bpy.data.objects.new("sun_hdri", ld); sc.collection.objects.link(sun); sun.rotation_euler = (-sun_dir).to_track_quat('-Z', 'Y').to_euler()
    ld.use_shadow = True
else:
    vm = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeVectorMath"); sun = bpy.data.objects["sun_hdri"]; bg.inputs[1].default_value = HDR_STR

# ---------- EEVEE: realism ----------
e = sc.eevee
def sset(o, a, v):
    try: setattr(o, a, v)
    except Exception as ex: print("skip", a, ex)
sset(e, "use_raytracing", True); sset(e, "ray_tracing_method", 'SCREEN'); ro = e.ray_tracing_options
sset(ro, "resolution_scale", '1'); sset(ro, "use_denoise", True); sset(ro, "denoise_spatial", True); sset(ro, "denoise_temporal", True); sset(ro, "denoise_bilateral", True); sset(ro, "trace_max_roughness", 0.9); sset(ro, "screen_trace_quality", 1.0)
sset(e, "use_fast_gi", True); sset(e, "fast_gi_method", 'GLOBAL_ILLUMINATION'); sset(e, "fast_gi_ray_count", 4); sset(e, "fast_gi_step_count", 16); sset(e, "fast_gi_quality", 1.0); sset(e, "fast_gi_resolution", '1'); sset(e, "gi_diffuse_bounces", 3)
sset(e, "use_shadows", True); sset(e, "shadow_ray_count", 4); sset(e, "shadow_step_count", 16); sset(e, "shadow_resolution_scale", 1.0); sset(e, "light_threshold", 0.001)
sset(e, "use_taa_reprojection", True); sset(e, "taa_render_samples", SAMPLES); sset(e, "gi_glossy_clamp", 0.0); sset(e, "clamp_surface_indirect", 0.0)
sc.render.filter_size = 1.0; sc.render.use_motion_blur = False
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "None"; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '16'

# ---------- human proxy: replaces the cone pedestrian (walking pose, profile view, coat to mid-calf) ----------
def make_mannequin():
    old = bpy.data.objects.get("fg_person")
    if old is None: return
    base = old.matrix_world.translation.copy(); base.z = 0.0
    cpos = sc.camera.matrix_world.translation.copy(); cpos.z = 0.0; dv = base - cpos; base = cpos + dv.normalized() * float(os.environ.get("HUMAN_DIST", "4.3"))   # same screen position, a little farther so the whole figure fits
    sw = bpy.data.objects.get("sidewalk.001")                         # the user's sidewalk strip in front of the car: keep her on it and put her feet on its top
    if sw:
        y0 = sw.location.y - sw.scale.y / 2 + 0.35; y1 = sw.location.y + sw.scale.y / 2 - 0.35; base.y = min(max(base.y, y0), y1); base.z = sw.location.z + sw.scale.z / 2
    walk = Vector((float(os.environ.get("WALK_X", "1")), 0.0, 0.0))     # she walks along the sidewalk: +1 = towards +X (right of the frame, towards the camera), -1 = towards -X (left, away)
    ang = math.atan2(walk.y, walk.x); H = float(os.environ.get("HUMAN_H", "1.62")); k = H / 1.70
    mat = old.material_slots[0].material if old.material_slots else None
    parts = []
    def prim(op, loc, rot=(0, 0, 0), scale=(1, 1, 1), **kw):
        getattr(bpy.ops.mesh, op)(location=(0, 0, 0), **kw); o = bpy.context.object; o.scale = scale; o.rotation_euler = rot; o.location = loc; parts.append(o); return o
    def limb(p1, p2, r1, r2=None):
        a = Vector(p1) * k; b = Vector(p2) * k; d = b - a; L = d.length; mid = (a + b) / 2
        q = d.to_track_quat('Z', 'Y'); o = prim("primitive_cone_add", mid, q.to_euler(), radius1=r1 * k, radius2=(r2 if r2 is not None else r1) * k, depth=L, vertices=16); return o
    prim("primitive_cube_add", (0, 0, 0), scale=(0.001, 0.001, 0.001), size=1.0)                  # neutral part: the joined object keeps origin (0,0,0) and no rotation
    limb((0, 0.09, 0.92), (0.20, 0.09, 0.09), 0.085, 0.055)           # leading leg
    limb((0, -0.09, 0.92), (-0.24, -0.09, 0.09), 0.085, 0.055)        # trailing leg
    prim("primitive_cone_add", (0.285 * k, 0.09 * k, 0.07 * k), rot=(0, math.radians(90), 0), radius1=0.042 * k, radius2=0.014 * k, depth=0.27 * k, vertices=16)
    prim("primitive_cylinder_add", (0.17 * k, 0.09 * k, 0.03 * k), radius=0.018 * k, depth=0.06 * k, vertices=12)          # slim heel   # shoe: wide heel behind, narrow toe in front (+x = walking direction)
    prim("primitive_cone_add", (-0.175 * k, -0.09 * k, 0.07 * k), rot=(0, math.radians(90), 0), radius1=0.042 * k, radius2=0.014 * k, depth=0.27 * k, vertices=16)
    prim("primitive_cylinder_add", (-0.29 * k, -0.09 * k, 0.03 * k), radius=0.018 * k, depth=0.06 * k, vertices=12)
    prim("primitive_cone_add", (0, 0, 0.93 * k), radius1=0.25 * k, radius2=0.16 * k, depth=0.96 * k, vertices=24)   # long coat
    prim("primitive_uv_sphere_add", (0, 0, 1.40 * k), scale=(0.10 * k, 0.19 * k, 0.085 * k), radius=1.0)             # shoulders
    prim("primitive_uv_sphere_add", (0.09 * k, 0, 1.22 * k), scale=(0.10 * k, 0.15 * k, 0.16 * k), radius=1.0)             # chest bulge: the front of the torso
    prim("primitive_cube_add", (0.14 * k, 0, 1.02 * k), scale=(0.02 * k, 0.03 * k, 0.55 * k), size=1.0)                       # coat front opening line
    limb((0, 0.22, 1.38), (-0.14, 0.27, 0.86), 0.05, 0.04)             # arm swinging back
    limb((0, -0.22, 1.38), (0.16, -0.26, 0.88), 0.05, 0.04)            # arm swinging forward
    prim("primitive_cylinder_add", (0, 0, 1.50 * k), radius=0.05 * k, depth=0.12 * k)                               # neck
    prim("primitive_uv_sphere_add", (0.01 * k, 0, 1.62 * k), scale=(0.085 * k, 0.078 * k, 0.10 * k), radius=1.0)    # head
    prim("primitive_uv_sphere_add", (-0.04 * k, 0, 1.63 * k), scale=(0.105 * k, 0.095 * k, 0.105 * k), radius=1.0)
    prim("primitive_cone_add", (0.105 * k, 0, 1.605 * k), rot=(0, math.radians(90), 0), radius1=0.022 * k, radius2=0.004 * k, depth=0.05 * k, vertices=12)   # nose: points where she looks
    prim("primitive_uv_sphere_add", (0.075 * k, 0, 1.555 * k), scale=(0.03 * k, 0.04 * k, 0.025 * k), radius=1.0)                                                 # chin
    prim("primitive_uv_sphere_add", (-0.14 * k, 0.27 * k, 0.84 * k), scale=(0.045 * k, 0.035 * k, 0.06 * k), radius=1.0)
    prim("primitive_uv_sphere_add", (0.16 * k, -0.26 * k, 0.86 * k), scale=(0.045 * k, 0.035 * k, 0.06 * k), radius=1.0)    # hair
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); m = bpy.context.object; m.name = "fg_person_human"; m["grp"] = "fg"
    m.rotation_euler = (0, 0, ang); m.location = base
    bpy.ops.object.shade_smooth()
    m.data.materials.clear()
    def tone(nm, v):
        t = bpy.data.materials.new(nm); t.use_nodes = True; b = t.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (v, v, v, 1); b.inputs["Roughness"].default_value = 0.9; b.inputs["Emission Color"].default_value = (v, v, v, 1); b.inputs["Emission Strength"].default_value = 0.9; return t
    if os.environ.get("HUMAN_TONES", "1") == "1":
        for nm, v in (("skin", 0.62), ("hair", 0.10), ("coat", 0.20), ("trousers", 0.07)): m.data.materials.append(tone("man_" + nm, v))
        for poly in m.data.polygons:
            c = poly.center * m.scale.z; zz = c.z / k          # the joined object keeps the 0.001 scale of the neutral part: convert local mm to metres
            poly.material_index = (1 if (zz > 1.50 and c.x / k < -0.03) else 0 if (zz > 1.50 or (zz < 1.0 and abs(c.y) > 0.2 and zz > 0.80 and False)) else 3 if zz < 0.50 else 2)
        import collections; print("MAN idx counts", dict(collections.Counter(pp.material_index for pp in m.data.polygons)), "scale", m.scale.z)
        hands = [pp for pp in m.data.polygons if 0.75 < pp.center.z * m.scale.z / k < 0.95 and abs(pp.center.y * m.scale.z / k) > 0.23]
        for pp in hands: pp.material_index = 0
    elif mat: m.data.materials.append(mat)
    for o in [old] + list(old.children): o.hide_render = True; o.hide_viewport = True
    print("MANNEQUIN at", tuple(round(x, 2) for x in base), "walk az", round(math.degrees(ang), 1))
if os.environ.get("HUMAN", "1") == "1": make_mannequin()

# ---------- building: exactly 3 columns, closed colonnade (floor, plinths, end wall, continuous entablature) ----------
def fix_building():
    wall = bpy.data.objects.get("wall"); mat = wall.material_slots[0].material if wall and wall.material_slots else None
    gmat = bpy.data.objects["sidewalk"].material_slots[0].material if bpy.data.objects.get("sidewalk") else None
    def nbox(name, c, sz, grp, m):
        bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.name = name; o.scale = sz; o["grp"] = grp
        o.data.materials.clear()
        if m: o.data.materials.append(m)
        return o
    for nme in ("pier0", "pier4", "bigpier", "bld_r", "glass_r"):
        o = bpy.data.objects.get(nme)
        if o: o.hide_render = True; o.hide_viewport = True
    nbox("arcade_floor", (-9.0, 12.05, 0.07), (44.0, 3.2, 0.14), "ground2", gmat)                  # floor under the colonnade, same level as the sidewalk
    for i, x in enumerate((-15, -8, -1)): nbox("plinth%d" % i, (x, 9.6, 0.34), (2.6, 2.7, 0.4), "building", mat)   # columns stand on a base
    c = bpy.data.objects.get("cornice")
    if c: c.location.x = -8.75; c.scale.x = 23.1; c.location.y = 10.4
    print("BUILDING fixed: 3 columns")
if os.environ.get("BUILDING", "1") == "1": fix_building()

# ---------- richer clay: block joints on the stone, paving slabs on the ground (bump only, grey) ----------
def clay_tex(name, rgb, freq, mortar, depth, vertical=False):
    t = bpy.data.materials.new(name); t.use_nodes = True; nt_ = t.node_tree; b = nt_.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.9
    g_ = nt_.nodes.new("ShaderNodeNewGeometry"); br_ = nt_.nodes.new("ShaderNodeTexBrick"); br_.inputs["Scale"].default_value = freq; br_.inputs["Mortar Size"].default_value = mortar
    br_.inputs["Color1"].default_value = (0.9, 0.9, 0.9, 1); br_.inputs["Color2"].default_value = (0.8, 0.8, 0.8, 1); br_.inputs["Mortar"].default_value = (0.2, 0.2, 0.2, 1); br_.inputs["Bias"].default_value = 0.0
    bm_ = nt_.nodes.new("ShaderNodeBump"); bm_.inputs["Distance"].default_value = depth; bm_.inputs["Strength"].default_value = 1.0
    mix_ = nt_.nodes.new("ShaderNodeMix"); mix_.data_type = 'RGBA'; mix_.inputs[0].default_value = 0.35
    if vertical:
        sp_ = nt_.nodes.new("ShaderNodeSeparateXYZ"); cm_ = nt_.nodes.new("ShaderNodeCombineXYZ"); ad_ = nt_.nodes.new("ShaderNodeMath"); ad_.operation = 'ADD'
        nt_.links.new(g_.outputs["Position"], sp_.inputs[0]); nt_.links.new(sp_.outputs["X"], ad_.inputs[0]); nt_.links.new(sp_.outputs["Y"], ad_.inputs[1])
        nt_.links.new(ad_.outputs[0], cm_.inputs["X"]); nt_.links.new(sp_.outputs["Z"], cm_.inputs["Y"]); nt_.links.new(cm_.outputs[0], br_.inputs["Vector"])
    else:
        nt_.links.new(g_.outputs["Position"], br_.inputs["Vector"])
    nt_.links.new(br_.outputs["Fac"], bm_.inputs["Height"]); nt_.links.new(bm_.outputs["Normal"], b.inputs["Normal"])
    mix_.inputs[6].default_value = (*rgb, 1); nt_.links.new(br_.outputs["Color"], mix_.inputs[7]); nt_.links.new(mix_.outputs[2], b.inputs["Base Color"])
    return t
if os.environ.get("CLAYTEX", "1") == "1":
    tex = {"building": clay_tex("clay_stone", (0.55, 0.52, 0.47), 0.42, 0.012, 0.06, True), "ground2": clay_tex("clay_pavers", (0.40, 0.38, 0.36), 0.5, 0.012, 0.03), "ground": clay_tex("clay_slabs", (0.28, 0.27, 0.26), 0.35, 0.010, 0.03)}
    for o in bpy.data.objects:
        if o.type == 'MESH' and "grp" in o.keys() and o["grp"] in tex and o.name != "fg_person_human":
            o.data.materials.clear(); o.data.materials.append(tex[o["grp"]])

# ---------- road vs sidewalk: clear tonal separation in the clay (dark asphalt road, light sidewalks) ----------
def set_tone(grp, v):
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.get("grp") == grp:
            for sl in o.material_slots:
                m = sl.material
                if m and m.use_nodes and "Principled BSDF" in m.node_tree.nodes and not m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].is_linked:
                    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (v, v, v, 1)
set_tone("ground", float(os.environ.get("ROAD_TONE", "0.10"))); set_tone("ground2", float(os.environ.get("SIDEWALK_TONE", "0.55")))

# ---------- groups ----------
env_objs = [o for o in bpy.data.objects if o.type == 'MESH' and "grp" in o.keys()]; car_names = {o.name for o in bpy.data.objects if o.type == 'MESH' and "grp" not in o.keys()}
def mat_emit(name, build):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree; n.nodes.clear()
    out = n.nodes.new("ShaderNodeOutputMaterial"); em = n.nodes.new("ShaderNodeEmission"); build(n, em); n.links.new(em.outputs[0], out.inputs[0]); return m
def flat(name, rgb):
    def b(n, em): em.inputs["Color"].default_value = (*rgb, 1)
    return mat_emit(name, b)
def mat_clay(name, rgb=(0.5, 0.5, 0.5)):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.9; return m
def car_group(o):
    n = o.name.lower(); ms = " ".join(s.material.name.lower() for s in o.material_slots if s.material)
    if "paint" in n or "car paint" in ms: return "paint"
    if "light" in n: return "lamp"
    if "window" in ms: return "glass"
    if "callip" in ms: return "caliper"
    if "wheel" in ms or n.startswith("polysurface"): return "wheel"
    return "other"
CAR_COL = {"paint": (1, 0, 0), "lamp": (0, 1, 1), "glass": (0, 0, 1), "wheel": (0, 1, 0), "caliper": (1, 0, 1), "other": (1, 1, 0)}
GRP_COL = {"ground": (0.35, 0.35, 0.35), "ground2": (0.55, 0.55, 0.55), "building": (0.78, 0.47, 0.20), "glass": (0.12, 0.24, 0.63), "fg": (1.0, 0.5, 0.0)}
store = {o.name: [s.material for s in o.material_slots] for o in bpy.data.objects if o.type == 'MESH'}
def restore():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for s, m in zip(o.material_slots, store[o.name]): s.material = m
def set_all(mat):
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for s in o.material_slots: s.material = mat
cam = sc.camera; dof0 = cam.data.dof.use_dof
def render(name, samples, filt=1.0, view="AgX", dof=False):
    cam.data.dof.use_dof = dof; sc.eevee.taa_render_samples = samples; sc.render.filter_size = filt; sc.view_settings.view_transform = view
    sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True); print("RENDERED", name)
if not BAKED: bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT), "mclaren_scene_v2.blend"), copy=True)   # never overwrite the hand-edited v2
if "--nopasses" in argv: sys.exit(0)

# 1) beauty with real materials (keeps the user's depth of field)
render("beauty_color", SAMPLES, 1.0, "AgX", dof0)
# 2) clay (shapes + shadows), sharp
clay_car = mat_clay("clay_all")
for o_ in bpy.data.objects:
    if o_.type == "MESH" and o_.name in car_names:
        for sl_ in o_.material_slots: sl_.material = clay_car
lamp_m = mat_emit("clay_lamp", lambda n, em: (em.inputs["Color"].__setattr__("default_value", (0.92, 0.95, 1.0, 1)), em.inputs["Strength"].__setattr__("default_value", 0.9)))
for o in bpy.data.objects:
    if o.type == "MESH" and o.name in car_names and car_group(o) == "lamp":
        for sl in o.material_slots: sl.material = lamp_m
render("beauty_clay", SAMPLES); restore()
# 3) depth 4..30 m (near = white), no DOF
def build_depth(n, em):
    ci = n.nodes.new("ShaderNodeCameraData"); mr = n.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 4.0; mr.inputs["From Max"].default_value = 30.0; mr.inputs["To Min"].default_value = 1.0; mr.inputs["To Max"].default_value = 0.0; mr.clamp = True
    n.links.new(ci.outputs["View Z Depth"], mr.inputs["Value"]); c = n.nodes.new("ShaderNodeCombineColor")
    for k in range(3): n.links.new(mr.outputs[0], c.inputs[k])
    n.links.new(c.outputs[0], em.inputs["Color"])
bg.inputs[1].default_value = 0.0; sun.hide_render = True
set_all(mat_emit("depth", build_depth)); render("depth", 1, 0.0, "Standard"); restore()
# 4) camera-space normals
def build_nrm(n, em):
    g = n.nodes.new("ShaderNodeNewGeometry"); vt = n.nodes.new("ShaderNodeVectorTransform"); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    ma = n.nodes.new("ShaderNodeVectorMath"); ma.operation = 'MULTIPLY_ADD'; ma.inputs[1].default_value = (0.5, 0.5, 0.5); ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    n.links.new(g.outputs["Normal"], vt.inputs[0]); n.links.new(vt.outputs[0], ma.inputs[0]); n.links.new(ma.outputs[0], em.inputs["Color"])
set_all(mat_emit("nrm", build_nrm)); render("normal", 1, 0.0, "Standard"); restore()
# 5) flat ID colours (sky pale blue)
bg.inputs[0].default_value = (0.53, 0.81, 0.92, 1); bg.inputs[1].default_value = 1.0
for l in list(nt.links):
    if l.to_node == bg and l.to_socket == bg.inputs[0]: nt.links.remove(l)
cm = {k: flat("id_" + k, v) for k, v in CAR_COL.items()}; em_ = {k: flat("idenv_" + k, v) for k, v in GRP_COL.items()}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    m = cm[car_group(o)] if o.name in car_names else em_[o["grp"]]
    for s in o.material_slots: s.material = m
render("id", 1, 0.0, "Standard"); restore()
nt.links.new(vm.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = HDR_STR; sun.hide_render = False
# 6) car only, real materials, RGBA, environment as holdout (occluders still cut it), sharp
for o in env_objs: o.is_holdout = True
sc.render.film_transparent = True; sc.render.image_settings.color_mode = 'RGBA'
render("car_rgba", SAMPLES)
print("ALLDONE")
