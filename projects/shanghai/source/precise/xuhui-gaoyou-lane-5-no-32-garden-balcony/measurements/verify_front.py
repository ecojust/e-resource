"""Shoot independently selected exterior-photo pixels through each glTF export."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PROJECT,COLORS,BRICK,RED,TIMBER,SOFFIT,STEEL,GLASS,GLASS2,SHADOW,IRON,CAP,EDGE,PIPE,DRAIN,FLOOR,JOINT
SerialScene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
SURVEY=json.loads((HERE/'garden-camera-survey.json').read_text())
SAMPLES={
 'memo06':{'b':[(53,259),(88,287),(146,241),(96,321),(751,338),(770,357),(474,288)],'g':[(191,260),(238,270),(282,281),(307,293),(197,306),(652,344),(690,359)],'h':[(211,235),(293,248),(663,311)],'c':[(47,144),(151,161),(296,192),(472,234),(567,249),(704,263),(808,283)],'u':[(87,174),(238,198),(453,258),(516,264),(750,286)],'w':[(460,314),(490,318)],'s':[(413,102),(647,197),(824,246)]},
 'memo59':{'b':[(517,69),(548,82),(557,46),(773,96),(758,124),(922,37)],'g':[(596,49),(610,66),(643,52),(672,70)],'w':[(816,50),(855,46)],'h':[(612,33),(673,26)],'c':[(474,16)],'p':[(755,63)],'i':[(837,69),(862,68)]},
 'stroll100':{'b':[(397,244),(457,253),(473,278),(724,291)],'g':[(519,231),(537,259),(568,224),(617,264)],'h':[(522,207),(627,195)],'u':[(343,178),(407,165),(579,147)],'c':[(338,135),(444,130),(560,118),(647,106)],'w':[(809,229),(864,211)],'i':[(829,300),(856,299)],'s':[(287,61),(487,54)]},
 'stroll101':{'b':[(432,330),(435,397),(652,276),(578,469),(559,496),(340,353)],'g':[(543,253),(582,247),(477,331),(526,350),(594,330),(480,400)],'h':[(499,238),(550,219)],'c':[(415,160),(479,136),(540,114)],'u':[(412,196),(458,177),(291,257)],'d':[(413,372),(412,465)],'i':[(335,414),(349,418)]},
 'stroll102':{'b':[(300,335),(313,385),(391,397),(548,392),(637,442),(671,455),(744,410)],'g':[(265,322),(259,358),(733,355),(729,365),(795,364)],'h':[(266,275)],'c':[(264,193),(298,156),(705,230),(781,260)],'u':[(262,227),(291,211),(753,271)],'d':[(352,379),(351,413)],'s':[(229,125),(410,140)]}}
EXPECT={'b':[BRICK],'g':[GLASS,GLASS2,STEEL],'h':[RED,JOINT],'c':[TIMBER,EDGE],'u':[SOFFIT],'w':[SHADOW,STEEL],'p':[CAP],'i':[IRON],'d':[PIPE,DRAIN],'s':[None]}
NAMES={'b':'facing brick','g':'steel window and glazing','h':'soldier head','c':'painted fascia or gutter rim','u':'soffit or canopy bracket','w':'shaded opening','p':'pier capping','i':'ornamental balcony iron','d':'downpipe','s':'sky'}
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inspect(path):
    scene=SerialScene(path);rows=[];stats={}
    for image,groups in SAMPLES.items():
        p=np.asarray(SURVEY['cameras'][image]['P']);A=np.linalg.inv(p[:,:3]);eye=-A@p[:,3]
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
    rows=[([14,-18,3.4],[3.92,2.2,.65],15.4,'花园面与右侧凸窗'),
          ([3.9,-6.6,.72],[3.23,-.18,.23],5.55,'砖墩、涡卷铁栏与檐下弧撑'),
          ([16,2.,2.7],[8.05,4.44,.42],9.4,'从花园转入侧面的两扇窄窗')]
    fontpath=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    font=ImageFont.truetype(str(fontpath),20) if fontpath.exists() else ImageFont.load_default()
    board=Image.new('RGB',(900,1074),'#efece4');d=ImageDraw.Draw(board)
    with tempfile.TemporaryDirectory(dir=None) as td:
        so=Path(td)/'garden-raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',helpers/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        sun=np.asarray([.43,-.52,.73],dtype='float32');sun/=np.linalg.norm(sun)
        for i,(eye,target,size,label) in enumerate(rows):
            eye=np.array(eye,dtype=float);u=np.array(target)-eye;distance=np.linalg.norm(u);u/=distance
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
