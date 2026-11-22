"""Draw the courtyard portals and their carved heads directly from a delivered GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),
              str(HERE.parents[1]/'jingan-jkk-apartments-changle-street-front/measurements')]
from glb_triangles import load_triangles,material_appearance
from render_central_steel_views import draw_mesh

def draw(asset,out):
    data=json.loads((HERE/'paired-door-photographs.json').read_bytes())
    tris,ids,names,signature=load_triangles(asset)
    originals=material_appearance(asset)['materials']
    rgba=np.array([originals[n]['baseColorFactor']for n in names]);blend=np.array([originals[n].get('alphaMode')=='BLEND' for n in names])
    keep=np.isin(ids,[i for i,n in enumerate(names)if n.startswith('Courtyard door | ')])
    def scene(mask,key,size):
        return draw_mesh((tris[mask],ids[mask],rgba,blend),np.array(data['cameras'][key]),{},size,'all')
    passage_names={'Wujin courtyard | warm plaster in recess','Wujin courtyard | grey interior floor','Wujin courtyard | unlit enclosed doorway','Wujin courtyard | dark interior framing'}
    passage=np.isin(ids,[i for i,n in enumerate(names)if n in passage_names]);full,view=scene(keep|passage,'4',(740,710))
    centre=tris.mean(axis=1)
    above=keep&(centre[:,0]<1.5)&(centre[:,2]>4.24)
    carving,detail=scene(above,'8',(430,310))
    paint='#2f3835';pad='#fcf9f2';board=Image.new('RGB',(1300,1000),pad);pen=ImageDraw.Draw(board)
    def title(x,y,text,size,bold=False,color=paint):
        f='Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+f+'.ttc',size,index=2)
        pen.text((x,y),text,font=font,fill=color)
    title(45,30,'武进路225弄院内的两座券门',41,True)
    title(47,94,'9号与11号　｜　依据2015年7月19日原照绘制的模型投影',23)
    pen.line((44,151,1255,151),fill='#a4aaa3',width=2)
    board.paste(full,(32,179));board.paste(carving,(818,192))
    title(824,504,'9号门额与半圆盲券',23,True)
    strings=['红色砖券罩住砌实的半圆面。','下方小花额与门楣分别出挑。','9号气窗留四片深色玻璃，','11号外侧两格可见横条。','2012年照片中9号券仍呈红色，','2015年两扇门的下部已刷白。']
    for i,t in enumerate(strings):title(824,559+i*41,t,21)
    title(44,915,'门牌依原照由左至右为9、11。右门可见门后的灰墙及地坪，卷草山墙另有局部图。',20)
    title(44,954,'测绘参照　高参88，2012年12月及2015年7月。图中仅使用模型几何和材质。',16,color='#5b675e')
    out.parent.mkdir(exist_ok=True,parents=True);board.save(out,quality=90,subsampling=0)
    result=dict(mesh_sha256=signature,model_photo_plate=out.name,plate_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
                photo_pixels_included=False,triangles_drawn=int(keep.sum()),portal_projection=view,carved_head_projection=detail)
    out.with_suffix('.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('asset',type=Path);parser.add_argument('board',type=Path);args=parser.parse_args();print(draw(args.asset,args.board)['plate_sha256'])
