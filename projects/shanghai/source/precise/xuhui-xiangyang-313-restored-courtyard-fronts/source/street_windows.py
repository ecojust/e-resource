"""Photographed western fold, No. 313 courtyard, 22 February 2020."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade

HERE=Path(__file__).resolve().parent
CONTROL=json.loads((HERE.parent/'measurements/west-fold-controls.json').read_text())
EDGES={int(k):v for k,v in CONTROL['edges_enu'].items()}
ROOF_HEIGHT={int(k):v for k,v in CONTROL['roof_upper_Z_m'].items()}
WALL='Xiangyang 313 | pale courtyard render'
FRAME='Xiangyang 313 | dark painted window joinery'
GLASS='Xiangyang 313 | western pale reflected glass'
BLUE='Xiangyang 313 | western blue-grey reflected glass'
SHADE='Xiangyang 313 | western upper sash in shade'
STONE='Xiangyang 313 | pale projecting sill'
VALANCE='Xiangyang 313 | violet fabric window hood'
PIPE='Xiangyang 313 | weathered iron pipework'
PALETTE={
 WALL:{'color':[.84,.79,.65],'roughness':.88},FRAME:{'color':[.058,.053,.049],'roughness':.68},
 GLASS:{'color':[.60,.63,.65],'metallic':.13,'roughness':.37},
 BLUE:{'color':[.22,.37,.41],'metallic':.15,'roughness':.35},
 SHADE:{'color':[.09,.095,.094],'roughness':.49},
 STONE:{'color':[.65,.63,.58],'roughness':.81},
 VALANCE:{'color':[.19,.15,.23],'roughness':.9},
 PIPE:{'color':[.13,.122,.115],'roughness':.73}}
GRID={'main middle':(3,5),'angled middle':(2,5),'north middle':(2,5),'north upper':(1,2),'main upper':(2,1)}

def window(face,name,shape,lod):
    """Construct the sash frame and each glazed field behind a through opening."""
    u0,z0,u1,z1=shape.bounds
    cols,rows=GRID[name];w=u1-u0;h=z1-z0
    width=.042 if 'upper' not in name else .038
    light=shape.buffer(-width,join_style=2)
    xbars=[box(u0+w*i/cols-.024,z0,u0+w*i/cols+.024,z1) for i in range(1,cols)]
    row_heights=[i/rows for i in range(1,rows)]
    if name=='north upper':row_heights=[.80]
    slender=.013 if 'upper' not in name else .018
    zbars=[box(u0,z0+h*q-slender,u1,z0+h*q+slender) for q in row_heights]
    panes=light.difference(unary_union(xbars+zbars))
    face.prism(shape.difference(panes),-.108,-.040,FRAME,name+'/exterior frame and real glazing bars')
    material=BLUE if name=='angled middle' else SHADE if 'upper' in name else GLASS
    if lod:
        face.prism(shape,-.142,-.126,material,name+'/inset glass')
    else:
        for j,pane in enumerate(getattr(panes,'geoms',[panes])):
            face.prism(pane.buffer(.008,join_style=2),-.142,-.126,material,name+f'/inset pane {j+1}')
    face.box((u0+u1)/2,z0-.034,w+.145,.068,.225,.042,STONE,name+'/projecting sill')

def window_hood(face,shape,lod):
    """The one filmed violet hood on the high west opening has a hanging fabric edge."""
    u0,lo,u1,hi=shape.bounds
    u0-=.26;u1+=.14;project=.45;fall=.19
    corners=[(u0,0),(u1,0),(u1,project),(u0,project)]
    vertices=[face.point(u,hi+.075-fall*d/project+offset,d) for offset in [-.019,.019] for u,d in corners]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    # Point's second horizontal axis is the outward normal; the basis reverses handedness.
    faces=[tuple(reversed(f)) for f in faces]
    face.builder.add(vertices,faces,VALANCE,face.label+'/sloping fabric canopy')
    z=hi+.075-fall
    n=12 if lod else 32
    xs=np.linspace(u0,u1,n+1)
    hem=[(x,z-.125-.046*abs(np.sin((x-u0)/(u1-u0)*4*np.pi))) for x in xs]
    face.prism(Polygon([(u0,z+.015),(u1,z+.015),*reversed(hem)]),project-.014,project+.011,VALANCE,'scalloped front valance')
    # The station sees the fabric hang down the wall ends on both sides.
    cheek=Polygon([(0,hi+.075),(project,z+.006),(project,z-.12),(0,hi-.46)])
    for u in (u0,u1):
        face.builder.prism(cheek,-u-.014,-u+.014,lambda d,h,p:face.point(-p,h,d),VALANCE,face.label+'/canvas at hood end')
    for u in [u0+.045,u1-.045]:
        face.line((u,hi-.19,.012),(u,z+.01,project-.036),.012,PIPE,6 if lod else 10,'canopy support stay')

def add_street_windows(b,lod=False):
    for name,material in PALETTE.items():b.palette.setdefault(name,material)
    for i,(a,end) in EDGES.items():
        face=Facade(b,a,end,f'western folded facade / edge {i}')
        openings={name:box(*v['bounds_uz_m']) for name,v in CONTROL['openings'].items() if v['edge']==i}
        height=ROOF_HEIGHT[i]
        face.wall(0.,height-.075,list(openings.values()),thickness=.23,material=WALL)
        face.box(0,height-.038,face.length+.038,.076,.29,-.083,STONE,'flat concrete coping')
        for name,shape in openings.items():
            window(face,name,shape,lod)
            if name=='main upper':window_hood(face,shape,lod)
        if i==9:
            # The 2020 near-front image shows this pipe and the horizontal offset above the pair.
            u=-face.length/2+.08
            face.line((u,.15,.074),(u,height-.03,.074),.041,PIPE,8 if lod else 14,'vertical rainwater downpipe')
            face.line((u,8.13,.064),(.50,8.13,.064),.027,PIPE,8 if lod else 14,'dark horizontal service line')
            for z in (2.20,5.05,8.19,10.45):
                face.box(u,z,.126,.039,.094,.052,PIPE,'pipe clamp')
