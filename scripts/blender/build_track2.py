"""One race-track scene (gentle left bend, car at origin heading +X), three camera setups after the references:
  A low  : low 3/4 front next to the kerb, dutch roll, kerb blurred in the foreground (ref BMW M3 Touring)
  B high : high, close, head-on 3/4 front looking down, wide lens, bend + inside kerb behind (ref BMW M4 DTM)
  C side : long-lens side profile, strong horizontal panning (ref Porsche 911 RSR)
usage: blender -b ../mclaren_scene_v2.blend --python build_track2.py -- OUT.blend A|B|C"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Euler
argv = sys.argv[sys.argv.index("--") + 1:]
OUT, VIEW = argv[0], argv[1]
sc = bpy.context.scene; rng = np.random.default_rng(5)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and "grp" in o.keys()]: bpy.data.objects.remove(o, do_unlink=True)
R = 900.0                                     # left bend radius (m); car sits at s=0, heading +X
def mat(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    if isinstance(rgb, float): rgb = (rgb, rgb, rgb)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    m["clay"] = float(0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) ** 0.55 * 0.9 if max(rgb) - min(rgb) > 0.02 else float(rgb[0]); return m
M = {k: mat("col_" + k, v) for k, v in dict(asphalt=(0.10, 0.10, 0.11), kerb_a=(0.55, 0.04, 0.04), kerb_b=0.72, line=0.82, grass=(0.12, 0.21, 0.06), barrier=0.50, tree=(0.05, 0.11, 0.04), hill=(0.22, 0.30, 0.20)).items()}
M["asphalt"]["clay"] = 0.32; M["kerb_a"]["clay"] = 0.22; M["kerb_b"]["clay"] = 0.62; M["line"]["clay"] = 0.75; M["grass"]["clay"] = 0.30; M["tree"]["clay"] = 0.16; M["hill"]["clay"] = 0.36
def mesh_obj(name, verts, faces, m, grp, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m); o["grp"] = grp
    for p in me.polygons: p.use_smooth = smooth
    return o
def P(s, off, z=0.0):                         # point at arclength s, lateral offset off (+ = left/inside of the bend)
    th = s / R; cx = R * math.sin(th); cy = R * (1 - math.cos(th)); nx, ny = -math.sin(th), math.cos(th)
    return (cx + off * nx, cy + off * ny, z)
def ribbon(name, s0, s1, o0, o1, z, m, grp, n=160, dz=0.0, smooth=False):
    ss = np.linspace(s0, s1, n); v = []; f = []
    for i, s in enumerate(ss): v += [P(s, o0, z), P(s, o1, z + dz)]
    for i in range(n - 1): a = 2 * i; f.append((a, a + 1, a + 3, a + 2))
    return mesh_obj(name, v, f, m, grp, smooth)
S0, S1 = -260.0, 330.0
ribbon("asphalt", S0, S1, -3.6, 7.4, 0.0, M["asphalt"], "ground")
ribbon("edge_line", S0, S1, -3.75, -3.55, 0.004, M["line"], "ground2")
ribbon("edge_line_in", S0, S1, 7.2, 7.4, 0.004, M["line"], "ground2")
M["tyre"] = mat("col_tyre", (0.025, 0.025, 0.03)); M["tyre"]["clay"] = 0.012
for k_, (o_, w_) in enumerate([(-2.6, 0.8), (-1.5, 0.7), (2.4, 0.8), (3.4, 0.7), (4.4, 0.8), (5.5, 0.7), (6.5, 0.6)]):   # rubber streaks that follow the road/bend
    ribbon("tyre%d" % k_, S0 + 20 * k_, S1 - 25 * (k_ % 3), o_ - w_ / 2, o_ + w_ / 2, 0.003, M["tyre"], "ground2", n=240)
def kerb(side, nme):
    va = []; fa = []; vb = []; fb = []; L = 1.1; n = int((S1 - S0) / L)
    for i in range(n):
        sa = S0 + i * L; sb = sa + L; V, F = (va, fa) if i % 2 == 0 else (vb, fb); k = len(V)
        o0, o1 = (-6.1, -3.75) if side < 0 else (7.4, 9.75); z0, z1 = (0.0, 0.012) if side < 0 else (0.012, 0.0)
        V += [P(sa, o0, z0), P(sb, o0, z0), P(sb, o1, z1), P(sa, o1, z1)]; F.append((k, k + 1, k + 2, k + 3))
    mesh_obj(nme + "_a", va, fa, M["kerb_a"], "building"); mesh_obj(nme + "_b", vb, fb, M["kerb_b"], "ground2")
kerb(-1, "kerb_out"); kerb(+1, "kerb_in")
def grass(o0, o1, name):
    nx, ny = 200, 20; ss = np.linspace(S0, S1, nx); oo = np.linspace(o0, o1, ny); v = []
    for s in ss:
        for o in oo: x, y, _ = P(s, o); v.append((x, y, -0.02 - 0.05 * math.sin(s * 0.05) * math.sin(o * 0.3) + (rng.random() - 0.5) * 0.03))
    idx = np.arange(nx * ny).reshape(nx, ny); faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4).tolist()
    mesh_obj(name, v, faces, M["grass"], "building", True)
grass(-70.0, -6.1, "grass_out"); grass(9.75, 70.0, "grass_in")
def box(name, c, s, m, grp, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.name = name; o.scale = s; o.rotation_euler[2] = rz; o.data.materials.append(m); o["grp"] = grp
for s in np.arange(S0, S1, 7.0):                # concrete barrier on the inside + fence posts (segments follow the bend)
    x, y, _ = P(s + 3.5, 18.0); box("bar", (x, y, 0.55), (7.2, 0.25, 1.1), M["barrier"], "building", (s + 3.5) / R)
    x, y, _ = P(s + 3.5, 17.8); box("post", (x, y, 1.7), (0.07, 0.07, 2.3), M["barrier"], "building")
for i in range(70):
    s_ = rng.uniform(-250, 320); off = rng.uniform(85, 200); h = rng.uniform(8, 13)
    for k in range(rng.integers(4, 8)):
        x, y, _ = P(s_ + rng.uniform(-9, 9), off + rng.uniform(-5, 5)); r = rng.uniform(2.6, 4.6); hh = h * rng.uniform(0.6, 1.1)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, y, hh * 0.45)); bpy.ops.object.shade_smooth()
        o = bpy.context.object; o.scale = (r, r * rng.uniform(0.9, 1.2), hh * 0.5); o.data.materials.append(M["tree"]); o["grp"] = "building"
nx, ny = 220, 40; ss = np.linspace(-700, 900, nx); oo = np.linspace(230, 700, ny); v = []
for s in ss:
    for o in oo: x, y, _ = P(s, o); v.append((x, y, 8 + 20 * (math.sin(s * 0.006 + 1) * 0.5 + 0.5) * (math.sin(s * 0.017) * 0.3 + 0.7) + (o - 230) * 0.05))
idx = np.arange(nx * ny).reshape(nx, ny); faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4).tolist()
mesh_obj("hills", v, faces, M["hill"], "building", True)
W = sc.world; et = next(n for n in W.node_tree.nodes if n.bl_idname == "ShaderNodeTexEnvironment")
et.image = bpy.data.images.load(os.environ.get("HDRI", "C:/Users/Internet/Desktop/TEST COMFYUI/mclaren/hdri/DaySkyHDRI058B_8K_HDR.exr"), check_existing=True)
if VIEW == "C":      # pit-wall + stands on the far (outer) side, like the white wall and grandstand behind the Porsche
    for s_ in np.arange(S0, S1, 7.0):
        x, y, _ = P(s_ + 3.5, -13.0); box("pitwall", (x, y, 0.6), (7.2, 0.4, 1.2), M["line"], "ground2", (s_ + 3.5) / R)
    for s_ in np.arange(S0, S1, 30.0):
        x, y, _ = P(s_ + 15, -60.0); box("stand", (x, y, 3.2), (30.0, 12.0, 6.4), M["barrier"], "building", (s_ + 15) / R)
# car: slight steering angle, follows the bend
root = bpy.data.objects["RootNode"]; root.rotation_euler = (0, 0, math.radians(90 + float(os.environ.get("STEER", "-5"))))
VIEWS = {   # camera xyz, aim xyz, roll deg, lens mm, shift_y
    "A": ((5.3, -6.6, 0.50), (0.2, 0.0, 0.62), -5.0, 50.0, 0.0),
    "B": ((4.6, -3.1, 1.5), (0.4, 0.2, 0.40), -9.0, 24.0, 0.0),
    "C": ((-5.6, 10.6, 0.55), (0.0, 0.0, 0.60), 3.5, 70.0, 0.16),
}
cp, ap, roll, lens, shy = VIEWS[VIEW]
cam = sc.camera; cam.location = cp; cam.data.lens = lens; cam.data.dof.use_dof = False; cam.data.shift_x = 0.13 if VIEW == 'B' else 0.0; cam.data.shift_y = shy; cam.data.clip_end = 5000.0; cam.rotation_mode = 'XYZ'
q = (Vector(ap) - cam.location).to_track_quat('-Z', 'Y'); cam.rotation_euler = (q @ Euler((0, 0, math.radians(roll))).to_quaternion()).to_euler()
if VIEW == "B":   # pure translation of the camera to its own left (orientation, lens and shift unchanged)
    tl = float(os.environ.get("TRANS_B", "0.5")); left = cam.rotation_euler.to_quaternion() @ Vector((-1, 0, 0)); cam.location = cam.location + left * tl; print("B moved left by", tl, "to", tuple(cam.location))
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False); print("SAVED", OUT, VIEW)
