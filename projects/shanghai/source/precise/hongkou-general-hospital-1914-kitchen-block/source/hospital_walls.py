"""Open brick envelope, return quoins, original street portals and the documented courtyard balcony."""
from math import ceil, hypot
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from hospital_finish import BRICK,TEXTURE
from hospital_sashes import add_window,_finish
STONE='1914 block | buff limestone'
LIGHT='1914 block | cut limestone cap'
SHADE='1914 block | stone drip and recessed beds'
SOCKET='1914 block | dark portal reveal'
WOOD='1914 block | stained entrance doors'
PANEL='1914 block | door field panels'
BRASS='1914 block | aged pull handles'
IRON='1914 block | wrought balcony rail'
PIPE='1914 block | dark rainwater goods'
PALETTE={BRICK:dict(texture=str(TEXTURE),color=[1,1,1],roughness=.95),STONE:_finish((173,155,134),.93),
         LIGHT:_finish((190,173,151),.89),SHADE:_finish((146,128,109),.94),SOCKET:_finish((109,91,76),.95),
         WOOD:_finish((71,49,39),.74),PANEL:_finish((84,60,48),.76),BRASS:_finish((137,124,94),.47,.48),
         IRON:_finish((66,61,55),.68,.32),PIPE:_finish((84,77,69),.74,.17)}
# The coloured stone bands are measured between adjacent sash openings in the Qiao street plate.
QUOINS=[(4.31,4.61),(5.38,5.68),(6.43,6.74),(7.34,7.69),(8.43,8.67),(9.65,9.92),
        (10.80,11.10),(11.95,12.28),(13.01,13.42),(14.16,14.45),(15.22,15.49),
        (16.24,16.56),(17.11,17.47),(18.56,18.85),(19.71,20.02),(20.86,21.19),(21.98,22.26)]

def surface(b,kind,station,shape,inner,outer,mat,name):
    if shape.is_empty:return
    if kind=='north':
        sign=1
        def point(t,z,p):return t,station-p,z
    elif kind in ['east','recess']:
        sign=-1
        def point(t,z,p):return station+p,t,z
    elif kind in ['court','jog']:
        sign=-1
        def point(t,z,p):return t,station-p,z
    else:
        sign=1
        def point(t,z,p):return station+p,t,z
    a,h=sorted((sign*inner,sign*outer))
    b.prism(shape,a,h,point,mat,name)

def opening(o):return box(o['center']-o['width']/2,o['sill'],o['center']+o['width']/2,o['head'])

def door(b,face,st,o,lod):
    c=o['center'];w=o['width'];lo=o['sill'];hi=o['head'];left,right=c-w/2,c+w/2
    prefix=face+' '+o['id']+' entrance '
    def add(shape,d0,d1,mat,title):
        surface(b,face,st,shape,d0,d1,mat,prefix+title)
    def slab(x0,z0,x1,z1,d0,d1,mat,title):
        add(box(x0,z0,x1,z1),d0,d1,mat,title)
    # The photograph shows a deep stone-faced recess in front of dark double leaves.
    architrave=box(left-.19,lo,right+.19,hi+.20).difference(box(left,lo-.01,right,hi))
    add(architrave,-.021,.092,STONE,'inner three-sided casing')
    lining=box(left,lo,right,hi).difference(box(left+.082,lo+.005,right-.082,hi-.082))
    add(lining,-.315,-.116,SOCKET,'deep stone lining')
    capw=w+.98
    rise=.30 if face=='east' else 0.
    if rise:
        slab(c-capw/2,hi+.12,c+capw/2,hi+.52,-.016,.055,STONE,'entrance head field')
        slab(c-.60,hi+.24,c+.60,hi+.41,.051,.074,SHADE,'inset panel margin')
        slab(c-.554,hi+.268,c+.554,hi+.39,.071,.082,STONE,'inset plain panel')
    for sign in [-1,1]:
        x=left-.32 if sign<0 else right+.32
        slab(x-.18,lo,x+.18,hi+.28,-.012,.089,STONE,'jamb backing '+str(sign))
        for n in range(3):
            base=lo+.16+n*(hi-lo-.25)/3
            slab(x-.21,base,x+.21,base+.36,-.02,.142,LIGHT,'rusticated jamb '+str(sign)+' '+str(n))
    course=[(.16,.38,.10,STONE),(.38,.46,.17,SHADE),(.46,.54,.22,LIGHT),(.60,.67,.29,LIGHT),(.67,.72,.26,STONE)]
    for k,(z0,z1,depth,mat)in enumerate(course):
        over=.20 if k>=2 else 0.
        slab(c-capw/2-over,hi+z0+rise,c+capw/2+over,hi+z1+rise,-.018,depth,mat,'lintel moulding '+str(k))
    teeth=max(7,round((capw+.24)/.155))
    for k in range(teeth):
        x=c-capw/2+(k+.5)*capw/teeth
        slab(x-.039,hi+.525+rise,x+.039,hi+.61+rise,.13,.232,STONE,'lintel dentils')
    slab(left-.01,lo-.01,right+.01,lo+.052,-.35,.046,SHADE,'threshold')
    for side,(x0,x1)in enumerate([(left+.055,c-.009),(c+.009,right-.055)]):
        slab(x0,lo+.032,x1,hi-.045,-.34,-.291,WOOD,'door leaf '+str(side))
        stile=.084
        for j,(z0,z1)in enumerate([(.11,.30),(.36,.62),(.69,.90)]):
            core=box(x0+stile,lo+(hi-lo)*z0,x1-stile,lo+(hi-lo)*z1)
            slab(*core.bounds,-.293,-.27,PANEL,'raised field '+str(side)+' '+str(j))
            if not lod:
                add(core.buffer(.024,join_style=2).difference(core),-.29,-.244,WOOD,'panel mould '+str(side)+' '+str(j))
        handle=(x1-.065)if side==0 else(x0+.065)
        slab(handle-.016,lo+.87,handle+.016,lo+1.10,-.275,-.207,BRASS,'vertical pull '+str(side))

def ground_window(b,face,st,o):
    c=o['center'];w=o['width'];lo=o['sill'];hi=o['head'];x0=c-w/2;x1=c+w/2
    def slab(a,z,e,h,x,y,mat,name):
        surface(b,face,st,box(a,z,e,h),x,y,mat,face+' '+o['id']+' '+name)
    for j in range(4):
        z=lo+.25+j*(hi-lo-.44)/4
        for a,e in [(x0-.36,x0),(x1,x1+.36)]:
            slab(a,z,e,z+.18,-.011,.019,STONE,'alternating squared blocks '+str(j))
    slab(x0-.19,lo-.12,x1+.19,lo,-.022,.15,STONE,'deep continuous sill')
    slab(x0-.16,hi,x1+.16,hi+.13,-.015,.055,STONE,'lintel')
    slab(x0-.23,hi+.13,x1+.23,hi+.20,-.011,.171,SHADE,'hood drip')
    slab(x0-.29,hi+.20,x1+.29,hi+.28,-.012,.215,LIGHT,'hood cap')

def add_walls(b,l,lod=False):
    w,d,e=l['width'],l['depth'],l['eaves'];rx,ry=l['short_return_x'],l['short_return_depth'];t=.48
    f=l['faces'];ground=l['ground']
    bounds=[('north',0.,0.,w,f['north']+ground['north']),('east',0.,t,ry-t,[o for o in f['east'] if o['wall_x']==0]+ground['east']),
            ('recess',rx,ry,d-t,[o for o in f['east']if o['wall_x']>0]),('jog',ry,0.,rx+t,[]),
            ('court',d,rx,w,f.get('court',[])),('west',w,t,d-t,[])]
    for face,st,a,c,opens in bounds:
        holes=unary_union([opening(o)for o in opens]);skin=box(a,0,c,e-.155)
        surface(b,face,st,skin.difference(holes),-t,0.,BRICK,face+' continuous perforated brick wall')
        if face=='west':continue
        def course(za,zb,d0,d1,mat,label,x0=a,x1=c):
            shape=box(x0,za,x1,zb).difference(holes)
            surface(b,face,st,shape,d0,d1,mat,face+' '+label)
        if face=='east':
            # Photographs from three streetside stations show a fully dressed base on the
            # projecting east bay. The recessed run beyond it remains exposed red brick.
            course(.18,3.82,-.012,.046,STONE,'dressed eastern entrance bay',0.,ry)
        elif face=='north':
            course(.18,3.82,-.012,.046,STONE,'short return of eastern stone bay',0.,.205)
        elif face=='jog':
            course(.18,3.82,-.012,.046,STONE,'return of eastern entrance bay',0.,.17)
        course(.015,.25,-.01,.066,SHADE,'stone base')
        for j,(z0,z1,p,m) in enumerate([(3.69,3.80,.055,STONE),(3.80,3.90,.102,SHADE),(3.90,4.05,.16,LIGHT),(4.05,4.11,.093,STONE)]):
            course(z0,z1,-.012,p,m,'ground-floor belt '+str(j))
        course(17.12,17.46,-.009,.019,STONE,'upper uninterrupted string course')
        if face in ('north','east','jog'):
            course(13.0,13.38,-.009,.019,STONE,'pediment-level string course')
        quoins={'north':[(0,.88)],'east':[(t,1.03),(ry-.82,ry-t)],'recess':[(ry,ry+.63),(d-.89,d-t)],
                'court':[(rx,rx+.92)],'jog':[(0,rx+t)]}.get(face,[])
        for side,(x0,x1)in enumerate(quoins):
            for j,(lo,hi)in enumerate(QUOINS):
                if lo in [13.01,17.11] and (face in ('north','east','jog')or lo==17.11):continue
                loedge=x0+((.14 if j%2 else 0) if side==1 else 0)
                end=x1-((.14 if j%2 else 0) if side==0 else 0)
                if end>loedge:course(lo,hi,-.006,.028,STONE,'corner quoin '+str(side)+' '+str(j),loedge,end)
        for o in opens:
            if o['style']=='portal':
                door(b,face,st,o,lod)
            else:
                if o.get('level')==1 and face=='north':ground_window(b,face,st,o)
                add_window(b,'east'if face=='recess'else face,o,l,lod=lod)
    foot=Polygon([(0,0),(w,0),(w,d),(rx,d),(rx,ry),(0,ry)])
    b.plan_prism(foot,-.065,.002,SHADE,'Building sole following the six corners; section below paving')
    # Visible downpipes terminate just above the sidewalk. Offsets clear the stone cornice and water table.
    for face,st,coords in [('north',0,[5.85,16.63,26.46,38.],),('court',d,[10.05,21.72,32.63])]:
        exterior=-1 if face=='north'else 1
        for j,x in enumerate(coords):
            height=e-1.14
            line=[(x,st+exterior*.125,.25),(x,st+exterior*.125,height-.42),(x,st+exterior*.27,height-.19),(x,st+exterior*.27,height)]
            b.tube(line,.064,PIPE,8 if lod else 14,face+' rainwater pipe '+str(j))
            if not lod:
                for z in [1.52,4.37,8.35,12.50,16.85,20.9]:
                    b.box((x,st+exterior*.122,z),(.16,.16,.047),PIPE,label=face+' downpipe clips '+str(j))
