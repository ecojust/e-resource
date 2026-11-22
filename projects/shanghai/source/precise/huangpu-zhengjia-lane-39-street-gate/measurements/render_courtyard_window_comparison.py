"""Compare the original CC photograph with the textured GLB in the original camera."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/"huangpu-yuanmingyuan-apartments-street-front/measurements"
sys.path[:0]=[str(HERE.parent/"source"),str(RASTER)]
from courtyard_photo_plane import MATRIX
from courtyard_windows import PICKS
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane


def font(size,bold=False):
    f="NotoSansCJK-"+("Bold" if bold else "Regular")+".ttc"
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/"+f,size,index=2)


def draw_board(model,photo,dest,transform=None):
    local_to_gate = np.eye(4) if transform is None else np.array(
        json.loads(transform.read_text())["matrix"], dtype=float)
    if local_to_gate.shape != (4, 4):
        raise ValueError("Expected a four by four end-house to gate matrix")
    projection = MATRIX @ np.linalg.inv(local_to_gate)

    assert hashlib.sha256(photo.read_bytes()).hexdigest()==PICKS["image_sha256"]
    image=ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    # The facade's three storeys and five short canopies fit the same crop.
    crop=(450,1940,2270,3690)
    board=Image.new("RGB",(1500,930),"#f6f3ec")
    ink=ImageDraw.Draw(board)
    ink.text((35,18),"永嘉路39弄郑家衖　院内住宅窗扇与短雨篷",font=font(34,True),fill="#352f2b")
    ink.text((35,78),"2015年9月9日　Antigng 摄影",font=font(20),fill="#665846")
    ink.text((770,78),"重建窗件　同机位投影",font=font(20),fill="#665846")
    im=image.crop(crop);im.thumbnail((695,700),Image.Resampling.LANCZOS)
    board.paste(im,(35,120))
    sun=np.array([-.52,-.47,.71],np.float32);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as temp:
        lib=Path(temp)/"r.so"
        subprocess.run(["cc","-O2","-shared","-fPIC","-o",lib,RASTER/"photo_glb_raster.c","-lm"],check=True)
        dll=ctypes.CDLL(str(lib));dll.shadow_depth.restype=dll.paint.restype=None
        visible = model
        clipped = None
        if transform is not None:
            visible = Path(temp)/"visible.glb"
            clipped = clip_near_plane(model,visible,projection)
        light = np.ascontiguousarray(local_to_gate[:3,:3] @ sun,dtype="float32")
        render,data=raster(visible,dll,900,projection,crop,light,[225,28])
    render.thumbnail((695,700),Image.Resampling.LANCZOS)
    board.paste(render,(770,120))
    ink.text((35,810),"三层左窗的两扇百叶向外打开。中窗左半露出三格玻璃，右窗百叶间仍有局部开缝。",font=font(21),fill="#3f372f")
    ink.text((35,865),"照片裁剪自 Wikimedia Commons《郑家弄.jpg》，署名 Antigng，CC BY-SA 4.0。本对照图按相同许可发布。",font=font(17),fill="#665846")
    board.save(dest,quality=92)
    rec={"photograph":PICKS["source"],"credit":"Antigng","license":"https://creativecommons.org/licenses/by-sa/4.0/",
         "image_sha256":PICKS["image_sha256"],"change_to_photo":"EXIF orientation, rectangular crop and resizing",
         "model_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),"crop_oriented_pixels":crop,"render":data,
         "board_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    if transform is not None:
        rec["near_clipping"] = clipped
        rec["local_to_gate"] = local_to_gate.tolist()
        rec["transform_sha256"] = hashlib.sha256(transform.read_bytes()).hexdigest()
    dest.with_suffix(".json").write_text(json.dumps(rec,indent=2,ensure_ascii=False)+"\n")


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    for arg in ("model","photo","output"):cli.add_argument(arg,type=Path)
    cli.add_argument("--transform", type=Path, help="End-house to entrance coordinate JSON for a whole-building GLB")
    a=cli.parse_args();draw_board(a.model,a.photo,a.output,a.transform)
