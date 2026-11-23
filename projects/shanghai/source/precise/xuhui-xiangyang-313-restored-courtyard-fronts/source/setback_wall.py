"""South court service wall with individually cut openings, glazed leaves and projecting fittings."""
import json
import math
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade
from register_courtyard import Camera
from foreground_bay import FRAME, REVEAL, GLASSES, SILL, PLASTER, HARDWARE
from canopy_front import HOOD, lid, beam
from service_balcony import section_sheet

OBS=json.loads((Path(__file__).parent.parent/'measurements/setback-wall-readings.json').read_text())
DEPTH=OBS['setback_m']
CLOTH='Xiangyang 313 | blue violet fabric awning'
BRIGHT='Xiangyang 313 | pale service window railing'
CYAN='Xiangyang 313 | blue green door reflection'
PALETTE={CLOTH:{'color':[.106,.105,.18],'roughness':.90},
         BRIGHT:{'color':[.56,.57,.545],'metallic':.33,'roughness':.55},
         CYAN:{'color':[.106,.245,.247],'metallic':.14,'roughness':.35}}

def windows(face,name,bounds):
    l,lo,r,hi=bounds;w=r-l;h=hi-lo
    outer=box(l,lo,r,hi)
    clear=box(l+.042,lo+.04,r-.042,hi-.04)
    face.prism(outer,-.235,-.22,REVEAL,name+' / dark back')
    pieces=[outer.difference(clear)]
    x=l+w*(.53 if name in ('upper-east','middle-east') else .5)
    pieces.append(box(x-.022,lo,x+.022,hi))
    transom=hi-h*(.32 if name.startswith('upper') else .22)
    if name=='balcony-open':transom+=.038
    pieces.append(box(l,transom-.025,r,transom+.025))
    if name=='middle-east':
        for f in (.17,.32,.47,.62):
            z=lo+f*h
            pieces.append(box(l,z-.015,r,z+.015))
    if name=='upper-east':
        for f in (.18,.38,.58):
            z=lo+f*h
            pieces.append(box(x,z-.017,r,z+.017))
    if name=='balcony-fixed':
        for f in (.41,.60):
            z=lo+f*h
            pieces.append(box(x,z-.015,r,z+.015))
    frame=unary_union(pieces).intersection(outer)
    face.prism(frame,-.097,-.050,FRAME,name+' / dark frame and rails')
    for pane in clear.difference(frame).geoms:
        u=pane.centroid.x;z=pane.centroid.y
        if name in ('balcony-open','upper-open','upper-shaded') and z<transom and u<x:
            continue
        mat=GLASSES[1] if z>transom else GLASSES[0]
        if name.startswith('balcony') and z<transom:mat=CYAN
        face.prism(pane,-.13,-.122,mat,name+' / separate pane')
    if not name.startswith('balcony'):
        sill_depth=.158 if name=='middle-east' else .136
        sill_height=.084 if name=='middle-east' else .055
        face.box((l+r)/2,lo-sill_height/2,w+.13,sill_height,sill_depth,.015,SILL,name+' / pale sill')
    if name=='balcony-open':
        # A partly open leaf, seen edge-on left of the two balcony doors.
        sash=Facade(face.builder,(l+.024,DEPTH+.068),(l-.22,DEPTH-.32),name+' / hinged leaf')
        half=sash.length/2;frame=box(-half,lo+.06,half,transom-.03)
        glass=box(-half+.026,lo+.097,half-.026,transom-.07)
        sash.prism(frame.difference(glass),-.016,.016,FRAME,'narrow perimeter')
        sash.prism(glass,-.007,.006,CYAN,'reflected glazing')

def fitted_hood(b,c,name,record,lod):
    y=DEPTH-record['depth_m']
    a,d=[c.wall(uv,y) for uv in record['front']]
    back=[c.wall(uv,DEPTH) for uv in record['back']]
    left,right=a[0],d[0];tip=(a[2]+d[2])/2;rear=sum(p[2] for p in back)/2
    material=HOOD if name.startswith('cyan') else CLOTH
    lid(b,left,right,DEPTH+.013,y,rear,tip,.019,material,'south court '+name)
    for frac in ((0,.34,.67,1.) if material==HOOD else (.03,.97)):
        x=left+frac*(right-left)
        beam(b,(x,DEPTH,rear-.014),(x,y,tip-.014),.024,.027,HARDWARE,'south court '+name+' / bracket')
        beam(b,(x,DEPTH,rear-.17),(x,y+.03,tip-.034),.016,.018,HARDWARE,'south court '+name+' / brace')
    if record['drop_px']:
        p=(record['front'][0][0],record['front'][0][1]+record['drop_px'])
        drop=max(.028,tip-c.wall(p,y)[2])
        n=8 if name.startswith('violet') else 6
        steps=n*(4 if lod else 8);rings=[]
        for i in range(steps+1):
            t=i/steps;x=left+(right-left)*t;bottom=tip-drop*(.57+.43*abs(math.sin(t*n*math.pi)))
            rings.append(((x,y-.01,tip),(x,y+.012,tip),(x,y+.012,bottom),(x,y-.01,bottom)))
        section_sheet(b,rings,material,'south court '+name+' / scalloped hem')

def window_rail(b,c,name,record,lod):
    y=DEPTH-record['depth_m']
    a,d=[c.wall(uv,y) for uv in record['front']]
    left,right=a[0],d[0];z=(a[2]+d[2])/2
    b.box(((left+right)/2,(y+DEPTH)/2,z-.028),(right-left,DEPTH-y,.05),HARDWARE,label=name+' / projecting shelf')
    for rail in ((z+.047,z+.114,z+.184) if name=='eastern rails' else (z+.055,z+.17)):
        beam(b,(left,y,rail),(right,y,rail),.017,.024,BRIGHT,name+' / front rail')
        for x in (left,right):
            beam(b,(x,y,rail),(x,DEPTH,rail),.017,.024,BRIGHT,name+' / end return')
    for f in (0,.33,.66,1):
        x=left+f*(right-left);beam(b,(x,y,z),(x,y,z+.18),.022,.022,BRIGHT,name+' / rail post')
    for x in (left+.13,right-.12):
        beam(b,(x,DEPTH,z-.19),(x,y+.04,z-.037),.027,.03,HARDWARE,name+' / shelf bracket')

def add_setback_wall(b,lod=False):
    c=Camera('case1');face=Facade(b,(-1,DEPTH),(1,DEPTH),'south court / recessed window wall')
    bounds={key:rec['bounds_xz_m'] for key,rec in OBS['openings'].items()}
    # The wall under the projection continues up to its recessed lower return;
    # above it the courtyard's projecting bay covers that same strip.
    height=(11.33-1.43)/1.08
    wall=box(-9.311,0,-2.163,height)
    holes=unary_union([box(*v) for v in bounds.values()])
    face.prism(wall.difference(holes),-.17,0,PLASTER,'masonry with seven cut openings')
    for key,v in bounds.items():windows(face,key,v)
    for name,record in OBS['fittings'].items():
        if name.endswith('rails'):window_rail(b,c,name,record,lod)
        else:fitted_hood(b,c,name,record,lod)
