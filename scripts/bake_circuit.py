"""Bake the real-circuit environment + the camera framing + motion blur into a .blend so it can be opened and checked in Blender.
usage: blender -b blender/Test_anim_city.blend --python scripts/bake_circuit.py -- <out.blend>"""
import sys, os, math
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[sys.argv.index("--") + 1]
scene = bpy.context.scene
# DEDUP: remove objects already baked into the blend so they are not built twice
for _n in ("CIRCUIT_ENV", "VISOR"):
    _o = bpy.data.objects.get(_n)
    if _o: bpy.data.objects.remove(_o, do_unlink=True)
import circuit_env
ob = circuit_env.build(scene)          # removes the old PROXY_CITY, hides the old road, builds the circuit
ob.name = "CIRCUIT_ENV"
road = bpy.data.objects.get("NurbsPath.001")
if road: road.hide_viewport = True
scene.camera.delta_rotation_euler.x = math.radians(8.0)
scene.camera.data.shift_y = -0.09
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.5
h = bpy.data.objects.get("Sphere")
if h:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12)
    v = bpy.context.active_object; v.name = "VISOR"; v.parent = bpy.data.objects["f1_2026_sf26"]
    v.location = (-0.009, 0.846 + 0.012, -0.033 - 0.13); v.scale = (0.100, 0.040, 0.050)
    m = bpy.data.materials.new("VISOR"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1); v.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out)
