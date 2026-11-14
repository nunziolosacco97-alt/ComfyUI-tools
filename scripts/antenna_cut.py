# removes the thin nose antenna/pitot islands from the car mesh (in memory only) so it cannot flicker in the layout
import bpy, bmesh
_car = bpy.data.objects["f1_2026_sf26"]; _bm = bmesh.new(); _bm.from_mesh(_car.data); _bm.verts.ensure_lookup_table()
_seen = set(); _kill = []
for _v in _bm.verts:
    if _v.index in _seen: continue
    _st = [_v]; _comp = []; _seen.add(_v.index)
    while _st:
        _x = _st.pop(); _comp.append(_x)
        for _e in _x.link_edges:
            _o = _e.other_vert(_x)
            if _o.index not in _seen: _seen.add(_o.index); _st.append(_o)
    if len(_comp) > 60: continue
    _n = len(_comp); _cx = sum(v.co.x for v in _comp) / _n; _cy = sum(v.co.y for v in _comp) / _n; _cz = sum(v.co.z for v in _comp) / _n
    if abs(_cx) < 0.02 and 0.74 < _cy < 0.92 and 1.60 < _cz < 1.75: _kill += _comp
bmesh.ops.delete(_bm, geom=_kill, context="VERTS"); _bm.to_mesh(_car.data); _bm.free(); print("ANTENNA_CUT verts", len(_kill))
