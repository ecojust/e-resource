"""Build the relocated Shanghai Concert Hall's contemporary exterior."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
PROJECT = Path(os.environ['SHANGHAI_PROJECT']) if 'SHANGHAI_PROJECT' in os.environ else SOURCE.parents[3]
POSTAL = PROJECT / 'source/precise/hongkou-general-post-office/source'
sys.path[:0] = [str(POSTAL), str(POSTAL/'common')]
from photo_architecture import Builder, Facade, opening
from package_assets import metadata, record

PARAMS = json.loads((SOURCE/'parameters.json').read_text())
MODEL = PARAMS['id']
PLAN = PARAMS['footprint_uv_m']
COLORS = {
    'pale facing': {'color':[.66,.615,.517], 'roughness':.80},
    'buff brick': {'color':[.54,.421,.291], 'roughness':.87},
    'red tiles': {'color':[.37,.110,.070], 'roughness':.86},
    'stone steps': {'color':[.41,.386,.366], 'roughness':.88},
    'relief stone': {'color':[.735,.67,.535], 'roughness':.76},
}

def face(builder, edge, name):
    # Source ring is clockwise. Facade expects the interior to its left.
    return Facade(builder, PLAN[(edge+1)%len(PLAN)], PLAN[edge], name)

def row(width, number, span=.75):
    return [0.] if number==1 else np.linspace(-width*span/2,width*span/2,number).tolist()

def main_front(f, side, lod):
    """The historical northwest entrance and the opposite, newer southeast entrance."""
    old = side == 'old'
    zbase = 6.0
    w = f.length
    bays = row(w,3,.49)
    bw = w*.176
    win = [opening(x,6.5,bw,7.70,1.70,12 if lod else 28) for x in bays]
    doors = [opening(x,1.16,bw,3.36,.29 if old else 0,12 if lod else 20) for x in bays]
    top_centers=[x+d for x in bays for d in (-.66,.66)]
    top = [opening(x,17.18,1.03,1.14) for x in top_centers]
    h = 20.20 if old else 19.8
    f.wall(0,zbase,doors,material='pale facing')
    f.wall(zbase,h,win+top,material='pale facing')
    for a in doors: f.window(a,2,1 if lod else 2,glass='interior shadow',label='door panels')
    for a in win: f.window(a,2 if lod else 3,3 if lod else 5,glass='recessed glass',label='arched glazing')
    for a in top: f.window(a,1 if lod else 2,2,trim=False,label='attic lights')
    # Pilaster order and independent column plinth, capital and moulding profiles.
    for x in [(a+b)/2 for a,b in zip(bays,bays[1:])]+[bays[0]-.53*(bays[1]-bays[0]), bays[-1]+.53*(bays[1]-bays[0])]:
        pt=f.point(x,0,.14)
        f.builder.lathe(pt[:2],[(6.08,.33),(6.22,.40),(6.34,.38),(6.51,.29),
            (13.9,.256),(14.10,.32),(14.17,.43),(14.34,.42)],'carved pale stone',10 if lod else 20,f.label+'/column order')
        f.box(x,14.38,.95,.22,.90,.16,'relief stone','capital')
    if old:
        for x in bays:
            # Small triangular hood inside the lower part of each tall opening.
            ped=Polygon([(x-bw*.46,10.32),(x+bw*.46,10.32),(x,10.89)])
            f.prism(ped,-.20,-.02,'relief stone','window pediment')
            f.box(x,10.30,bw*.99,.14,.26,-.03,'carved pale stone','window hood')
            for j in range(1,5 if lod else 9):
                u=x-bw*.44+j*bw*.88/(5 if lod else 9)
                f.box(u,6.76,.085,.52,.18,.10,'relief stone','baluster')
            f.box(x,7.05,bw,.12,.35,.12,'carved pale stone','balcony rail')
        f.box(0,15.48,w*.72,1.18,.17,.035,'relief stone','frieze panel')
        for x in [-w*.424,w*.424]:
            panel=opening(x,6.36,1.12,2.25,.49,12 if lod else 24)
            f.prism(panel,-.035,.065,'limestone','shallow niche')
            f.prism(panel.buffer(.11).difference(panel),-.02,.13,'relief stone','niche moulding')
            f.box(x,3.38,2.12,3.0,.13,.07,'bronze window frame','poster frame')
            f.box(x,3.38,1.91,2.76,.045,.16,'limestone','unlettered display panel')
        # Stylized raised foliage only, no asserted reproduction of the figural relief.
        if not lod:
            for j in range(16):
                x=(j-7.5)*w*.041
                for dy in [-1,1]:
                    f.line((x-.30,15.44,.145),(x+.24,15.44+dy*.34,.145),.037,'carved pale stone',6,'frieze foliage')
    for z,m in [(5.89,.34),(14.48,.25),(16.6,.32),(h-.35,.42),(h+.03,.20)]:
        f.beam(z,.19,m)
    steps(f, w*.82, steps_count=7 if old else 6)

def steps(f,width,steps_count):
    depth=.38
    for i in range(steps_count):
        h=1.16*(i+1)/steps_count
        f.box(0,h/2,width,h,depth,depth*(steps_count-i-.5),'stone steps','stair tread')
    for x in [-width/2-.18,width/2+.18]:
        for i in range(steps_count):
            h=.29+1.16*(i+1)/steps_count
            f.box(x,h/2,.37,h,depth,depth*(steps_count-i-.5),'pale facing','stair cheek')

def flanking(f,height,lod,kind):
    w=f.length
    if w < 5.8:
        f.wall(0,height,[],material='pale facing')
    else:
        count=1 if w<10 else 2 if w<18 else 7
        xs=row(w,count,.78 if count>2 else .52)
        ground=[]; upper=[]
        if kind=='chamfer':
            ground=[opening(0,1.16,1.65,3.40)]
            upper=[opening(0,6.65,2.5,3.95,1.17,12 if lod else 24)]
            upper.extend(opening(x,6.65,1.03,2.75) for x in (-2,2))
            upper.extend(opening(x,12.5,1.15,2.52) for x in (-.86,.86))
            steps(f,w*.69,7)
        else:
            for x in xs:
                for dx in ([-.72,.72] if w>8 or count>1 else [0]):
                    ground.append(opening(x+dx,.96,.83,1.88))
                    upper.extend([opening(x+dx,7.04,.88,2.42),opening(x+dx,11.78,.88,2.14)])
        attic=[]
        for x in xs:
            for dx in [-.65,.65]:
                attic.append(opening(x+dx,height-2.35,.88,1.10))
        f.wall(0,5.9,ground,material='pale facing')
        f.wall(5.9,height,upper+attic,material='buff brick')
        for a in ground+upper+attic:
            f.window(a,1 if lod else 2,2 if lod else 3,trim=kind=='chamfer' and a in upper)
    for z in [5.77,height-2.67,height-.22]:
        f.beam(z,.22,.42)
    if not lod:
        for z in [1.9,2.66,3.42,4.18,4.94]:
            # Restrict scoring to opaque portions around actual openings below.
            line=box(-w/2,z-.018,w/2,z+.018)
            if w>=5.8: line=line.difference(unary_union(ground))
            f.prism(line,0,.014,'stone steps','rusticated joint')

def long_side(f,lod,visible):
    w=f.length
    if not visible:
        # West elevation is obscured in the reviewed photos. Only its slab and
        # plain wall with horizontal cornices are asserted by the roof outline.
        f.wall(0,16.1,[],material='buff brick')
        for z in [5.83,14.4,15.92]: f.beam(z,.21,.30)
        return
    xs=row(w,3,.22)
    arches=[opening(x,7.10,2.75,5.88,1.30,12 if lod else 22)for x in xs]
    misc=[]
    for x in [-w*.405,-w*.315,-w*.220,w*.220,w*.315,w*.405]:
        for z in [7.10,11.52]: misc.append(opening(x,z,1.13,2.25))
    ground=[opening(x,1.05,1.12,2.22) for x in row(w,11,.91)]
    attic=[opening(x,14.38,.87,1.05,.37,8 if lod else 16) for x in row(w,17,.91)]
    f.wall(0,5.9,ground,material='pale facing')
    f.wall(5.9,16.8,arches+misc+attic,material='buff brick')
    for a in ground+misc+attic:f.window(a,1 if lod else 2,2,trim=False)
    for a in arches:f.window(a,2,3 if lod else 5,label='east arched window')
    for z in [5.80,13.92,16.46,16.78]:f.beam(z,.19,.33)

def roof(builder,lod):
    plan=Polygon(PLAN)
    builder.plan_prism(plan,0,.20,'stone steps','Mass/base within owner')
    builder.plan_prism(plan,15.61,15.82,'roof zinc','Roof/continuous lower roof')
    # Ground plan follows the mapped block. Two entrance heads and the
    # central auditorium roof follow the material changes visible overhead.
    zones=[(box(-50,-5,4.15,8.1),20.20),(box(4.15,-5,45,8.1),19.2),
           (box(-50,8.1,45,55.1),16.78),(box(-50,55.1,45,70),18.45)]
    for poly,top in zones:
        wing=plan.intersection(poly)
        builder.plan_prism(wing,top-.23,top,'roof zinc','Roof/parapet coping')
        if top > 17.0:
            builder.plan_prism(wing.buffer(-.60,join_style=2),15.80,top-.23,'pale facing','Roof/step returns')
    central=plan.intersection(box(-16.1,56.6,3.66,70))
    builder.plan_prism(central.buffer(-.56,join_style=2),18.30,19.57,'pale facing','Roof/southeast attic return')
    builder.plan_prism(central,19.54,19.8,'roof zinc','Roof/southeast entrance head')
    # The long elevation in Shanghai_Concert_Hall.jpg shows a pale triangular
    # gable below the red longitudinal roof. The angle is an estimate.
    x0,x1,y0,y1=-17.45,13.6,8.5,41.2
    eave=16.86; ridge=21.55; mid=(x0+x1)/2
    triangle=Polygon([(x0,eave),(x1,eave),(mid,ridge)])
    for y in [y0,y1-.18]:
        builder.prism(triangle,-y-.18,-y,lambda x,z,d:(x,-d,z),'pale facing','Roof/end gables')
    for outer,side in [(x0,'east'),(x1,'west')]:
        # Each roof slope has an actual thickness and a closed eave edge.
        section=Polygon([(outer,eave),(mid,ridge),(mid,ridge+.105),(outer,eave+.105)])
        builder.prism(section,-y1-.12,-y0+.12,lambda x,z,d:(x,-d,z),'red tiles','Roof/'+side+' slope')
        if not lod:
            for frac in np.linspace(.035,.935,23):
                xx=outer+(mid-outer)*frac
                za=eave+(ridge-eave)*frac+.119
                builder.tube([(xx,y0,za),(xx,y1,za)],.036,'red brick',6,'Roof/tile courses')
    builder.tube([(mid,y0-.12,ridge+.11),(mid,y1+.12,ridge+.11)],.085,'red brick',8,'Roof/long ridge')
    # Low, rectilinear services to rear of red roof only; quantities estimated.
    for x in [-9,-3.7,1.6,6.9]:
        builder.box((x,48.7,17.18),(4.2,6.2,.72),'roof zinc',label='Roof/service curb')
        if not lod:
            for y in [46.75,48.05,49.35,50.65]:
                builder.box((x,y,17.58),(3.46,.17,.09),'interior shadow',label='Roof/service grilles')

def assemble(lod):
    b=Builder(COLORS)
    roof(b,lod)
    # The short jogs of the source polygon are real and kept separate.
    for i in range(len(PLAN)):
        f=face(b,i,f'Elevation-{i:02}')
        if i in [3,10]: main_front(f,'old' if i==3 else 'new',lod)
        elif i in [5,13]: long_side(f,lod,i==5)
        else:
            h=(20.2 if i in [4] else 19.2 if i in [0,1,2,14] else 18.45)
            flanking(f,h,lod,'chamfer' if i==4 else 'side')
    return b

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--gltfpack',default='gltfpack')
    ap.add_argument('--blender',default='blender')
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);args.audit.mkdir(parents=True,exist_ok=True)
    meta={'id':MODEL,'name':'迁建后的上海音乐厅（原南京大戏院）外部体量与入口','scope':'Exterior after relocation, with 2024 entrances, northeastern frontage and estimated auditorium roof. No interior or pre-move reconstruction.'}
    paths={}
    with tempfile.TemporaryDirectory() as directory:
        work=Path(directory)
        for lod in [False,True]:
            model=assemble(lod)
            raw=work/'low.glb' if lod else args.out/(MODEL+'-raw.glb')
            model.save(raw,meta)
            raw.with_suffix('.geometry.json').unlink(missing_ok=True)
            dest=args.out/(MODEL+('-lod.glb' if lod else '-web.glb'))
            subprocess.run([args.gltfpack,'-i',str(raw),'-o',str(dest),'-cc','-noq','-vnf','-km','-kn','-ke'],check=True)
            metadata(dest,raw)
            assert record(raw)['triangles']==record(dest)['triangles']
            paths['lod' if lod else 'full']=dest
            if not lod:
                paths['raw']=raw
                groups=defaultdict(lambda:{'v':[],'f':[],'materials':[],'face_materials':[]})
                for p in model.parts:
                    g=groups[p['label']];n=len(g['v']);g['v'].extend(p['vertices'])
                    g['f'] += [[n+i for i in t] for t in p['triangles']]
                    if p['material'] not in g['materials']:g['materials'].append(p['material'])
                    g['face_materials'] += [g['materials'].index(p['material'])]*len(p['triangles'])
                (work/'groups.json').write_text(json.dumps({'groups':groups,'palette':model.palette,'metadata':meta},separators=(',',':')))
        blend=args.out/(MODEL+'.blend');preview=args.audit/'model-preview.png'
        subprocess.run([args.blender,'-b','--threads','2','--python-exit-code','1','--python',str(SOURCE/'native.py'),'--',str(work/'groups.json'),str(blend),str(preview)],check=True)
        paths['native']=blend
    manifest={**meta,'model_id':MODEL,'status':'original-photo-informed-exterior','viewer_page':'concert-hall.html','audit_directory':'data/audit/concert-hall-v1/','model_scope_zh':'2003年平移后的上海音乐厅，西北主入口及倒角、东北侧拱窗、东南入口与简化屋顶。西南面、隐蔽部位和尺寸含估计。','coordinate_convention':'GLB local +X facade right, +Y up, +Z outward. Placement applies heading.','source_register':'source/precise/'+MODEL+'/reference-review.json','geometry_license':'Original architectural details and code: MIT. City footprint geometry derived from OpenStreetMap / Overture Maps under ODbL 1.0.','map_reference_license':'ODbL-1.0','photos_embedded':False,'interiors_modeled':False,'assets':{k:record(v)for k,v in paths.items()}}
    assert manifest['assets']['lod']['triangles']<manifest['assets']['full']['triangles']
    (args.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest['assets']))

if __name__=='__main__': main()
