import sys,os
from PIL import Image, ImageDraw
B=r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren"
R=B+r"\bench\results"
def sheet(kind,v,clay,out):
    ms=["zimage","flux","moss","ph3","h3"]
    ims=[("clay",Image.open(clay))]+[(m,Image.open(f"{R}\{kind}_{m}_{v}_s101_nf_0.png")) for m in ms]
    w,h=640,384; S=Image.new("RGB",(w*3,h*2))
    for i,(n,im) in enumerate(ims):
        im=im.convert("RGB").resize((w,h)); d=ImageDraw.Draw(im); d.rectangle([0,0,130,22],fill=(0,0,0)); d.text((6,5),n,fill=(255,255,255))
        S.paste(im,((i%3)*w,(i//3)*h))
    S.save(out)
os.makedirs(R+r"\FINALI_nf",exist_ok=True)
for v in "ABC": sheet("trk",v,B+rf"\mtn\inputs_v{v}\beauty_clay.png",R+rf"\FINALI_nf\sheet_McLaren_{v}.png")
for v in "1234": sheet("hum",v,B+rf"\mtn\hum_inputs_{v}\beauty_clay.png",R+rf"\FINALI_nf\sheet_Hummer_{v}.png")
