import bpy
o = bpy.data.objects["f1_2026_sf26"]; me = o.data
regs = {"frontwing": lambda c: c.z < -1.85, "rearwing": lambda c: c.z > 1.55, "halo": lambda c: -0.65 < c.z < -0.2 and c.y > 0.78, "body": lambda c: -1.85 <= c.z <= 1.55 and c.y < 0.78}
cnt = {}
for p in me.polygons:
    c = p.center
    for r, f in regs.items():
        if f(c): cnt.setdefault(r, {}); n = me.materials[p.material_index].name if me.materials[p.material_index] else "none"; cnt[r][n] = cnt[r].get(n, 0) + 1
for r, d in cnt.items(): print("REG", r, sorted(d.items(), key=lambda x: -x[1])[:8])
