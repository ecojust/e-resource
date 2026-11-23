"""Produce a same-station comparison from two independently rendered courtyard meshes."""
from pathlib import Path
from argparse import ArgumentParser
import hashlib,json
from PIL import Image,ImageDraw,ImageFont

CROPS=[
    ("2013",(87,546,205,665),"绿色1230号牌与红色墙箱","Number plate and wall cabinet"),
    ("2013",(125,149,407,352),"入口东侧二楼钢窗的四道分格","Four window lights east of the entrance"),
    ("2016",(238,302,640,480),"院内地层窗外防护笼、外机及旧窗","Ground-floor guards, outdoor units and the windows behind"),
]
SIZE={"2013":(1247,885),"2016":(650,487)}
def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def draw_comparison(first,revised,out):
    out.mkdir(parents=True,exist_ok=True)
    cjk=Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
    def font(size):
        return ImageFont.truetype(str(cjk),size,index=2) if cjk.exists() else ImageFont.load_default(size=size)
    canvas=Image.new("RGB",(1000,882),"#f2f0ea")
    draw=ImageDraw.Draw(canvas)
    draw.text((19,6),"淮海中路1230号院内立面" if cjk.exists() else "1230 Middle Huaihai Road",font=font(25),fill="#2c302f")
    titles=("初稿","修订稿") if cjk.exists() else ("First mesh","Revised mesh")
    for i,title in enumerate(titles):
        draw.text((26+i*494,44),title,font=font(19),fill="#424947")
    records=[]
    for j,(year,rect,zh,en) in enumerate(CROPS):
        row_y=79+j*261
        draw.text((17,row_y),f"{year} · {zh if cjk.exists() else en}",font=font(16),fill="#313836")
        step={"camera_year":year,"native_photo_xyxy":rect,"frames":[]}
        for i,folder in enumerate((first,revised)):
            p=folder/f"view-{year}.jpg"
            with Image.open(p) as full:
                sx,sy=full.width/SIZE[year][0],full.height/SIZE[year][1]
                box=[round(edge*(sx if k%2==0 else sy))for k,edge in enumerate(rect)]
                tile=full.crop(box).convert("RGB")
            factor=min(470/tile.width,216/tile.height)
            tile=tile.resize((round(tile.width*factor),round(tile.height*factor)),Image.Resampling.LANCZOS)
            canvas.paste(tile,(12+i*495+(475-tile.width)//2,row_y+29+(216-tile.height)//2))
            step["frames"].append({"file":p.name,"sha256":digest(p),"rendered_crop":box})
        records.append(step)
    label="2013年机位源自高参88。2016年机位源自中国の風景。图中像素均由模型生成。" if cjk.exists() else "Model renders from the camera stations of Gao88 (2013) and masa3594 (2016)."
    draw.text((17,853),label,font=font(13),fill="#464c49")
    dest=out/"revision-comparison.jpg"
    canvas.save(dest,quality=95,subsampling=0,optimize=True)
    (out/"revision-comparison.json").write_text(json.dumps({
        "image":dest.name,"sha256":digest(dest),"source":"Images are model-only renders, no source photograph pixels.",
        "rows":records},ensure_ascii=False,indent=2)+"\n")

if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    p.add_argument("first",type=Path); p.add_argument("revised",type=Path); p.add_argument("output",type=Path)
    a=p.parse_args();draw_comparison(a.first,a.revised,a.output)
