"""Cast the dated photo sample rays against the actual exported glTF triangles."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PROJECT,COLORS,RENDER,BRICK,CAP,STONE,GLASS,GLASS2,SASH,IRON,GLYPH,INTERIOR,SHADOW,TILE,DARK
from register_front import P
SerialScene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
M=json.loads((HERE/'two-dates-feature-registration.json').read_bytes())['recorded_sets']
# Rectified FOTO tracing coordinates (790x675 preview). No source image is shipped.
SAMPLES={
 'front_roughcast':([(367,149),(375,120),(432,133),(359,215),(444,271),(371,259),(369,321),(445,344),(377,396),(381,462)],{RENDER}),
 'brick_steps':([(381,85),(394,76),(412,79),(428,87),(357,103)],{BRICK}),
 'crest':([(394,120),(406,111),(416,118),(406,134)],{GLYPH,STONE}),
 'raking_cornice':([(345,88),(366,76),(394,54),(423,61),(449,78)],{CAP,STONE}),
 'shaft_glazing':([(400,204),(405,218),(411,236),(404,329),(411,350),(409,446),(411,572)],{SASH,GLASS,GLASS2}),
 'recessed_arched_head':([(390,187),(401,174),(418,190)],{STONE,CAP}),
 'red_window_diamond':([(407,182),(405,184)],{BRICK}),
 'upper_strip':([(184,180),(215,178),(254,174),(282,180),(317,171),(498,172),(538,170),(575,170),(612,162)],{SASH,GLASS,GLASS2}),
 'front_slab_or_parapet':([(153,345),(175,346),(272,347),(302,346),(477,339),(517,342),(623,339),(650,339),(165,462),(275,461),(587,456),(623,456),(183,580),(515,581)],{CAP,STONE}),
 'retreated_portico':([(200,274),(239,288),(290,268),(484,266),(539,272),(604,263),(180,397),(306,389),(497,394)],{INTERIOR,STONE,GLASS,GLASS2,SASH}),
 'hollow_tile_eave':([(154,214),(201,213),(250,212),(307,210),(486,205),(517,204),(566,204),(631,204)],{TILE,DARK,CAP,STONE})}
# Independently read from the 650x487 March 2016 close-up.
CANON={
 'front_roughcast':([(170,277),(281,201),(307,183),(281,254),(302,247),(159,345),(292,379)],{RENDER}),
 'brick_steps':([(174,211),(205,171),(237,134),(281,130)],{BRICK}),
 'raking_cornice':([(157,200),(199,153),(249,91),(287,90),(317,92)],{CAP,STONE}),
 'crest':([(227,194),(247,181),(252,176),(230,214)],{GLYPH,STONE}),
 'red_window_diamond':([(231,290),(237,287)],{BRICK}),
 'recessed_arched_head':([(214,290),(220,279),(242,269),(255,280)],{STONE,CAP}),
 'shaft_glazing':([(194,349),(204,370),(216,348),(235,331),(241,367)],{GLASS,GLASS2,SASH}),
 'clear_sky':([(172,165),(210,104),(238,78)],{None})}
def sha(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def mapped(matrix,u,v):
    q=matrix@[u,v,1.];return q[:2]/q[2]
RECT=np.array([[1/40,0,-406/40],[0,-1/40,599/40],[0,0,1]])
def records():
    output=[]
    for tag,data,cam,uv in [('gao02',SAMPLES,P,P[:,[0,2,3]]@RECT),('jp27',CANON,np.linalg.inv(M['jp27-gable']['H'])@P,np.eye(3))]:
        for group,(points,expected) in data.items():
            for u,v in points:
                pixel=mapped(uv,u,v)
                yield tag,group,pixel,expected,cam
def sample(scene,eye,inv,pixel):
    direction=inv@[*pixel,1.]
    direction/=np.linalg.norm(direction)
    if direction[1]<0:direction=-direction
    hit=scene.ray(eye,direction,70.);return hit['material']if hit else None
def inspect(path):
    scene=SerialScene(path);out=[]
    for tag,g,px,expected,cam in records():
        eye=np.linalg.solve(cam[:,:3],-cam[:,3]);inv=np.linalg.inv(cam[:,:3]);actual=sample(scene,eye,inv,px);radius=0 if actual in expected else None
        if radius is None:
            for delta in (1,2,3,5):
                if any(sample(scene,eye,inv,px+off) in expected for off in np.array([(1,0),(0,1),(-1,0),(0,-1),(.707,.707),(-.707,.707),(.707,-.707),(-.707,-.707)])*delta):
                    radius=delta;break
        out.append({'image':tag,'observed':g,'image_uv':np.round(px,2).tolist(),'expected':sorted(k or 'sky'for k in expected),'first_hit':actual,'radius_px':radius})
    result={}
    for tag in ('gao02','jp27'):
        q=[r for r in out if r['image']==tag];result[tag]={'exact':sum(r['radius_px']==0 for r in q),'within_2px':sum(r['radius_px']is not None and r['radius_px']<=2 for r in q),'total':len(q)}
    return {'mesh_sha256':sha(path),'registered_readings':result,'matched':sum(r['radius_px']==0 for r in out),'total':len(out),'rays':out,
      'camera_use':'The independent March gable close-up is transferred through its own façade homography. Depth off that plane has greater uncertainty. All first materials and misses are retained.'}
def render(path,out):
    scene=SerialScene(path);w,h=860,680
    target=np.array([.1,.15,6.47]);eye=np.array([9.0,-28,9.5]);direction=target-eye;direction/=np.linalg.norm(direction)
    right=np.cross(direction,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,direction)
    v=scene.tri-target;uv=np.empty((*v.shape[:2],2));uv[:,:,0]=w/2+(v@right)*42.;uv[:,:,1]=h/2-(v@up)*42.
    depths=(v@direction).mean(axis=1)
    norms=np.cross(scene.tri[:,1]-scene.tri[:,0],scene.tri[:,2]-scene.tri[:,0]);norms/=np.linalg.norm(norms,axis=1)[:,None]
    sun=np.array([-.28,-.75,.60]);sun/=np.linalg.norm(sun)
    img=Image.new('RGB',(w,h),(233,231,221));draw=ImageDraw.Draw(img)
    for i in np.argsort(-depths):
        fac=.78+.26*max(0.,norms[i]@sun);mat=scene.materials[scene.mi[i]]
        draw.polygon([tuple(v)for v in uv[i]],fill=tuple(round(c*fac)for c in COLORS[mat]))
    img.save(out,quality=91)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('json',type=Path);a=ap.parse_args()
    r=inspect(a.mesh);a.json.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(r['registered_readings'])
