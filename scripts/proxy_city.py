"""Grey proxy city around the track (layout only). v2: true road width, race-track asphalt details (tyre marks, racing line, edge lines, kerbs),
crowd/window textures through a class mask, advertising hoardings and billboards. Deterministic (seeded)."""
import math, random, bpy, bmesh, numpy as np
from mathutils import Vector, Matrix

L_SUN = Vector((0.45, -0.55, 0.70)).normalized()
CLS_NONE, CLS_CROWD, CLS_FACADE = 0.0, 1.0, 2.0


def _path(scene, ext=140.0):
    dg = bpy.context.evaluated_depsgraph_get()
    co = bpy.data.objects["NurbsPath"]; me = co.evaluated_get(dg).to_mesh()
    P = [co.matrix_world @ v.co for v in me.vertices]
    P = [Vector((p.x, p.y, 0.0)) for p in P]
    t0 = (P[0] - P[1]).normalized(); t1 = (P[-1] - P[-2]).normalized()
    pre = [P[0] + t0 * d for d in np.arange(ext, 0, -6.0)]
    post = [P[-1] + t1 * d for d in np.arange(6.0, ext + 1, 6.0)]
    P = pre + P + post
    out = [P[0]]; acc = 0.0
    for a, b in zip(P[:-1], P[1:]):
        seg = (b - a).length
        while acc + seg >= 3.0:
            k = (3.0 - acc) / seg; a = a.lerp(b, k); out.append(a); seg = (b - a).length; acc = 0.0
        acc += seg
    return out


def _halfwidth(P):
    """true half width: only road vertices within 12 m laterally of the centre line (other track sections ignored)"""
    rd = bpy.data.objects["NurbsPath.001"]
    V = np.array([(rd.matrix_world @ v.co)[:2] for v in rd.data.vertices])
    hs = []
    for i in range(2, len(P) - 2, 4):
        t = (P[i + 1] - P[i - 1]).normalized(); n = np.array([-t.y, t.x]); p = np.array(P[i][:2])
        d = V - p; al = d @ np.array([t.x, t.y]); la = d @ n
        m = (np.abs(al) < 4) & (np.abs(la) < 12)
        if m.sum() > 2: hs.append(np.abs(la[m]).max())
    return 8.7   # measured: road mesh is +-8.6..8.8 m around the centre line


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.cl = self.bm.loops.layers.float_color.new("Col")
        self.cc = self.bm.loops.layers.float_color.new("Cls")

    def box(self, c, size, ang, tone, z0=0.0, cls=CLS_NONE, flat=False):
        sx, sy, sz = size
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        M = Matrix.Translation((c.x, c.y, z0 + sz / 2)) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Diagonal((sx, sy, sz, 1.0))
        bmesh.ops.transform(self.bm, matrix=M, verts=res["verts"])
        self.bm.normal_update()
        for f in {f for v in res["verts"] for f in v.link_faces}:
            n = f.normal
            if flat: sh = 1.0
            elif n.z > 0.9: sh = 1.0
            elif n.z < -0.9: sh = 0.3
            else: sh = 0.45 + 0.55 * max(0.0, n.dot(L_SUN))
            col = (tone * sh, tone * sh, tone * sh, 1.0)
            k = cls if abs(n.z) < 0.9 else (CLS_CROWD if cls == CLS_CROWD else CLS_NONE)
            for l in f.loops:
                l[self.cl] = col; l[self.cc] = (k, k, k, 1.0)

    def finish(self):
        me = bpy.data.meshes.new("PROXY_CITY"); self.bm.normal_update(); self.bm.to_mesh(me); self.bm.free()
        m = bpy.data.materials.new("PROXY"); m.use_nodes = True
        nt = m.node_tree; nd = nt.nodes; lk = nt.links; pb = nd.get("Principled BSDF")
        col = nd.new("ShaderNodeAttribute"); col.attribute_name = "Col"
        cls = nd.new("ShaderNodeAttribute"); cls.attribute_name = "Cls"
        sep = nd.new("ShaderNodeSeparateColor"); lk.new(cls.outputs["Color"], sep.inputs["Color"])
        def math(op, a=None, b=None):
            n = nd.new("ShaderNodeMath"); n.operation = op
            if a is not None: lk.new(a, n.inputs[0]) if not isinstance(a, float) else setattr(n.inputs[0], "default_value", a)
            if b is not None: lk.new(b, n.inputs[1]) if not isinstance(b, float) else setattr(n.inputs[1], "default_value", b)
            return n
        tc = nd.new("ShaderNodeTexCoord")
        # crowd: fine high-contrast noise (heads / people)
        nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 6.0; nz.inputs["Roughness"].default_value = 0.8
        lk.new(tc.outputs["Object"], nz.inputs["Vector"])
        cr = nd.new("ShaderNodeMapRange"); cr.inputs["From Min"].default_value = 0.35; cr.inputs["From Max"].default_value = 0.65
        cr.inputs["To Min"].default_value = 0.35; cr.inputs["To Max"].default_value = 1.35; lk.new(nz.outputs["Fac"], cr.inputs["Value"])
        # facades: window grid (3D checker, cells ~ 2.6 m wide x 3.4 m tall)
        mp = nd.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.55, 0.55, 0.33); lk.new(tc.outputs["Object"], mp.inputs["Vector"])
        ck = nd.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = 1.0; lk.new(mp.outputs["Vector"], ck.inputs["Vector"])
        fr = nd.new("ShaderNodeMapRange"); fr.inputs["To Min"].default_value = 0.62; fr.inputs["To Max"].default_value = 1.18; lk.new(ck.outputs["Fac"], fr.inputs["Value"])
        isC = math("LESS_THAN", None, 1.5); lk.new(sep.outputs["Red"], isC.inputs[0])
        gC = math("GREATER_THAN", None, 0.5); lk.new(sep.outputs["Red"], gC.inputs[0])
        m1 = math("MULTIPLY", isC.outputs[0], gC.outputs[0])            # crowd mask
        m2 = math("GREATER_THAN", None, 1.5); lk.new(sep.outputs["Red"], m2.inputs[0])   # facade mask
        mixc = nd.new("ShaderNodeMix"); mixc.data_type = "FLOAT"; lk.new(m1.outputs[0], mixc.inputs["Factor"]); mixc.inputs["A"].default_value = 1.0; lk.new(cr.outputs["Result"], mixc.inputs["B"])
        mixf = nd.new("ShaderNodeMix"); mixf.data_type = "FLOAT"; lk.new(m2.outputs[0], mixf.inputs["Factor"]); lk.new(mixc.outputs["Result"], mixf.inputs["A"]); lk.new(fr.outputs["Result"], mixf.inputs["B"])
        mul = nd.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1.0
        lk.new(col.outputs["Color"], mul.inputs["A"]); lk.new(mixf.outputs["Result"], mul.inputs["B"])
        lk.new(mul.outputs["Result"], pb.inputs["Base Color"]); pb.inputs["Roughness"].default_value = 0.9
        for nm in ("Specular IOR Level", "Specular"):
            if nm in pb.inputs: pb.inputs[nm].default_value = 0.0
        me.materials.append(m)
        ob = bpy.data.objects.new("PROXY_CITY", me); bpy.context.scene.collection.objects.link(ob)
        return ob


def build(scene, seed=7):
    old = bpy.data.objects.get('PROXY_CITY')
    if old: bpy.data.objects.remove(old, do_unlink=True)
    rnd = random.Random(seed)
    P = _path(scene); hw = _halfwidth(P)
    print("PROXY hw=%.1f samples=%d" % (hw, len(P)))
    B = Builder(); occupied = []

    def tang(i):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, len(P) - 1)]; return (b - a).normalized()

    def free(c, r, own=None):
        for j, q in enumerate(P):
            if own is not None and abs(j - own) <= 16: continue
            if (q - c).length < r + hw + 3: return False
        for (x, y, rr) in occupied:
            if (x - c.x) ** 2 + (y - c.y) ** 2 < (r + rr) ** 2 * 0.8: return False
        return True

    # ---- race-track asphalt details (flat, just above the road) ----
    wob = [0.0]
    for i in range(len(P)):
        wob.append(wob[-1] * 0.97 + rnd.uniform(-0.03, 0.03))
    for i in range(len(P)):
        t = tang(i); n = Vector((-t.y, t.x, 0)); a = math.atan2(t.y, t.x)
        # racing line: wide dark rubbered band + two tyre-mark pairs (lighter/darker)
        line = 1.2 * math.sin(i * 0.045) + wob[i]
        B.box(P[i] + n * line, (3.2, 2.2, 0.01), a, 0.09, z0=0.05, flat=True)
        for off, w_, tone in ((-0.9, 0.28, 0.045), (0.9, 0.28, 0.045), (2.6, 0.22, 0.055), (-2.6, 0.22, 0.055), (4.2, 0.16, 0.07), (-4.5, 0.16, 0.07)):
            if math.sin(i * 0.13 + off * 7.0) > -0.55:
                B.box(P[i] + n * (line * 0.8 + off + 0.5 * math.sin(i * 0.07 + off)), (3.2, w_, 0.01), a, tone, z0=0.06, flat=True)
        # dense tyre-mark strands across the whole road width
        for k in range(-6, 7):
            off = k * 1.3
            if abs(off) < hw - 1.0 and math.sin(i * 0.09 + k * 2.3) > -0.35:
                B.box(P[i] + n * (off + 0.6 * math.sin(i * 0.05 + k)), (3.2, 0.10 + 0.05 * ((k + 7) % 3), 0.01), a, 0.065 + 0.02 * ((k + 7) % 3), z0=0.065, flat=True)
        # edge lines + kerbs
        for s in (1, -1):
            B.box(P[i] + n * s * (hw - 0.35), (3.0, 0.22, 0.01), a, 0.60, z0=0.06, flat=True)
            B.box(P[i] + n * s * (hw + 0.45), (3.0, 0.9, 0.05), a, 0.62 if (i % 2) else 0.14, z0=0.0, flat=True)
        # rubber marbles/dirt patches off the line
        if i % 7 == 0:
            B.box(P[i] + n * rnd.choice([-1, 1]) * (hw - 1.5), (rnd.uniform(3, 7), rnd.uniform(1, 2.5), 0.01), a, 0.05, z0=0.06, flat=True)

    for side in (1, -1):
        # ---- fence posts + catch-fence rail
        for i in range(0, len(P)):
            t = tang(i); n = Vector((-t.y, t.x, 0)) * side; a = math.atan2(t.y, t.x)
            c = P[i] + n * (hw + 2.4)
            B.box(c, (0.12, 0.12, 4.0), a, 0.40)
            B.box(c, (3.05, 0.05, 0.12), a, 0.40, z0=3.9)
        # ---- advertising hoardings along the barrier
        i = 1
        while i < len(P) - 4:
            run = rnd.choice([2, 3, 3]); t = tang(i); n = Vector((-t.y, t.x, 0)) * side; a = math.atan2(t.y, t.x)
            mid = P[min(i + run // 2, len(P) - 1)]
            B.box(mid + n * (hw + 1.7), (run * 3.0, 0.12, 0.95), a, rnd.choice([0.62, 0.22, 0.50, 0.30, 0.70]), z0=0.55, flat=True)
            B.box(mid + n * (hw + 1.7), (run * 3.0, 0.5, 0.55), a, 0.30)   # concrete base
            i += run
        # ---- stands (tiered, crowd texture) with gaps, some with canopy
        i = 4
        while i < len(P) - 8:
            run = rnd.choice([8, 10, 12])
            seg = range(i, min(i + run, len(P) - 2))
            mid = P[seg[len(seg) // 2]]; t = tang(seg[len(seg) // 2]); n = Vector((-t.y, t.x, 0)) * side
            ang = math.atan2(t.y, t.x); length = len(seg) * 3.0
            if free(mid + n * (hw + 9.0), 7, seg[len(seg) // 2]):
                tiers = rnd.choice([5, 6, 7])
                for k in range(tiers):
                    c = mid + n * (hw + 5.0 + 0.95 * k + 0.5)
                    B.box(c, (length, 1.0, 0.6 * (k + 1)), ang, 0.40 + 0.04 * (k % 2), cls=CLS_CROWD)
                if rnd.random() < 0.6:
                    top = 0.6 * tiers + 2.8
                    c = mid + n * (hw + 5.0 + 0.95 * tiers * 0.5 + 0.5)
                    B.box(c, (length, 0.95 * tiers + 1.0, 0.35), ang, 0.46, z0=top)
                    for dx in (-length / 2 + 0.3, 0, length / 2 - 0.3):
                        B.box(c + t * dx + n * (0.95 * tiers * 0.5), (0.3, 0.3, top), ang, 0.38)
                occupied.append((mid.x + n.x * 8, mid.y + n.y * 8, 9))
            i += run + rnd.choice([1, 2])
        # ---- lamp poles
        for i in range(2, len(P), 10):
            t = tang(i); n = Vector((-t.y, t.x, 0)) * side; a = math.atan2(t.y, t.x)
            c = P[i] + n * (hw + 4.0)
            B.box(c, (0.25, 0.25, 11.0), a, 0.33)
            B.box(c - n * 1.2, (0.2, 2.6, 0.2), a + math.pi / 2, 0.33, z0=10.8)
    # ---- gantry bridges over the track (with sign boards)
    for frac in (0.30, 0.62, 0.86):
        i = int(len(P) * frac); t = tang(i); n = Vector((-t.y, t.x, 0)); a = math.atan2(t.y, t.x)
        for s in (1, -1): B.box(P[i] + n * s * (hw + 3.5), (1.2, 1.2, 8.5), a, 0.36)
        B.box(P[i], (2.0, 2 * (hw + 3.5) + 1.2, 1.4), a, 0.42, z0=7.5)
        B.box(P[i], (0.5, 2 * (hw + 3.5), 1.2), a, 0.30, z0=8.9)
        B.box(P[i] - t * 1.1, (0.2, 2 * (hw + 3.5) - 2, 1.5), a, 0.85, z0=7.5, flat=True)   # banner
    # ---- low-rise + skyscrapers (facade windows) with billboards/screens
    for layer, (dmin, dmax, hmin, hmax, wmin, wmax, tones) in enumerate((
            (32, 55, 14, 45, 18, 38, (0.24, 0.32, 0.40, 0.48)),
            (62, 110, 60, 150, 26, 55, (0.20, 0.28, 0.36, 0.46)),
            (115, 190, 110, 280, 34, 70, (0.22, 0.30, 0.38)))):
        for side in (1, -1):
            i = 0
            while i < len(P):
                t = tang(i); n = Vector((-t.y, t.x, 0)) * side
                off = hw + rnd.uniform(dmin, dmax); c = P[i] + n * off
                w = rnd.uniform(wmin, wmax); d = rnd.uniform(wmin, wmax); h = rnd.uniform(hmin, hmax)
                r = max(w, d) * 0.72
                if free(c, r, i):
                    ang = math.atan2(t.y, t.x) + rnd.choice([0, 0, 0.12, -0.12])
                    tone = rnd.choice(tones)
                    B.box(c, (w, d, h), ang, tone, cls=CLS_FACADE)
                    if layer > 0 and rnd.random() < 0.5:
                        B.box(c, (w * 0.6, d * 0.6, h * 0.12), ang, tone, z0=h, cls=CLS_FACADE)
                    if rnd.random() < 0.45:   # big billboard / LED screen facing the track
                        bw = min(w * 0.8, rnd.uniform(14, 30)); bh = bw * rnd.uniform(0.35, 0.6)
                        z0 = rnd.uniform(0.2, 0.6) * h
                        B.box(c - n * (d / 2 + 0.3), (bw, 0.5, bh), ang, 0.88, z0=z0, flat=True)
                    occupied.append((c.x, c.y, r))
                i += rnd.choice([2, 3, 4]) if layer == 0 else rnd.choice([3, 4, 5])
    ob = B.finish(); print("PROXY faces", len(ob.data.polygons))
    return ob


def build_track(scene, seed=7):
    """real-circuit look: alternating red/white kerbs, white edge lines, soft rubbered racing line. No buildings."""
    old = bpy.data.objects.get('PROXY_CITY')
    if old: bpy.data.objects.remove(old, do_unlink=True)
    rnd = random.Random(seed)
    P = _path(scene); hw = _halfwidth(P)
    B = Builder()
    for i in range(len(P)):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized(); n = Vector((-t.y, t.x, 0)); a = math.atan2(t.y, t.x)
        for s_ in (1, -1):
            for h, tone in ((-0.75, 0.80 if i % 2 else 0.16), (0.75, 0.16 if i % 2 else 0.80)):
                B.box(P[i] + n * s_ * (hw + 0.55) + t * h, (1.5, 1.2, 0.05), a, tone, z0=0.0, flat=True)
            B.box(P[i] + n * s_ * (hw - 0.3), (3.0, 0.25, 0.01), a, 0.75, z0=0.06, flat=True)
        line = 1.3 * math.sin(i * 0.045)
        B.box(P[i] + n * line, (3.2, 2.4, 0.01), a, 0.10, z0=0.05, flat=True)
    return B.finish()
