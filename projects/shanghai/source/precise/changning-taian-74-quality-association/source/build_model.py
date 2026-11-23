"""Build the measured street-facing pediment and recessed casements at the east side of the Yicun lane entrance."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
import entrance

ID = 'changning-taian-74-quality-association'
META = dict(id=ID, name='泰安路74号上海市质量协会临街面', address='上海市长宁区泰安路74号（76弄口东侧）',
            neighbouring_register='3M006', neighbouring_site='亦村', geometry_license='MIT', photos_embedded=False,
            scope='泰安路74号机构楼沿街一面。其西邻为76弄亦村入口，受保护的院内住宅另行建模。',
            viewer_page='taian-74-quality-association.html')
WALL='scored pale render'
TRIM='off-white cast moulding'
DARK='painted metal joinery'
GLASS='cool recessed glass'
GRILLE='charcoal metal apron'
STONE='grey plinth and shadow mould'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [
    (WALL,[.70,.699,.664],.9),(TRIM,[.82,.81,.758],.78),(DARK,[.086,.095,.090],.52),
    (GLASS,[.117,.173,.201],.28),(GRILLE,[.075,.075,.068],.72),(STONE,[.42,.421,.394],.87)]}
REG=json.loads((HERE/'registered-front.json').read_bytes())
H=np.asarray(REG['image_to_front_xz'])
PIX=json.loads((HERE/'front-features.json').read_bytes())['features']

def surface_point(px):
    q=H@[*px,1.]
    return q[:2]/q[2]

def traced(name):
    return Polygon([surface_point(p) for p in PIX[name]])

def build(lod=False):
    scene=Builder(PALETTE)
    def face(shape,back,front,material,label):
        scene.prism(shape,back,front,lambda x,z,d:(x,-d,z),material,label)
    def fascia(x0,x1,zmin,zmax,depth,material,name):
        scene.box(((x0+x1)/2,-depth/2,(zmin+zmax)/2),(x1-x0,depth,zmax-zmin),material,label=name)
    openings={name:traced(name) for name in PIX if name.startswith(('lower-','upper-')) and len(PIX[name])==4}
    width=REG['control_xz_m'][1][0]
    wall=box(-.32,4.23,width+.20,12.52).difference(unary_union(list(openings.values())))
    face(wall,-.42,-.01,WALL,'street facade/wall and six window reveals')
    # The scoring is cut by all real openings. Shallow joints are separate from the casement surrounds.
    for i,z in enumerate(np.arange(4.55,12.39,.354)):
        shape=wall.intersection(box(-.28,z,width+.16,z+.012))
        face(shape,-.008,.0001,STONE,f'facade scoring/horizontal bed {i+1:02}')
    for name,op in openings.items():
        x0,z0,x1,z1=op.bounds
        ring=op.buffer(.112,join_style='mitre').difference(op)
        face(ring,-.11,.108,TRIM,name+'/projecting four-sided surround')
        frame=op.difference(op.buffer(-.068,join_style='mitre'))
        face(frame,-.209,-.085,DARK,name+'/rebated frame')
        inside=op.buffer(-.070,join_style='mitre')
        cols=[0,.211,.749,1] if 'center' in name else [0,.322,.672,1]
        rows=[0,.192,.78,1] if 'center' in name else [0,.195,.80,1]
        x0,z0,x1,z1=inside.bounds
        for i,t in enumerate(cols[1:-1]):
            x=x0+(x1-x0)*t
            face(inside.intersection(box(x-.026,z0-.01,x+.026,z1+.01)),-.192,-.121,DARK,f'{name}/mullion {i+1}')
        for i,t in enumerate(rows[1:-1]):
            z=z0+(z1-z0)*t
            face(inside.intersection(box(x0-.01,z-.023,x1+.01,z+.023)),-.204,-.137,DARK,f'{name}/transom {i+1}')
        for i,(ta,tb) in enumerate(zip(cols,cols[1:])):
            for j,(va,vb) in enumerate(zip(rows,rows[1:])):
                left=x0+(x1-x0)*ta+(.028 if ta else -.002)
                right=x0+(x1-x0)*tb-(.028 if tb<1 else -.002)
                bottom=z0+(z1-z0)*va+(.025 if va else -.002)
                top=z0+(z1-z0)*vb-(.025 if vb<1 else -.002)
                pane=inside.intersection(box(left,bottom,right,top))
                face(pane,-.246,-.222,GLASS,f'{name}/glazing {i+1}-{j+1}')
        fascia(x0-.15,x1+.15,z0-.15,z0-.055,.180,TRIM,name+'/sloping sill edge')
        fascia(x0-.10,x1+.10,z1+.10,z1+.190,.195,TRIM,name+'/lintel hood')
    apron=traced('central-apron')
    face(apron,-.011,.095,GRILLE,'central bay/deep dark window apron')
    face(apron.difference(apron.buffer(-.066,join_style='mitre')),.0955,.135,DARK,'central bay/apron perimeter frame')
    for end in ('west','east'):
        body=traced(end+'-coffer-frame')
        for r in (1,2):
            for c in (1,2):
                cell=traced(f'{end}-coffer-{r}-{c}')
                face(cell.difference(cell.buffer(-.057,join_style='mitre')),.028,.094,TRIM,f'{end} spandrel/recess {r}-{c}')
        face(body,-.008,.025,WALL,end+' spandrel/panel behind four coffers')
        face(traced(end+'-bottom'),-.010,.228,TRIM,end+' spandrel/lower mould')
    for key in ('west-corner-flute','west-corner-edge','east-corner-edge'):
        strip=LineString([surface_point(p) for p in PIX[key]]).buffer(.063,cap_style='flat')
        face(strip,-.007,.144,TRIM,key+'/raised corner band')
    # Model the layered cornice and the shallow pediment independently of the hidden roof.
    for i,(z,th,depth,over,mat) in enumerate([
        (4.19,.165,.29,.17,STONE),(4.355,.103,.19,.115,TRIM),
        (12.09,.133,.163,.08,TRIM),(12.23,.078,.236,.13,STONE),
        (12.31,.174,.29,.18,TRIM),(12.49,.135,.37,.235,TRIM),(12.63,.161,.45,.29,STONE)]):
        fascia(-.32-over,width+.20+over,z,z+th,depth,mat,f'street cornice/course {i+1}')
    xmid=5.62;left=2.37;right=8.90;base=12.68;peak=13.78
    pediment=Polygon([(left,base),(xmid,peak),(right,base)])
    face(pediment,-.43,.031,WALL,'attic pediment/triangular infill')
    for i,(w,dep,raised) in enumerate([(.185,.315,0.),(.063,.36,.105),(.094,.240,-.126)]):
        slope=LineString([(left-.09,base+raised),(xmid,peak+raised),(right+.09,base+raised)])
        face(slope.buffer(w/2,cap_style='flat',join_style='mitre'),-.35,dep,TRIM,f'attic pediment/raking cornice {i+1}')
    for i,x in enumerate(np.arange(-.24,width+.15,.220 if not lod else .440)):
        scene.box((x,-.152,12.20),(.092 if not lod else .14,.144,.112),TRIM,label=f'cornice/dentil {i+1:02}')
    return entrance.add(scene,lod)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    print(build(args.lod).save(args.output,META)['sha256'])
