"""Shoot independently selected exterior-photo pixels through each glTF export."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PROJECT,METRIC,COLORS,WALL,BASE,CREAM,CAP,GLASS,BLUE,AMBER,DARK,IRON,PIPE,BROWN,STEEL,PALE
SerialScene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
SURVEY=json.loads((HERE/'registered-street-cameras.json').read_text())
SAMPLES={'p13': {'w': [(194, 310), (185, 372), (393, 270), (525, 375), (310, 256), (193, 407)], 'g': [(249, 383), (124, 378), (450, 385), (243, 243), (361, 237), (453, 224)], 'c': [(247, 422), (451, 423), (246, 273)], 'p': [(296, 274)], 'b': [(393, 475), (180, 459)]}, 'p14': {'w': [(320, 378), (162, 403), (312, 322)], 'g': [(252, 390), (252, 351), (475, 365), (98, 413), (145, 189)], 'c': [(245, 435), (102, 443)], 'f': [(126, 260), (254, 228)], 'i': [(171, 222)], 'p': [(355, 422)]}, 'j20': {'w': [(325, 218), (348, 263), (500, 160), (488, 284), (475, 348)], 'g': [(285, 199), (386, 207), (483, 214), (556, 345), (529, 116), (319, 70), (374, 84)], 'i': [(345, 107), (300, 97)], 'f': [(372, 124)], 'c': [(285, 233), (385, 240)]}, 'j18': {'w': [(335, 160), (340, 291), (423, 147), (423, 260), (361, 306)], 'g': [(313, 219), (311, 339), (308, 111), (398, 124), (401, 222), (442, 195)], 'c': [(315, 361)], 'b': [(347, 394)]}, 'p59': {'w': [(306, 241), (160, 270), (332, 129), (440, 195), (299, 340)], 'g': [(258, 183), (274, 70), (245, 334), (86, 233), (131, 112), (379, 265)], 'c': [(263, 206), (273, 90), (125, 127)], 'p': [(345, 265)]}}
SAMPLES.update({
 's3':{'g':[(190,269),(189,289),(457,259),(662,232),(666,67),(287,338),(283,322)],'w':[(222,280),(420,220),(601,214),(516,367),(154,366)],'c':[(187,303),(461,283)]},
 's5':{'g':[(433,260),(445,281),(543,331),(538,205),(676,281),(780,176),(802,290),(829,419),(442,447),(252,285)],'w':[(463,284),(511,372),(713,257),(742,353),(372,313),(685,204)],'c':[(436,298),(676,310)]},
 's11':{'g':[(218,295),(319,287),(364,284),(465,285),(507,309)],'w':[(346,269),(404,271),(489,293),(451,336)]}})
EXPECT={'w':[WALL],'g':[GLASS,BLUE,AMBER,DARK,STEEL,PALE,BROWN],'c':[CAP,CREAM],'p':[PIPE],'i':[IRON],'f':[CREAM,CAP],'b':[BASE]}
NAMES={'w':'raked stucco','g':'sash or glass','c':'stone sill','p':'rainwater pipe','i':'oriel ironwork','f':'oriel rendered spandrel','b':'street plinth'}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inspect(path):
    scene=SerialScene(path);rows=[];stats={}
    other=json.loads((HERE/'fenyang-wing-street-registration.json').read_bytes())
    cameras=dict(SURVEY['cameras'])
    for k,projection in other['registered_2020_station_projections'].items():
        cameras['s'+k]=projection
    for image,groups in SAMPLES.items():
        p=np.asarray(cameras[image]);A=np.linalg.inv(p[:,:3]);eye=-A@p[:,3]
        if not image.startswith('s'):eye*=METRIC['display_m_per_local_unit']
        def first(uv):
            direction=A@[*uv,1.];direction/=np.linalg.norm(direction);hit=scene.ray(eye,direction,100.)
            return hit['material']if hit else None
        outcomes=[]
        for k,pixels in groups.items():
            for uv in pixels:
                m=first(uv);r=0 if m in EXPECT[k] else None
                if r is None:
                    for radius in [1,2,4]:
                        if any(first(np.array(uv)+radius*np.array(off)) in EXPECT[k] for off in [(1,0),(-1,0),(0,1),(0,-1),(.707,.707),(-.707,.707),(.707,-.707),(-.707,-.707)]):
                            r=radius;break
                outcomes.append({'image':image,'pixel':uv,'observed':NAMES[k],'acceptable_materials':EXPECT[k],'first_hit':m,'within_radius_px':r})
        rows+=outcomes;stats[image]={'exact':sum(row['within_radius_px']==0 for row in outcomes),'within2':sum(row['within_radius_px'] is not None and row['within_radius_px']<=2 for row in outcomes),'total':len(outcomes)}
    return {'mesh_sha256':sha(path),'registered_readings':stats,'matched':sum(row['within_radius_px']==0 for row in rows),'total':len(rows),'rays':rows}
def render(path,out):
    """Render the original two repeating finishes from the embedded texture coordinates."""
    import ctypes
    import subprocess
    import tempfile
    from PIL import ImageFont
    helpers=PROJECT/'source/precise/jingan-jiaozhou-450-garden-residence/measurements'
    raster=runpy.run_path(str(helpers/'photo_glb_raster.py'))['raster']
    rows=[([36,-20,15],[10.2,7,5],45.7,'从太原路转入汾阳路'),([5.2,-9.8,7.9],[5.2,-.25,7.7],5.2,'凸窗下的阶折花铁'),([35,13.5,8],[12,12,4.5],34.5,'汾阳路阶折墙和折面窗湾')]
    fontpath=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    font=ImageFont.truetype(str(fontpath),20) if fontpath.exists() else ImageFont.load_default()
    board=Image.new('RGB',(900,1074),'#efece4');d=ImageDraw.Draw(board)
    with tempfile.TemporaryDirectory(dir=None) as td:
        so=Path(td)/'garden-raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',helpers/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        sun=np.asarray([.43,-.52,.73],dtype='float32');sun/=np.linalg.norm(sun)
        for i,(eye,target,size,label) in enumerate(rows):
            factor=METRIC['display_m_per_local_unit'];eye=np.array(eye,dtype=float)*factor;size*=factor;u=np.array(target)*factor-eye;distance=np.linalg.norm(u);u/=distance
            right=np.cross(u,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(u,right);f=1000.
            r=np.array([right*f,down*f,u]);P=np.c_[r,-r@eye];w=size*f/distance;h=w*330/900.
            img,receipt=raster(path,lib,1080,P,[-w/2,-h/2,w/2,h/2],sun,None)
            board.paste(img.resize((900,330),Image.Resampling.LANCZOS),(0,i*358))
            d.text((15,i*358+330),label,font=font,fill='#39372f')
    board.save(out,quality=91)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);p.add_argument('--board',type=Path);a=p.parse_args()
    d=inspect(a.mesh);a.out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(d['registered_readings'])
    if a.board:render(a.mesh,a.board)
