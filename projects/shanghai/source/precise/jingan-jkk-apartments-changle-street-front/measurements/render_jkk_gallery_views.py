"""Make a two-view plate of the JKK street elevation and gallery construction."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parents[1] / "huangpu-yuanmingyuan-apartments-street-front/measurements"
sys.path.insert(0, str(RUNTIME))
from photo_glb_raster import raster


def font(size, bold=False):
    name = "Bold" if bold else "Regular"
    return ImageFont.truetype(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{name}.ttc",size,index=2)


def camera(eye, target, focal, center):
    forward = np.array(target, float) - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward,[0.,0.,1.])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    intrinsics = np.array([[focal,0,center[0]],[0,focal,center[1]],[0,0,1.]])
    return intrinsics @ np.stack((right,down,forward)) @ np.column_stack((np.eye(3),-eye))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def render(model, output, private_images=None):
    data = json.loads((HERE/"jkk-balcony-sections.json").read_text())
    view = data["camera_views"]["middle-stack-centre20"]
    sun = np.array([-.44,-.68,.64],np.float32)
    sun /= np.linalg.norm(sun)
    main = camera(np.array([7.4,-35.,8.4]), [7.3,0,8.7], 1040, (498,272))
    photos = data["camera_views"]
    with tempfile.TemporaryDirectory() as temp:
        libpath = Path(temp)/"paint.so"
        subprocess.run(["cc","-O2","-shared","-fPIC","-o",libpath,RUNTIME/"photo_glb_raster.c","-lm"],check=True)
        lib = ctypes.CDLL(str(libpath))
        lib.shadow_depth.restype = lib.paint.restype = None
        overall, overview_report = raster(model,lib,1120,main,[0,0,996,535],sun,[213,40])
        detail, detail_report = raster(model,lib,740,np.asarray(view["projection_matrix"]),[65,62,778,430],sun,[213,40])
        if private_images:
            for key in ("middle-stack-centre20", "middle-stack-west15"):
                record = photos[key]
                width,height = record["native_size_px"]
                img, _ = raster(model,lib,width,np.asarray(record["projection_matrix"]),[0,0,width,height],sun,[213,40])
                src = private_images / (key+".jpg")
                if digest(src) != record["study_frame_sha256"]:
                    raise ValueError(f"Changed study frame {key}")
                comparison = Image.new("RGB",(width*2,height))
                comparison.paste(Image.open(src),(0,0))
                comparison.paste(img,(width,0))
                comparison.thumbnail((1000,430))
                comparison.save(private_images/("working-comparison-"+key+".jpg"),quality=90)
    board = Image.new("RGB",(1420,780),"#f7f5ef")
    d = ImageDraw.Draw(board)
    d.text((28,18),"J.K.K.公寓　长乐路临街楼",font=font(35,True),fill="#33332f")
    d.text((29,73),"四列阳台分布在三层，中央两列在窄壁柱两侧收口。",font=font(21),fill="#514c41")
    board.paste(overall.resize((837,450),Image.Resampling.LANCZOS),(28,139))
    d.text((30,602),"临街立面",font=font(25,True),fill="#353730")
    d.text((30,647),"登记地址为长乐路962弄1至4号。此图展示弄口临街楼。",font=font(19),fill="#554d41")
    board.paste(detail.resize((503,260),Image.Resampling.LANCZOS),(892,139))
    d.text((893,423),"中层阳台的圆角",font=font(25,True),fill="#353730")
    d.multiline_text((893,473),"两张冬景照片分别量得约0.26米和0.31米。\n模型取0.28米。四道横槽在圆角处\n连续转向侧面。",font=font(19),spacing=8,fill="#514c41")
    d.text((892,618),"右图采用2020年2月街景的摄影投影。",font=font(16),fill="#695f52")
    d.line((28,708,1391,708),fill="#b5ad9f")
    d.text((29,730),"原创建模视图　·　墙面与进深按2015及2020年冬景估算。",font=font(17),fill="#635a4e")
    board.save(output,quality=92)
    report={"model":model.name,"mesh_sha256":digest(model),"board_sha256":digest(output),
            "section_measurement_sha256":digest(HERE/"jkk-balcony-sections.json"),"overview_projection":main.tolist(),
            "overview":overview_report,"detail_projection_source":"middle-stack-centre20","detail":detail_report,
            "external_image_reproduced":False}
    output.with_suffix(".json").write_text(json.dumps(report,ensure_ascii=False,indent=1)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--private-images",type=Path)
    args=parser.parse_args()
    render(args.model,args.output,args.private_images)
