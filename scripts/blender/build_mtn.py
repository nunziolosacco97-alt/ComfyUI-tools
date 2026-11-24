"""McLaren on a grassy crest with alpine mountains behind (reference: GMC Hummer on hill, Dolomites).
usage: blender -b ../mclaren_scene_v2.blend --python build_mtn.py -- OUT.blend
Removes the urban volumes, builds one displaced terrain (crest + valley + mountains), clay material, keeps car/camera/sun.
env: SEED, SUN_AZ, CAM_Z"""
import bpy, sys, os, math, bmesh
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0]
SEED = int(os.environ.get("SEED", "7")); rng = np.random.default_rng(SEED)
sc = bpy.context.scene

# ---- remove the city ----
for o in [o for o in bpy.data.objects if o.type == 'MESH' and "grp" in o.keys()]:
    bpy.data.objects.remove(o, do_unlink=True)

# ---- noise helpers (numpy value noise, periodic-free) ----
def vnoise(x, y, seed):
    r = np.random.default_rng(seed); N = 256; g = r.random((N, N)).astype(np.float32)
    xi = np.floor(x).astype(int); yi = np.floor(y).astype(int); xf = x - xi; yf = y - yi
    sx = xf * xf * (3 - 2 * xf); sy = yf * yf * (3 - 2 * yf)
    a = g[yi % N, xi % N]; b = g[yi % N, (xi + 1) % N]; c = g[(yi + 1) % N, xi % N]; d = g[(yi + 1) % N, (xi + 1) % N]
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy
def fbm(x, y, oct, seed, lac=2.0, gain=0.5):
    s = 0; amp = 1; tot = 0
    for i in range(oct):
        s = s + amp * vnoise(x, y, seed + i); tot += amp; amp *= gain; x = x * lac + 17.3; y = y * lac + 9.1
    return s / tot
def ridged(x, y, oct, seed):
    s = 0; amp = 1; tot = 0
    for i in range(oct):
        n = 1 - np.abs(2 * vnoise(x, y, seed + i) - 1); n = n * n; s = s + amp * n; tot += amp; amp *= 0.5; x = x * 2.1 + 5.7; y = y * 2.1 + 3.3
    return s / tot
def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ---- terrain grid, dense near the car ----
cam = sc.camera; cw = cam.matrix_world
fwd = (cw.to_quaternion() @ Vector((0, 0, -1))); V = np.array([fwd.x, fwd.y]); V /= np.linalg.norm(V); Pp = np.array([-V[1], V[0]])
L = 3200.0; n = 1001
u = np.linspace(-1, 1, n); xs = L * (u + 8 * u ** 3) / 9
X, Y = np.meshgrid(xs, xs)
t = X * V[0] + Y * V[1]; s = X * Pp[0] + Y * Pp[1]; r = np.hypot(X, Y)
# local crest: flat under the car, gentle roll, rising grass slope toward the camera, drop behind
roll = ((fbm(X * 0.15, Y * 0.15, 4, 11) - 0.5) * 0.9 + (fbm(X * 0.9, Y * 0.9, 3, 21) - 0.5) * 0.12) * (1 + 1.8 * sm(9, 30, r))
H = roll * sm(3.8, 9.0, r)
H -= 1.6 * sm(3.0, 19.0, -t) * (1 + 0.15 * (fbm(X * 0.3, Y * 0.3, 2, 31) - 0.5))      # slope up toward the camera
H += 0.12 * sm(5, 30, -t) * (-t / 10.0) * 0 + 0.0
drop = sm(2.5, 40.0, t) * 0.55 + sm(40.0, 260.0, t) * 0.45                               # crest then fall into the valley
H -= 58.0 * drop
# valley floor with foothills
foot = fbm(X * 0.004, Y * 0.004, 5, 41); H += 38 * (foot - 0.45) * sm(120, 500, t)
# mountains: a wall of ridged peaks centred behind the car
band = np.exp(-(s / 900.0) ** 2) * sm(700, 1400, t) * (1 - sm(3200, 4400, t))
m = ridged(X * 0.0035, Y * 0.0035 + 3.0, 6, 51) * 0.75 + fbm(X * 0.002, Y * 0.002, 3, 61) * 0.5
peak = np.exp(-((s - 120) / 380.0) ** 2) * 1.0 + 0.55 * np.exp(-((s + 480) / 330.0) ** 2) + 0.45 * np.exp(-((s - 650) / 260.0) ** 2)
H += band * (50 + 280 * m ** 1.6 * (0.45 + 0.75 * peak))
H += (vnoise(X * 3.0, Y * 3.0, 77) - 0.5) * 0.05 * sm(3, 12, r) * (1 - sm(30, 120, r))   # tiny ground grain near camera
H = H.astype(np.float32)

verts = np.stack([X, Y, H], -1).reshape(-1, 3)
idx = np.arange(n * n).reshape(n, n)
faces = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)
mesh = bpy.data.meshes.new("terrain"); mesh.from_pydata(verts.tolist(), [], faces.tolist()); mesh.update()
ter = bpy.data.objects.new("terrain", mesh); sc.collection.objects.link(ter); ter["grp"] = "ground"
for p in mesh.polygons: p.use_smooth = True
# keep the ground under the camera slightly below the lens
hc = float(np.interp(0, [0, 1], [0, 1]))
ix = int(np.abs(xs - cw.translation.x).argmin()); iy = int(np.abs(xs - cw.translation.y).argmin())
print("TERRAIN verts", len(verts), "H at cam", H[iy, ix], "cam z", cw.translation.z, "H at car", H[int(np.abs(xs).argmin()), int(np.abs(xs).argmin())], "Hmax", H.max(), "Hmin", H.min())

# ---- clay material (muted, tone shifts with height so ridges read) ----
m_ = bpy.data.materials.new("clay_ground"); m_.use_nodes = True; nt = m_.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = 0.95
g = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ"); mr = nt.nodes.new("ShaderNodeMapRange"); cr = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(g.outputs["Position"], sp.inputs[0]); mr.inputs["From Min"].default_value = -10.0; mr.inputs["From Max"].default_value = 260.0
nt.links.new(sp.outputs["Z"], mr.inputs["Value"]); mr.clamp = True; nt.links.new(mr.outputs[0], cr.inputs[0])
cr.color_ramp.elements[0].color = (0.22, 0.22, 0.21, 1); cr.color_ramp.elements[1].color = (0.52, 0.51, 0.50, 1)
nt.links.new(cr.outputs[0], b.inputs["Base Color"])
ter.data.materials.append(m_)

# ---- a few low rocks around the crest (shape cues for the model) ----
rocks = []
for i in range(26):
    ang = rng.uniform(0, 2 * math.pi); rad = rng.uniform(5.5, 24.0); px, py = rad * math.cos(ang), rad * math.sin(ang)
    ix = int(np.abs(xs - px).argmin()); iy = int(np.abs(xs - py).argmin()); hz = float(H[iy, ix])
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(px, py, hz))
    o = bpy.context.object; sz = rng.uniform(0.07, 0.28); o.scale = (sz * rng.uniform(0.8, 1.6), sz * rng.uniform(0.8, 1.6), sz * rng.uniform(0.4, 0.8)); o.rotation_euler[2] = rng.uniform(0, 6)
    o.data.materials.append(m_); o["grp"] = "ground"; rocks.append(o)

# ---- camera: low, 3/4 front (unchanged lens/position), small tweak so crest line sits below the car ----
CD = float(os.environ.get("CAM_DIST", "1.7")); cam.location.x *= CD; cam.location.y *= CD
tc = cam.location.x * V[0] + cam.location.y * V[1]; ixc = int(np.abs(xs - cam.location.x).argmin()); iyc = int(np.abs(xs - cam.location.y).argmin())
cam.location.z = float(H[iyc, ixc]) + float(os.environ.get("CAM_H", "1.9")); print('CAMFINAL', tuple(cam.location), 'ground', H[iyc, ixc]); cam.data.clip_end = 20000.0; cam.data.clip_start = 0.1
cam.data.dof.use_dof = False; cam.data.shift_x = float(os.environ.get('SHIFT_X', '-0.13'))
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)
print("SAVED", OUT)
