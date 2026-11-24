import bpy, sys, math
from mathutils import Vector, Euler
sc = bpy.context.scene; cam = sc.camera; dg = bpy.context.evaluated_depsgraph_get()
def ground(x, y):
    ok, loc, *_ = sc.ray_cast(dg, Vector((x, y, 500)), Vector((0, 0, -1)), distance=1000)
    return loc.z if ok else 0.0
CAMS = {"1_front34_low": (7.5, -8.0, 0.6, 40, (0.5, 0, 1.0), -2.0), "2_front_low": (10.5, -3.5, 0.45, 50, (0, 0, 1.05), 0.0),
        "3_rear34": (-7.0, -8.5, 1.3, 40, (0, 0, 1.0), 0.0), "4_side_long": (0.5, -13.0, 0.7, 85, (0, 0, 1.0), 0.0)}
sc.render.resolution_x, sc.render.resolution_y = 1280, 768
try: sc.eevee.taa_render_samples = 16
except Exception: pass
cam.data.shift_x = 0; cam.data.shift_y = 0
for n, (x, y, h, lens, aim, roll) in CAMS.items():
    cam.location = (x, y, ground(x, y) + h); cam.data.lens = lens
    q = (Vector(aim) - cam.location).to_track_quat('-Z', 'Y'); cam.rotation_euler = (q @ Euler((0, 0, math.radians(roll))).to_quaternion()).to_euler()
    sc.render.filepath = "C:/Users/Internet/Desktop/TEST COMFYUI/mclaren/mtn/hum_cam_" + n + ".png"; bpy.ops.render.render(write_still=True); print("OK", n)
