"""The pebble-dashed wall, two different window assemblies and the brick arch at No. 24."""
from math import cos, sin, pi
import json
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from frontage_coordinates import CUT_BOTTOM, MEASUREMENTS, facade_point, FRONT_CAMERA, GABLE_CAMERA
from material_names import PLASTER, RED, DARK, TEXTURES

STONE='Yefeng frontage | weathered pale cement'
CAST='Yefeng frontage | shaded cast cement'
WOOD='Yefeng frontage | oxblood timber'
GLASS='Yefeng frontage | blue-grey reflected sky'
SHADE='Yefeng frontage | violet blind'
IVORY='Yefeng frontage | pale painted metal'
IRON='Yefeng frontage | iron railing'
WIRE='Yefeng frontage | galvanized mesh'
VOID='Yefeng frontage | shaded arch recess'
SIGN='Yefeng frontage | green enamel address'
LETTER='Yefeng frontage | ivory address numerals'
GREY='Yefeng frontage | grey rendered plinth'
KEY='Yefeng frontage | red keystone'
INTRADOS='Yefeng frontage | brick inside shaded passage'
BRICKS=['Yefeng frontage | radial brick '+s for s in ('brown','rose','clay','ochre','russet')]
def finish(rgb,roughness=.85,metallic=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)
PALETTE={k:dict(texture=str(f),color=[1.,1.,1.],roughness=.92,metallic=0.) for k,f in TEXTURES.items()}
for mat,rgb in [(STONE,[185,169,145]),(CAST,[122,111,98]),(WOOD,[103,61,51]),(GLASS,[126,135,152]),(SHADE,[79,67,77]),(IVORY,[188,183,173]),(IRON,[71,66,60]),(WIRE,[160,151,143]),(VOID,[56,43,44]),(SIGN,[44,97,70]),(LETTER,[221,225,190])]:
    PALETTE[mat]=finish(rgb,.39 if mat==GLASS else .71 if mat in (IRON,WIRE,LETTER,SIGN) else .88,.23 if mat in (IRON,WIRE)else 0)
PALETTE[GREY]=finish([158,151,139]);PALETTE[KEY]=finish([147,83,82]);PALETTE[INTRADOS]=finish([80,60,56])
for tag,rgb in zip(BRICKS,[(134,76,58),(156,89,64),(166,97,67),(153,100,72),(141,84,65)]):
    PALETTE[tag]=finish(rgb)

def block(b,l,r,front,back,low,high,mat,label):
    b.box([(l+r)/2,(front+back)/2,(low+high)/2],[r-l,back-front,high-low],mat,label=label)

def section(b,shape,front,back,mat,label):
    if shape.is_empty:return
    b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,label)

def xz(u,v,camera=FRONT_CAMERA):
    return tuple(facade_point(u,v,camera=camera)[[0,2]])

def rod(b,points,rad,mat,tag,lod=False):
    b.tube(points,rad,mat,6 if lod else 10,tag)

def rectangular_sash(b,opening,upper,lod):
    l,bot,r,top=opening.bounds
    tag='Pebble gable | '+('upper timber window' if upper else 'lower metal window')
    mat=WOOD if upper else IVORY
    # The different liners and glazing fill the actual through-openings in the rendered wall.
    w=.042 if upper else .048
    for x in [l+w*.5,r-w*.5]:block(b,x-w/2,x+w/2,.035,.143,bot,top,mat,tag+' jamb')
    for z in [bot+w/2,top-w/2]:block(b,l+w,r-w,.035,.143,z-w/2,z+w/2,mat,tag+' head and foot')
    if upper:
        # The timber crossing positions come from orthophotos of both registered views.
        bars=[-1.514,-1.253,-.988]
        rails=[3.720,4.067,4.421]
        edges=[l+w,*bars,r-w];levels=[bot+w,*rails,top-w]
        for a,c in zip(edges,edges[1:]):
            for lo,hi in zip(levels,levels[1:]):
                block(b,a+.004,c-.004,.206,.237,lo+.004,hi-.004,GLASS,tag+' glass')
        for i,x in enumerate(bars):
            wid=.068 if i==1 else .024
            block(b,x-wid/2,x+wid/2,.15,.214,bot+w,top-w,WOOD,tag+' timber mullions')
        for z in rails:
            block(b,l+w,r-w,.156,.209,z-.012,z+.012,WOOD,tag+' glazing bars')
        block(b,l-.065,r+.066,-.14,.18,bot-.063,bot+.013,STONE,tag+' projecting sill')
    else:
        rail=bot+.66*(top-bot)
        block(b,l+w,r-w,.076,.126,rail+.019,top-w,SHADE,tag+' dark transom')
        block(b,l+w,r-w,.043,.125,rail-.023,rail+.024,IVORY,tag+' transom rail')
        mid=(r+l)/2
        for a,c in [(l+w,mid-.023),(mid+.023,r-w)]:
            block(b,a,c,.105,.135,bot+w,rail-.023,VOID,tag+' shaded glazing')
        block(b,mid-.027,mid+.027,.039,.105,bot+w,rail-.022,IVORY,tag+' paired sash stiles')
        # The galvanised diamond net lies forward of both lower lights and below the dark upper panel.
        pane=box(l+w,bot+w,r-w,rail-.029);span=r-l;hei=top-bot
        for slope in (-1,1):
            for x0 in np.arange(l-w-hei,r+hei,.117):
                shape=LineString([(x0,bot),(x0+slope*hei,bot+hei)]).intersection(pane)
                if shape.geom_type=='LineString' and shape.length>.026:
                    rod(b,[(x,-.013,z)for x,z in shape.coords],.0034 if not lod else .0048,WIRE,tag+' diamond mesh',lod)
        # Projecting window guard with two supports and a shallow shelf, registered most clearly in photograph 4.
        block(b,l-.18,r+.18,-.34,.145,bot-.13,bot-.049,CAST,tag+' canopy lip')
        for x in np.linspace(l+.09,r-.09,3):
            section(b,Polygon([(x-.049,bot-.135),(x+.049,bot-.135),(x+.040,bot-.28),(x-.035,bot-.28)]),-.243,.04,CAST,tag+' cement support')
        y=-.325;zt=bot+.138
        rod(b,[(l-.125,.005,zt),(l-.125,y,zt),(r+.125,y,zt),(r+.125,.005,zt)],.014,IRON,tag+' top guard',lod)
        for x in np.linspace(l-.125,r+.125,11):
            rod(b,[(x,y,bot-.052),(x,y,zt)],.009,IRON,tag+' uprights',lod)
        for x in np.linspace(l-.06,r+.06,9):
            arc=[(x+.035*cos(t),y-.002,zt-.071+.053*sin(t))for t in np.linspace(.04,pi-.04,8)]
            rod(b,arc,.006,IRON,tag+' repeated arches',lod)

CHIPS=['Yefeng frontage | aggregate '+v for v in ('grey','mushroom','umber','quartz')]
for tag,rgb in zip(CHIPS,[(115,109,102),(136,123,110),(99,93,85),(151,146,135)]):
    PALETTE[tag]=finish(rgb,.96)

def show_aggregate(b,wall,lod):
    # The texture carries the fine grit. The largest aggregate projects a few millimetres.
    rng=np.random.default_rng(2408)
    left,foot,right,top=wall.bounds
    n=5 if lod else 6
    for k in range(1950):
        x=rng.uniform(left+.012,right-.012);z=rng.uniform(foot+.012,top-.012)
        rad=rng.uniform(.005,.013);aspect=rng.uniform(.55,1.);height=rng.uniform(.0026,.0065)
        phase=rng.uniform(0,2*pi);size=rng.uniform(.82,1.15,6);tone=int(rng.integers(4))
        if (lod and k%9) or not wall.contains(Point(x,z)):continue
        angle=phase+np.arange(n)*2*pi/n
        ring=[[x+rad*size[j]*cos(t),.0017,z+aspect*rad*size[j]*sin(t)]for j,t in enumerate(angle)]
        v=[[x-.001,-height,z+.0006],*ring,[x,.006,z]]
        faces=[]
        for j in range(n):
            a=j+1;c=(j+1)%n+1
            faces.extend([(0,a,c),(n+1,c,a)])
        b.add(v,faces,CHIPS[tone],'Pebble gable | embedded aggregate')

def add_gable(b,lod=False):
    left=-2.4;right=.04
    ridge=[(-2.4,7.94)]
    ridge += [xz(u,v,GABLE_CAMERA)for u,v in [(380,107),(407,111),(420,111),(447,114),(472,114),(505,115),(520,114),(530,110)]]
    ridge += [(right,6.4)]
    split=-.09
    outline=Polygon([(left,split),(right,split),*reversed(ridge)])
    # Rectified returns are averaged over both sides of each opening; the slight skew in the photograph is retained in the photo records.
    up=box(-1.81,3.335,-.733,4.766);lo=box(-1.785,.052,-.748,1.692)
    section(b,outline.difference(unary_union([up,lo])),0,1.25,PLASTER,'Pebble gable | rendered face and returns')
    cap=LineString(ridge).buffer(.048,cap_style=2,join_style=2)
    section(b,cap,-.038,1.28,CAST,'Pebble gable | shallow upturned parapet coping')
    show_aggregate(b,outline.difference(unary_union([up.buffer(.018),lo.buffer(.018)])),lod)
    for opening,upper in [(up,True),(lo,False)]:rectangular_sash(b,opening,upper,lod)
    block(b,left,right,-.055,.28,split-.035,split+.052,STONE,'Pebble gable | cement stringcourse')
    # The 2019 image records the arch crown. The later view shows its full jambs and the lower grey render.
    spring=-2.773193; apex=-1.946485;centre=-1.204004;radius=0.771639
    def arch(t,extra=0.):
        return (centre+(radius+extra)*cos(t),spring+(apex-spring+extra)*sin(t))
    angles=np.linspace(0,pi,39 if lod else 69)
    hole=Polygon([(centre+radius,CUT_BOTTOM-.35),*[arch(t)for t in angles],(centre-radius,CUT_BOTTOM-.35)])
    from entrance_recess import registration
    recess=registration();rear=recess['rear_y']
    press=np.array(json.loads((MEASUREMENTS/'press-entrance-camera.json').read_bytes())['press'])
    exterior_render=np.mean([xz(*pt,camera=press)[1]for pt in [(20,387),(48,389),(262,399),(279,400)]])
    upper=box(left,exterior_render,right,split).difference(hole)
    lower=box(left,CUT_BOTTOM,right,exterior_render).difference(hole)
    section(b,upper,0,rear+.055,RED,'No 24 entrance | red brick wall and reveals')
    section(b,lower,-.013,rear+.055,GREY,'No 24 entrance | grey finished lower wall')
    # A darker row of bricks lines the arch barrel. Its lower part continues as a pair of straight jambs.
    lining=Polygon([arch(t,.008) for t in angles]+[arch(t,-.014)for t in angles[::-1]])
    section(b,lining,.015,rear+.02,INTRADOS,'No 24 entrance | shaded inner arch of passage')
    block(b,centre-radius-.006,centre-radius+.009,.016,rear+.02,recess['render_top_z'],spring,INTRADOS,'No 24 entrance | shaded left jamb')
    # The red keystone stands proud of the radiating stretchers in the press photograph.
    keypoints=[xz(u,v,camera=press)for u,v in [(155,120),(200,126),(191,171),(160,169)]]
    section(b,Polygon(keypoints),-.066,-.039,KEY,'No 24 entrance | larger red keystone')
    ring=Polygon([arch(t)for t in angles]+[arch(t,.205)for t in angles[::-1]])
    section(b,ring.intersection(box(left,CUT_BOTTOM,right,split)),-.019,.012,DARK,'No 24 entrance | arched mortar bed')
    for k in range(29):
        ts=np.linspace((k+.028)*pi/29,(k+.974)*pi/29,4)
        seg=Polygon([arch(t,.005)for t in ts]+[arch(t,.201)for t in ts[::-1]]).intersection(box(left,CUT_BOTTOM,right,split))
        section(b,seg,-.033,-.014,BRICKS[(k*7)%5],'No 24 entrance | radial brick voussoirs')
    p=Polygon([xz(*q)for q in [(228,799),(257,795),(259,819),(228,824)]])
    section(b,p,-.034,.0,SIGN,'No 24 entrance | glazed number plate')
    digits={'2':[(0,.16),(.15,.02),(.7,0),(1,.21),(.96,.38),(.02,.95),(1,.95)],
            '4':[(.78,1),(.78,.04),(0,.66),(1,.66)]}
    for i,digit in enumerate('24'):
        pts=[facade_point(232+i*9+6.2*u,801+12*v,-.042)for u,v in digits[digit]]
        rod(b,pts,.007,LETTER,'No 24 entrance | digit '+digit,lod)
