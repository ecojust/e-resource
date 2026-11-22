"""Render the real GLB from the two registered camera projections; photo pixels are never read."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parents[1]/'jingan-jkk-apartments-changle-street-front/measurements')]
from glb_triangles import load_triangles,material_appearance
from render_central_steel_views import draw_mesh

def render(asset,out):
    tris,ids,names,sign=load_triangles(asset);materials=material_appearance(asset)['materials']
    rgba=np.array([materials[n]['baseColorFactor'] for n in names]);blend=np.full(len(names),False)
    views=json.loads((HERE/'gate-camera-fit.json').read_text())['views'];evidence=[]
    board=Image.new('RGB',(1380,860),'#f4f0e7');d=ImageDraw.Draw(board)
    def text(x,y,t,size,color='#223431'):
        font=ImageFont.truetype('NotoSerifCJK-Regular.ttc',size,index=2);d.text((x,y),t,font=font,fill=color)
    text(35,20,'长春路319号院门',39);text(36,80,'四片斜页、五字门扇与双砖柱',23)
    for j,(v,label)in enumerate(zip(views,['2023年街前近照机位','2021年开馆日斜照机位'])):
        im,metrics=draw_mesh((tris,ids,rgba,blend),np.array(v['P']),{},(655,530),'all')
        x=32+677*j;board.paste(im,(x,135));text(x,665,label,22);evidence.append(metrics)
    text(35,734,'双门在两幅模型图中均按2023年照片闭合。2021年9月25日拍摄时，两扇门向院内敞开。',21)
    text(35,785,'两柱按28皮砖、每皮暂取64毫米换算；五字用思源宋体繁体字形重排，细小碑文保留原照参考。',18,'#53635d')
    out.parent.mkdir(exist_ok=True,parents=True);board.save(out,quality=91,subsampling=0)
    out.with_suffix('.json').write_text(json.dumps(dict(asset_sha256=sign,plate_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),photo_pixels_included=False,views=evidence),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('asset',type=Path);p.add_argument('output',type=Path);a=p.parse_args();render(a.asset,a.output)
