"""Photographed upper arcade and rounded bay at the address named by Antigng, 2 August 2018."""
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SURVEY=json.loads((Path(__file__).resolve().parents[1]/'measurements/courtyard-camera.json').read_text())
WALL='362 | straw mineral finish'
TRIM='362 | pale ochre moulding'
DARK='362 | dark eave shadow'
FRAME='362 | painted steel'
GLASS='362 | blue grey glass'
SEALED='362 | section reveal'
PALETTE={name:{'color':col,'roughness':rough} for name,col,rough in [
    (WALL,[.68,.58,.395],.92),(TRIM,[.80,.72,.53],.85),(DARK,[.25,.25,.24],.87),
    (FRAME,[.19,.20,.19],.59),(GLASS,[.27,.36,.40],.35),(SEALED,[.48,.43,.34],.88)]}
CIRCLE=(-6.7910,-.09360)
SECTOR=(-119.,4.)

def face(b,shape,front,back,mat,name):
    b.prism(shape,-back,-front,lambda x,z,w:(x,-w,z),mat,name)

def sector(b,limits,r0,r1,z0,z1,mat,name,lod):
    # The two radial seams terminate the photographed fragment. Chordal sectors share exact edges.
    n=max(1,math.ceil((limits[1]-limits[0])/(8 if lod else 3)))
    verts=[]
    for k in range(n+1):
        t=math.radians(limits[0]+(limits[1]-limits[0])*k/n)
        for r,z in [(r0,z0),(r1,z0),(r1,z1),(r0,z1)]:
            verts.append((CIRCLE[0]+r*math.cos(t),CIRCLE[1]+r*math.sin(t),z))
    faces=[(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)]
    for k in range(n):
        for j in range(4):
            a,b0=4*k+j,4*k+(j+1)%4
            faces.append((a,b0,b0+4,a+4))
    # The contour is r-out, up and r-in, so the order above winds toward decreasing angle.
    b.add(verts,[tuple(reversed(f)) for f in faces],mat,name)

def three_lights(b,lod):
    heads=[]
    for row in SURVEY['axes']:
        x,r,h=row['x'],row['rx'],row['rise']
        n=18 if lod else 42
        arch=[(x+r*math.cos(t*math.pi/n),h*math.sin(t*math.pi/n)) for t in range(n+1)]
        heads.append(Polygon([(x-r,-.30),(x+r,-.30),*arch]))
    # Do not extend this cutoff to a conjectural sill occluded by the contemporary sign and gate.
    shell=Polygon([(-4.92,-.30),(3.07,-.30),(3.07,1.749),(-4.92,1.920)])
    face(b,shell.difference(unary_union(heads)),0,.255,WALL,'Arcade | pierced upper wall')
    face(b,Polygon([(-4.92,1.88),(3.07,1.71),(3.07,1.79),(-4.92,1.962)]),-.078,.12,TRIM,'Arcade | projecting parapet lip')
    for i,(opening,row) in enumerate(zip(heads,SURVEY['axes']),1):
        cx,rx=row['x'],row['rx']; label=f'Arch {i}'
        def strip(x0,z0,x1,z1):return opening.intersection(box(x0,z0,x1,z1))
        rim=opening.buffer(.075,join_style='round').difference(opening).intersection(box(cx-rx-.09,-.299,cx+rx+.09,1.4))
        face(b,rim,-.035,.052,TRIM,label+' | plaster arch mould')
        inside=opening.buffer(-.028)
        face(b,opening.difference(inside),.043,.103,FRAME,label+' | curved sash')
        face(b,inside,.105,.128,GLASS,label+' | recessed glazing')
        face(b,strip(cx-.025,-.295,cx+.025,row['rise']),.054,.106,FRAME,label+' | centre mullion')
        face(b,strip(cx-rx,-.058,cx+rx,.025),.050,.103,FRAME,label+' | transom')

def round_bay(b,lod):
    low,high=SECTOR
    # Joint elevations of the bowed window were read at the middle and right jamb, away from silhouette.
    lo,hi=-112.,-55.; sill,head=1.896,3.51
    lower_head=.76
    sector(b,SECTOR,1.58,1.815,lower_head,sill,WALL,'Bow | waist between windows',lod)
    sector(b,(low,lo),1.58,1.815,-.30,lower_head,WALL,'Bow | lower left jamb',lod)
    sector(b,(hi,high),1.58,1.815,-.30,lower_head,WALL,'Bow | lower right pier',lod)
    sector(b,(lo,hi),1.753,1.775,-.30,lower_head,GLASS,'Bow | visible top of lower window',lod)
    for i,a in enumerate([lo,-94.1,-81.5,-68.8,hi]):
        w=1.75 if i in (0,2,4) else .55
        sector(b,(a-w/2,a+w/2),1.771,1.82,-.30,lower_head,FRAME,f'Bow | lower glazing bar {i+1}',lod)
    for i,height in enumerate([-.02,.38,lower_head-.025]):
        sector(b,(lo,hi),1.77,1.819,height-.018,height+.018,FRAME,f'Bow | lower horizontal {i+1}',lod)
    sector(b,(low,lo),1.58,1.815,sill,head,WALL,'Bow | left jamb return',lod)
    sector(b,(hi,high),1.58,1.815,sill,head,WALL,'Bow | broad curved right pier',lod)
    sector(b,SECTOR,1.58,1.815,head,3.735,WALL,'Bow | header',lod)
    sector(b,(lo,hi),1.753,1.775,sill,head,GLASS,'Bow | curved steel-window glazing',lod)
    # A stout dividing mullion and three much lighter vertical glazing bars remain legible.
    for i,a in enumerate([lo,-94.1,-81.5,-68.8,hi]):
        w=1.75 if i in (0,2,4) else .55
        sector(b,(a-w/2,a+w/2),1.771,1.82,sill,head,FRAME,f'Bow | mullion {i+1}',lod)
    for i,height in enumerate([sill+.035,2.27,2.59,2.97,3.29,head-.035]):
        w=.052 if i in (0,5) else .020
        sector(b,(lo,hi),1.77,1.817,height-w/2,height+w/2,FRAME,f'Bow | horizontal bar {i+1}',lod)
    sector(b,(lo-1,hi+1),1.72,1.855,sill-.060,sill,TRIM,'Bow | window sill',lod)
    for i,(r,z0,z1,mat) in enumerate([(1.852,3.73,3.77,TRIM),(1.842,3.77,3.87,DARK),
                                      (1.887,3.87,3.927,TRIM),(1.889,3.927,3.970,DARK),(1.903,3.970,4.009,TRIM)]):
        sector(b,SECTOR,1.58,r,z0,z1,mat,f'Bow | cornice course {i+1}',lod)
    for i in range(29):
        t=low+(high-low)*(i+.5)/29
        sector(b,(t-1.04,t+1.04),1.834,1.871,3.780,3.873,TRIM,f'Bow | dentil {i+1}',lod)

def add_court_arcade(b,lod=False,layout=None):
    for name,material in PALETTE.items():b.palette.setdefault(name,material)
    three_lights(b,lod)
    round_bay(b,lod)

if __name__=='__main__':
    import argparse,sys
    parser=argparse.ArgumentParser();parser.add_argument('out',type=Path);parser.add_argument('--lod',action='store_true')
    args=parser.parse_args(); project=next(p for p in Path(__file__).resolve().parents if (p/'tools/package_architectural_model.py').is_file())
    sys.path.insert(0,str(project/'source/precise/hongkou-general-post-office/source/common'))
    from photo_architecture import Builder
    b=Builder(PALETTE);add_court_arcade(b,args.lod)
    b.save(args.out,dict(name='襄阳南路362号照片所见院侧三券与弧形檐',scope='2018年具名照片的可见上部截段',source=SURVEY['source'],photo_author='Antigng',photo_license='CC BY-SA 4.0',source_photo_embedded=False))
