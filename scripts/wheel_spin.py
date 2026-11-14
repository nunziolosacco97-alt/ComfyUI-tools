"""Wheel animation: spin about the REAL axle (PCA of the mesh, keeps camber) through the wheel centre + steering of the front wheels
from the path curvature (Ackermann: delta = atan(L*curvature))."""
import math, bpy, numpy as np
from mathutils import Matrix, Vector, Quaternion

NAMES = ("FL_Tire", "FR_Tire", "RL_Tire", "RR_Tire")


def _islands(o):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen = set(); isl = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); comp = []
        while st:
            x = st.pop(); comp.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        isl.append(comp)
    bm.free(); return isl


def _odd_axis(V):
    m = V.mean(0); w, e = np.linalg.eigh(np.cov((V - m).T))
    odd = max(range(3), key=lambda i: abs(w[i] - np.mean([w[j] for j in range(3) if j != i])))
    a = e[:, odd]; return (a if a[0] > 0 else -a), m


def _circle(V, a, frac):
    """outermost ring of a body of revolution: least-squares circle centre in the plane normal to a."""
    m = V.mean(0); d = V - m; rad = np.linalg.norm(d - np.outer(d @ a, a), axis=1)
    ring = V[rad > frac * rad.max()]
    u = np.cross(a, [0, 0, 1.0]); u = u / np.linalg.norm(u); t = np.cross(a, u)
    P = np.c_[ring @ u, ring @ t]
    sol = np.linalg.lstsq(np.c_[2 * P, np.ones(len(P))], (P ** 2).sum(1), rcond=None)[0]
    r = float(np.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2))
    return sol[0] * u + sol[1] * t + (ring @ a).mean() * a, r


def _axle_and_centre(o):
    """Axle/centre from tyre body + rim body (separate islands) so the rim does not wobble inside the tyre."""
    v = np.array([c.co[:] for c in o.data.vertices], dtype=float)
    isl = sorted(_islands(o), key=len)
    tyre = v[isl[-1]]; aT, _ = _odd_axis(tyre)
    cT, rT = _circle(tyre, aT, 0.985)
    rim = None
    for comp in reversed(isl[:-1]):
        if len(comp) < 300: continue
        V = v[comp]; aR, mR = _odd_axis(V)
        if abs(aR @ aT) > 0.99 and np.linalg.norm((mR - cT) - ((mR - cT) @ aT) * aT) < 0.03 and            np.linalg.norm((V - cT) - np.outer((V - cT) @ aT, aT), axis=1).max() < 0.26:
            rim = V; break
    if rim is None:
        a = aT; c = cT
    else:
        cR, _ = _circle(rim, aR, 0.9)
        a = aT + aR * (1 if aT @ aR > 0 else -1); a = a / np.linalg.norm(a)
        cm = (cT + cR) / 2; c = cm
        print("WHEEL_AXIS", o.name, "tyre-rim angle %.2f deg, centre gap %.1f mm" % (math.degrees(math.acos(min(1, abs(aT @ aR)))), np.linalg.norm((cT - cR) - ((cT - cR) @ a) * a) * 1000))
    if a[0] < 0: a = -a
    return Vector(a), Vector(c), rT


def _fcs(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves"): return list(act.fcurves)
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        cb = action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except Exception as ex:
        print("fcs err", ex); return []


def _clear(o):
    ad = o.animation_data
    for fc in _fcs(o):
        if fc.data_path in ("location", "rotation_euler", "rotation_quaternion"):
            try: fc.id_data.fcurves.remove(fc)
            except Exception:
                try: ad.action.layers[0].strips[0].channelbags[0].fcurves.remove(fc)
                except Exception as ex: print("rm err", ex)
    if "_base_loc" not in o: o["_base_loc"] = list(o.location)
    o.location = Vector(o["_base_loc"]); o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (1, 0, 0, 0)


def _gauss(v, sigma):
    n = len(v); k = int(sigma * 3); w = [math.exp(-(i * i) / (2 * sigma * sigma)) for i in range(-k, k + 1)]
    out = []
    for i in range(n):
        num = den = 0.0
        for j, wj in zip(range(i - k, i + k + 1), w):
            jj = min(max(j, 0), n - 1); num += v[jj] * wj; den += wj
        out.append(num / den)
    return out


def apply(scene, factor=1.0, steer=2.2):
    tires = [bpy.data.objects[n] for n in NAMES if n in bpy.data.objects]
    if not tires:
        print("WHEEL_SPIN: no tyres"); return
    for t in tires: _clear(t)
    geo = {t.name: _axle_and_centre(t) for t in tires}
    f0, f1 = scene.frame_start, scene.frame_end
    cen = {t.name: [] for t in tires}; aw0 = {}
    for f in range(f0, f1 + 2):
        scene.frame_set(f)
        for t in tires:
            cen[t.name].append(t.matrix_world @ geo[t.name][1])
            if f == f0: aw0[t.name] = (t.matrix_world.to_3x3() @ geo[t.name][0]).normalized()
    # wheelbase and heading from front/rear centres
    get = lambda n, i: cen[n][i]
    L = ((get("FL_Tire", 0) + get("FR_Tire", 0)) / 2 - (get("RL_Tire", 0) + get("RR_Tire", 0)) / 2).length
    n = f1 - f0 + 1
    psi = []
    for i in range(n + 1):
        d = (get("FL_Tire", i) + get("FR_Tire", i)) / 2 - (get("RL_Tire", i) + get("RR_Tire", i)) / 2
        psi.append(math.atan2(d.y, d.x))
    delta = []
    for i in range(n):
        j = min(i + 1, n); k = max(i - 0 if i < n else i, 0)
        dpsi = (psi[min(i + 1, n)] - psi[i] + math.pi) % (2 * math.pi) - math.pi
        ds = ((get("FL_Tire", min(i + 1, n)) + get("FR_Tire", min(i + 1, n))) / 2 - (get("FL_Tire", i) + get("FR_Tire", i)) / 2).length
        kap = dpsi / ds if ds > 1e-6 else 0.0
        delta.append(math.atan(L * kap))
    # light smoothing
    sm = _gauss(delta, 5.0)
    print("WHEEL_SPIN wheelbase %.2f  max steer %.1f deg" % (L, math.degrees(max(abs(x) for x in sm))))
    for t in tires:
        a, c, r = geo[t.name]
        front = t.name.startswith("F")
        ang = 0.0; p = cen[t.name]; prevq = None
        inc = _gauss([factor * (p[i + 1] - p[i]).length / r for i in range(n)], 3.0)
        fwd0 = p[1] - p[0]
        s = 1.0 if a.cross(Vector((0, 0, 1))).dot(t.matrix_world.to_3x3().inverted() @ fwd0 * 0 + (t.matrix_world.to_3x3() @ a).cross(Vector((0, 0, 1))) * 0) >= 0 else 1.0
        # sign: top of wheel must move along travel direction (world)
        aw = aw0[t.name]
        s = 1.0 if aw.cross(Vector((0, 0, 1))).dot(fwd0) > 0 else -1.0
        for i, f in enumerate(range(f0, f1 + 1)):
            R = Matrix.Rotation(s * ang, 4, a)
            if front: R = Matrix.Rotation(steer * sm[i], 4, "Z") @ R
            M = Matrix.Translation(c) @ R @ Matrix.Translation(-c)
            loc, q, _ = M.decompose()
            if prevq is not None and q.dot(prevq) < 0: q = Quaternion((-q.w, -q.x, -q.y, -q.z))
            prevq = q
            t.location = Vector(t["_base_loc"]) + loc; t.rotation_quaternion = q
            t.keyframe_insert("location", frame=f); t.keyframe_insert("rotation_quaternion", frame=f)
            ang += inc[i]
        for fc in _fcs(t):
            if fc.data_path in ("location", "rotation_quaternion"):
                for k in fc.keyframe_points: k.interpolation = "LINEAR"
        print("WHEEL_SPIN", t.name, "r=%.3f" % r, "axle(local)", tuple(round(x, 3) for x in a), "sign", s)
    scene.frame_set(f0)
