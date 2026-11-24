"""McLaren speeding on a race track (refs: BMW/Porsche panning shots). Low dramatic 3/4-front camera with a small dutch roll,
red/white kerb between camera and car, dark asphalt, grass run-off, barrier, tree line, low hills.
usage: blender -b ../mclaren_scene_v2.blend --python build_track.py -- OUT.blend
env: CAM (x,y,z), ROLL (deg), SUN_AZ not used (HDRI/sun from v2)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Euler
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0]
sc = bpy.context.scene; rng = np.random.default_rng(5)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and "grp" in o.keys()]: bpy.data.objects.remove(o, do_unlink=True)

def mat(name, v, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (v, v, v, 1); b.inputs["Roughness"].default_value = rough; return m
M = {k: mat("clay_" + k, v) for k, v in dict(asphalt=0.12, kerb_a=0.22, kerb_b=0.62, line=0.75, grass=0.30, barrier=0.50, tree=0.16, hill=0.36).items()}
def mesh_obj(name, verts, faces, m, grp):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m); o["grp"] = grp
    for p in me.polygons: p.use_smooth = False
    return o
def quad_strip(x0, x1, y0, y1, z, n=1):
    xs = np.linspace(x0, x1, n + 1); v = []; f = []
    for i, x in enumerate(xs): v += [(x, y0, z), (x, y1, z)]
    for i in range(n): a = 2 * i; f.append((a, a + 1, a + 3, a + 2))
    return v, f
def box(name, c, s, m, grp):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.name = name; o.scale = s; o.data.materials.append(m); o["grp"] = grp; return o

X0, X1 = -400.0, 400.0
# asphalt (car at origin, front +X): y -3.6 .. 7.4
v, f = quad_strip(X0, X1, -3.6, 7.4, 0.0); mesh_obj("asphalt", v, f, M["asphalt"], "ground")
# white edge line next to the kerb
v, f = quad_strip(X0, X1, -3.75, -3.55, 0.004); mesh_obj("edge_line", v, f, M["line"], "ground2")
# red/white kerb strip between camera and car: alternating 1.1 m blocks, slightly raised
va = []; fa = []; vb = []; fb = []; n = int((X1 - X0) / 1.1)
for i in range(n):
    xa = X0 + i * 1.1; xb = xa + 1.1; tgt = (va, fa) if i % 2 == 0 else (vb, fb); V, F = tgt; k = len(V)
    V += [(xa, -6.1, 0.0), (xb, -6.1, 0.0), (xb, -3.75, 0.012), (xa, -3.75, 0.012)]; F.append((k, k + 1, k + 2, k + 3))
mesh_obj("kerb_a", va, fa, M["kerb_a"], "building"); mesh_obj("kerb_b", vb, fb, M["kerb_b"], "ground2")
# grass run-off both sides, gently rolling, with a ditch edge
def grass(y0, y1, name):
    nx, ny = 160, 24; xs = np.linspace(X0, X1, nx); ys = np.linspace(y0, y1, ny); X, Y = np.meshgrid(xs, ys)
    Z = -0.02 - 0.06 * np.sin(X * 0.05) * np.sin(Y * 0.3) + (rng.random(X.shape) - 0.5) * 0.03
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3).tolist(); idx = np.arange(nx * ny).reshape(ny, nx)
    faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4).tolist()
    o = mesh_obj(name, verts, faces, M["grass"], "building"); [setattr(p, "use_smooth", True) for p in o.data.polygons]; return o
grass(-60.0, -6.1, "grass_cam"); grass(7.4, 60.0, "grass_far")
# barrier + catch fence posts on the far side, grandstand-less
box("barrier", (0, 16.0, 0.55), (X1 * 2, 0.25, 1.1), M["barrier"], "building")
for i in range(0, 400, 3): box("post%d" % i, (X0 + i * 2.0, 15.8, 1.6), (0.07, 0.07, 2.2), M["barrier"], "building")
# tree line (clumps) and low hills behind
for i in range(110):
    x = rng.uniform(-300, 300); y = rng.uniform(100, 190); h = rng.uniform(9, 17); r = rng.uniform(4.0, 8.0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(x, y, h * 0.55)); o = bpy.context.object; bpy.ops.object.shade_smooth(); o.scale = (r, r, h * 0.55); o.data.materials.append(M["tree"]); o["grp"] = "building"
nx, ny = 200, 40; xs = np.linspace(-900, 900, nx); ys = np.linspace(120, 700, ny); XX, YY = np.meshgrid(xs, ys)
ZZ = 12 + 22 * (np.sin(XX * 0.006 + 1) * 0.5 + 0.5) * (np.sin(XX * 0.017) * 0.3 + 0.7) + (YY - 120) * 0.06
verts = np.stack([XX, YY, ZZ], -1).reshape(-1, 3).tolist(); idx = np.arange(nx * ny).reshape(ny, nx)
faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4).tolist()
o = mesh_obj("hills", verts, faces, M["hill"], "building"); [setattr(p, "use_smooth", True) for p in o.data.polygons]

# car: slight steering angle on the track
root = bpy.data.objects["RootNode"]; root.rotation_euler = (0, 0, math.radians(90 + float(os.environ.get("STEER", "-7"))))
# camera: low, near the kerb, dutch roll
cam = sc.camera; cx, cy, cz = [float(t) for t in os.environ.get("CAM", "5.3,-6.6,0.5").split(",")]
cam.location = (cx, cy, cz); cam.data.dof.use_dof = False; cam.data.shift_x = 0.0; cam.data.shift_y = 0.0; cam.data.clip_end = 5000.0
tgt = Vector((0.2, 0.0, float(os.environ.get("AIM_Z", "0.62")))); q = (tgt - cam.location).to_track_quat('-Z', 'Y'); e = q.to_euler()
cam.rotation_euler = (e.x, e.y, e.z); cam.rotation_mode = 'XYZ'
cam.rotation_euler = (q @ Euler((0, 0, math.radians(float(os.environ.get("ROLL", "-5"))))).to_quaternion()).to_euler()
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False); print("SAVED", OUT)
