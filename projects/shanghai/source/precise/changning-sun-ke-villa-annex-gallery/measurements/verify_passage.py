"""Inspect the open portal from the sign-side photograph and render both source perspectives."""
from pathlib import Path
import argparse
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from gallery_cameras import CROPS
from fit_gallery import GalleryPlane
from review_gallery import test_mesh,render,CHECKS
HERE=Path(__file__).resolve().parent
SIGN_POINTS={
    'scalloped warm render':[(952,279),(966,297),(995,322),(941,339),(1038,329),(1044,356),(1018,409)],
    'fired barrel tile':[(982,240),(999,229),(1020,220),(1040,224),(1051,213)],
    'charcoal rainwater metal':[(1028,313),(1026,361),(1025,411),(1024,438)],
    'smoked window glass':[(1054,386),(1054,401)],
    'through opening':[(910,382),(918,387),(927,391)],
    'warm inset circle':[(957,381),(972,381),(995,382),(958,397),(974,397),(993,400)]}
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path);cli.add_argument('--render',action='store_true')
    a=cli.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    front=GalleryPlane().matrix
    side=np.array(json.loads((HERE/'passage-station.json').read_bytes())['projection'])
    result={'gallery':test_mesh(a.mesh,front,CHECKS),'passage':test_mesh(a.mesh,side,SIGN_POINTS),'round_detail_count':6,'note':'Six round-detail centres were used to construct their position on the passage sidewall and are listed separately from the 21 independent material and aperture checks.'}
    if a.render:
        thumb=[]
        for key,matrix,title in [('gallery',front,'三券与七跨木廊'),('passage',side,'园口方门与错台瓦顶')]:
            target=a.out/(key+'-model.jpg')
            result[key]['render']=render(a.mesh,target,matrix,CROPS[key][0]);im=Image.open(target)
            im.thumbnail((690,340) if key=='gallery'else(260,340))
            thumb.append((title,im.copy()))
        canvas=Image.new('RGB',(974,396),'#eae7df');d=ImageDraw.Draw(canvas)
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',18,index=2)
        for x,(title,im)in zip((8,706),thumb):
            canvas.paste(im,(x,8+(340-im.height)//2));d.text((x+4,354),title,font=font,fill='#302d29')
        canvas.save(a.out/'registered-gallery.jpg',quality=94,subsampling=0)
    (a.out/(a.mesh.stem+'-dual-view.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for key,j in result.items():
        if isinstance(j,dict):print(key,j['direct'],j['count'],[(p['uv'],p['from_photo'],p['first_hit'])for p in j['points']if not p['matched']])
if __name__=='__main__':main()
