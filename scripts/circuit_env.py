"""Blender environment of a real race circuit (layout reference only): asphalt ribbon, white lines, red/white kerbs, asphalt run-off,
gravel trap, grass, tyre barriers, catch fence, far grandstands with white tent roofs, tree line / hills. Everything follows the car path."""
import math, random, bpy, bmesh
from mathutils import Vector
import proxy_city as pc

HW = 8.4   # road half width


def _subdivide(P, step=1.5):
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(round((b - a).length / step)))
        for k in range(1, n + 1): out.append(a.lerp(b, k / n))
    return out


def build(scene, seed=11):
    rnd = random.Random(seed)
    for _n in ("PROXY_CITY", "CIRCUIT_ENV"):
        old = bpy.data.objects.get(_n)
        if old: bpy.data.objects.remove(old, do_unlink=True)
    road = bpy.data.objects.get("NurbsPath.001")
    if road: road.hide_render = True
    P = _subdivide(pc._path(scene, ext=200.0), 1.5)
    N = len(P)
    T = [(P[min(i + 1, N - 1)] - P[max(i - 1, 0)]).normalized() for i in range(N)]
    Nn = [Vector((-t.y, t.x, 0)) for t in T]
    B = pc.Builder(); bm = B.bm

    def strip(a, b, z, tone_fn):
        """continuous quad strip between signed lateral offsets a<b along the path"""
        for i in range(N - 1):
            tone = tone_fn(i)
            vs = [bm.verts.new(P[i] + Nn[i] * a + Vector((0, 0, z))), bm.verts.new(P[i + 1] + Nn[i + 1] * a + Vector((0, 0, z))),
                  bm.verts.new(P[i + 1] + Nn[i + 1] * b + Vector((0, 0, z))), bm.verts.new(P[i] + Nn[i] * b + Vector((0, 0, z)))]
            f = bm.faces.new(vs)
            for l in f.loops:
                l[B.cl] = (tone, tone, tone, 1.0); l[B.cc] = (0.0, 0.0, 0.0, 1.0)

    const = lambda v: (lambda i: v)
    # ground bands, widest first (higher z wins)
    for s in (1, -1):
        lo = lambda a, b: (min(a, b), max(a, b))
        strip(*lo(s * 30, s * 900), 0.010, const(0.22))                                    # grass
        strip(*lo(s * (HW + 9.0), s * 30), 0.015, lambda i: 0.46 + 0.04 * math.sin(i * 0.3))   # gravel trap
        strip(*lo(s * (HW + 1.3), s * (HW + 9.0)), 0.020, const(0.21))                       # asphalt run-off
        strip(*lo(s * HW, s * (HW + 1.3)), 0.040, lambda i: 0.33 if (i // 2) % 2 else 0.86)  # kerb (red / white)
    strip(-HW, HW, 0.030, lambda i: 0.15 + 0.022 * math.sin(i * 0.05) + 0.014 * math.sin(i * 0.173 + 1.0))                                                       # racing asphalt
    for s in (1, -1):
        a, b = sorted((s * (HW - 0.55), s * (HW - 0.30))); strip(a, b, 0.045, const(0.80))   # edge line
    for k, off in enumerate([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]):   # soft rubbered racing line (smooth gradient)
        w = 0.5 * (1 - abs(off) / 3.6)
        strip(off - 0.5, off + 0.5, 0.034 + 0.0005 * k, lambda i, off=off, w=w: 0.15 - 0.045 * w * (0.8 + 0.2 * math.sin(i * 0.2 + off)))
    # TYREMARKS: dark rubber lanes with gaps, weaving around the racing line
    for k, (off, wd) in enumerate([]):
        strip(off - wd / 2, off + wd / 2, 0.037 + 0.001 * k, lambda i, k=k: 0.095 + 0.03 * abs(math.sin(i * 0.11 + k * 1.7)) + (0.055 if math.sin(i * 0.045 + k * 2.3) < -0.1 else 0.0))
    # barriers, fence, grandstands, trees
    for s in (1, -1):
        for i in range(0, N, 4):
            t, n = T[i], Nn[i] * s; a = math.atan2(t.y, t.x)
            B.box(P[i] + n * (HW + 16.0), (6.0, 1.0, 1.25), a, 0.78 if (i // 4) % 3 == 0 else 0.20, flat=False)      # tyre wall blocks
        for i in range(0, N, 2):
            t, n = T[i], Nn[i] * s; a = math.atan2(t.y, t.x)
            pass
    # grandstands with white tent roofs (both sides, with gaps), far trees / hills
    for s in ():   # no stands
        i = 20
        while i < N - 30:
            if 100 < i < 270: i = 270   # KEEP_CLEAR: nothing beside the car at the frames we shoot
            run = rnd.choice([22, 30, 38])   # SPARSE: short stands
            seg = range(i, min(i + run, N - 2)); mid = P[seg[len(seg) // 2]]; t = T[seg[len(seg) // 2]]; n = Nn[seg[len(seg) // 2]] * s
            a = math.atan2(t.y, t.x); length = len(seg) * 1.5
            base = HW + 48.0 + rnd.uniform(0, 20)
            tiers = rnd.choice([2, 3])
            for k in range(tiers):
                B.box(mid + n * (base + 1.1 * k), (length, 1.2, 0.7 * (k + 1)), a, 0.34 + 0.03 * (k % 2), cls=pc.CLS_CROWD)
            top = 0.7 * tiers + 3.5
            B.box(mid + n * (base + 0.55 * tiers), (length + 4, 1.1 * tiers + 3, 0.5), a, 0.88, z0=top)          # white tent roof
            for dx in range(-int(length / 2) + 2, int(length / 2), 14):
                B.box(mid + t * dx + n * (base + 1.1 * tiers + 1.0), (0.5, 0.5, top), a, 0.55)
            B.box(mid + n * (base + 1.1 * tiers + 2.5), (length + 6, 3, 7), a, 0.28)                              # rear block
            i += run + rnd.choice([70, 100, 130])
    # TERRAIN: rolling meadows and soft hills (like the reference photos) + clustered tree lines, instead of far cubes
    import bmesh as _bm
    LAT = [HW + 28, HW + 55, HW + 95, HW + 145, HW + 205, HW + 275, HW + 355, HW + 450, HW + 560, HW + 700, HW + 800, HW + 900]
    def height(i, lat, s):
        ph = 1.7 if s > 0 else 4.1
        v = 0.5 * math.sin(i * 0.019 + ph ) + 0.3 * math.sin(i * 0.043 - ph * 1.3) + 0.2 * math.sin(i * 0.097 + ph * 0.7)
        far = max(0.0, min(1.0, (lat - (HW + 90)) / 520.0)) * 15.0 * (0.55 + 0.45 * v) + max(0.0, min(1.0, (lat - HW - 380) / 320.0)) * 26.0 * (0.6 + 0.4 * v)
        mead = 0.9 * math.sin(i * 0.05 + lat * 0.05 + ph) * max(0.0, min(1.0, (lat - HW - 25) / 50.0))
        return 0.06 + far + mead
    tfaces = []
    for s in (1, -1):
        rows = []
        for i in range(0, N - 4, 4):
            rows.append([bm.verts.new(P[i] + Nn[i] * s * lat + Vector((0, 0, height(i, lat, s)))) for lat in LAT])
        for r0, r1 in zip(rows[:-1], rows[1:]):
            for k in range(len(LAT) - 1):
                tfaces.append(bm.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k])))
        bm.normal_update()
    for f in tfaces:
        n = f.normal if f.normal.z > 0 else -f.normal
        sh = 0.55 + 0.45 * max(0.0, n.dot(pc.L_SUN)); dist = (sum(v.co.xy.length for v in f.verts) / 4.0)
        tone = 0.30 * sh
        for l in f.loops:
            l[B.cl] = (tone, tone, tone, 1.0); l[B.cc] = (0.0, 0.0, 0.0, 1.0)
    _os = __import__('os')
    if _os.environ.get('TREE_FRAME'): scene.frame_set(int(_os.environ['TREE_FRAME']))
    from bpy_extras.object_utils import world_to_camera_view as _w2c
    _xmax = float(_os.environ.get('TREE_XMAX', '9'))
    # forest: continuous low lumpy canopy of broad rounded trees along the ridge, a few taller ones (reference stile_6)
    _os = __import__('os')
    if _os.environ.get('TREE_FRAME'): scene.frame_set(int(_os.environ['TREE_FRAME']))
    from bpy_extras.object_utils import world_to_camera_view as _w2c
    _xmax = float(_os.environ.get('TREE_XMAX', '9'))
    for s in (int(_os.environ.get('TREE_SIDE', '1')),):
        ph = [rnd.uniform(0, 6.28) for _ in range(4)]
        for layer in range(5):
            i = rnd.randint(0, 6)
            while i < N - 8:
                run = rnd.randint(150, 320); lat0 = rnd.uniform(HW + 520, HW + 700) + layer * rnd.uniform(-30, 30); drift = rnd.uniform(-0.3, 0.3)
                for j in range(run):
                    ii = min(N - 1, i + j)
                    env = 0.70 + 0.18 * math.sin(ii * 0.031 + ph[0] + layer) + 0.12 * math.sin(ii * 0.113 + ph[1]) + 0.08 * math.sin(ii * 0.29 + ph[2] + layer)
                    for k in range(rnd.choice([2, 3])):
                        lat = lat0 + drift * j + rnd.uniform(-22, 22)
                        c = P[ii] + Nn[ii] * s * lat
                        gz = height(ii, lat, s)
                        taper = 1.0
                        if _xmax < 5:
                            xs = _w2c(scene, scene.camera, Vector((c.x, c.y, gz + 2.0))).x
                            if xs > _xmax or xs < -0.25: continue
                            taper = max(0.0, min(1.0, (_xmax - xs) / 0.16))
                            if taper < 0.25: continue
                        big = False
                        r = rnd.uniform(8.0, 14.0) * max(0.6, env) * (0.55 + 0.45 * taper)
                        zs = rnd.uniform(0.6, 0.95)
                        wx = rnd.uniform(0.55, 0.85) if big else rnd.uniform(0.9, 1.7)
                        wy = rnd.uniform(0.55, 0.85) if big else rnd.uniform(0.9, 1.7)
                        res = _bm.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
                        M = pc.Matrix.Translation((c.x, c.y, gz + r * zs * 0.30)) @ pc.Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z') @ pc.Matrix.Diagonal((r * wx, r * wy, r * zs * (2.2 if big else 1.0), 1.0))
                        _bm.ops.transform(bm, matrix=M, verts=res["verts"]); bm.normal_update()
                        tone = rnd.choice([0.03, 0.035, 0.04, 0.05])
                        for f in {f for v in res["verts"] for f in v.link_faces}:
                            sh = 0.7 + 0.3 * max(0.0, f.normal.dot(pc.L_SUN))
                            for l in f.loops:
                                l[B.cl] = (tone * sh, tone * sh, tone * sh, 1.0); l[B.cc] = (0.0, 0.0, 0.0, 1.0)
                i += run + rnd.randint(0, 3)
    ob = B.finish(); print("CIRCUIT faces", len(ob.data.polygons))
    return ob
