"""The photographically visible broad and canted window walls, central loggia and recessed timber entrance."""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
from bay_carvings import STONE,SCULPT,DEEP,apron,spandrel,guilloche

HERE=Path(__file__).absolute().parent.parent/'measurements'
BASE='Fudefang | blue grey plinth'
DARK='Fudefang | charcoal shutter'
SLAT='Fudefang | recessed shutter louvre'
SASH='Fudefang | painted frame'
GLASS='Fudefang | subdued glazing'
OAK='Fudefang | dark entrance wood'
TILE='Fudefang | pale step stone'
INLAY='Fudefang | entry mosaic'
ROOM='Fudefang | shaded recess'
PALETTE={BASE:dict(color=[.17,.23,.246],roughness=.88),DARK:dict(color=[.066,.057,.053],roughness=.79),
         SLAT:dict(color=[.035,.031,.03],roughness=.83),SASH:dict(color=[.066,.061,.050],roughness=.64),
         GLASS:dict(color=[.11,.126,.127],roughness=.37),OAK:dict(color=[.14,.070,.043],roughness=.71),
         INLAY:dict(color=[.126,.162,.151],roughness=.72),ROOM:dict(color=[.077,.084,.071],roughness=.96),
         TILE:dict(color=[.54,.55,.50],roughness=.90)}
def cut_stone(face,wall,left,right,bottom,top,lod):
    # Ashlar joints stop at every opening and turn the corners of the bays.
    lines=[];width=right-left
    for j,z in enumerate(np.arange(bottom+.30,top,.456)):
        lines.append(box(left,z,right,z+.007))
        for x in np.arange(left+.37+(j%2)*.49,right,.98):
            lines.append(box(x,z+.008,x+.006,min(z+.456,top)))
    face.prism(unary_union(lines).intersection(wall),-.002,.003,DEEP,'coursed joints')
def sah_window(face,u,w,base,top,level,narrow,closed,lod):
    left=u-w/2;right=u+w/2;head=top;low=base
    slit=box(left,low,right,head)
    face.prism(box(left-.071,low-.039,right+.071,head+.095).difference(slit),-.007,.041,SCULPT,'stone sash surround')
    face.box(u,low-.014,w+.152,.100,.164,.038,SCULPT,'projecting sill')
    inner=box(left+.04,low+.044,right-.04,head-.044)
    face.prism(slit.difference(inner),-.20,-.12,SASH,'stepped reveal and lining')
    if closed:
        face.prism(inner,-.19,-.175,SLAT,'shadow behind closed shutter')
        dz=.138 if lod else .071
        bars=unary_union([box(left+.040,z,right-.040,min(z+dz-.010,head-.045))
                          for z in np.arange(low+.045,head-.045,dz) if z+.011<head-.045])
        face.prism(bars,-.172,-.142,DARK,'recessed horizontal shutter blades')
    else:
        face.prism(inner,-.220,-.202,GLASS,'recessed casement glass')
        count=2 if narrow else 4
        for t in np.arange(1,count)/count:
            face.box(left+w*t,(low+head)/2,.029,head-low-.06,.045,-.136,SASH,'wood sash muntin')
        for f,sz in [(.27,.030),(.71,.052),(.86,.025)]:
            face.box(u,low+f*(head-low),w-.066,sz,.047,-.134,SASH,'window transom')
    apron(face,u,w+.12,low-.07,lod)
    guilloche(face,u,w+.14,head+.033,.07,lod)
def bay(face,spec,lod):
    style,u,width,storeys,closed,supported=spec
    left=-face.length/2;right=face.length/2;upper=11.325
    holes=[box(u-width/2,lo,u+width/2,hi)for lo,hi in storeys] if supported else []
    wall=box(left,-.018,right,upper).difference(unary_union(holes))
    face.prism(wall,-.25,0,STONE,'masonry with continuous open window reveals')
    face.box(0,.17,face.length,.37,.063,.002,BASE,'blue grey plinth below the ground windows')
    cut_stone(face,wall,left,right,.35,upper,lod)
    if not supported:return
    for i,(lo,hi) in enumerate(storeys):
        sah_window(face,u,width,lo,hi,i,style!='broad',closed[i],lod)
    for i in range(2):
        z0=storeys[i][1]+.28;z1=storeys[i+1][0]-.45
        spandrel(face,u,width+.21,z0,z1,style!='broad',lod)
def solid(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def center(b,lod):
    l,r=-2.28,2.28;post=.45;back=1.596
    face=Facade(b,(l,back),(r,back),'Garden | recessed center')
    opening=box(-1.002,.58,1.002,3.344)
    mids=[box(-1.69,4.60,-.55,6.65),box(.53,4.60,1.64,6.65)]
    uppers=[box(-1.50,7.80,-.36,10.51),box(.25,7.80,1.40,10.51)]
    wall=box(l,0,r,11.34).difference(unary_union([opening,*mids,*uppers]))
    face.prism(wall,-.255,.0,STONE,'recessed entrance and two-storey gallery wall')
    frame=box(-1.002,.58,1.002,3.345).difference(box(-.92,.58,.92,3.25))
    face.prism(frame,-.19,-.13,OAK,'dark wood entrance surround')
    face.box(0,2.84,1.97,.13,.10,-.145,OAK,'door transom lintel')
    for x in (-.57,.57):
        face.box(x,1.68,.062,2.20,.082,-.15,OAK,'door side-light mullion')
    for x in (-.77,.77):
        face.box(x,1.65,.31,2.08,.033,-.185,GLASS,'dark glazed sides to entrance opening')
        face.box(x,.72,.31,.23,.054,-.159,OAK,'low solid panel')
        for z in (1.68,2.27):
            face.box(x,z,.30,.028,.056,-.147,OAK,'narrow side-light glazing bar')
    face.box(0,3.038,1.83,.265,.035,-.17,GLASS,'dark glazed transom')
    for x in (-.59,0,.59):
        face.box(x,3.046,.046,.289,.057,-.131,OAK,'transom mullion')
    # A short, bounded dark recess is visible through the open central passage.
    solid(b,-1.05,-.98,1.61,3.05,.57,3.32,ROOM,'Entrance | side of shadow recess')
    solid(b,.98,1.05,1.61,3.05,.57,3.32,ROOM,'Entrance | opposite side of shadow recess')
    solid(b,-1.03,1.03,3.05,3.12,.57,3.33,ROOM,'Entrance | limit of visible interior')
    solid(b,l,r,.62,1.77,.45,.56,TILE,'Entrance | entrance landing')
    solid(b,-1.02,1.02,1.60,3.10,.50,.58,TILE,'Entrance | inside threshold')
    for win in mids+uppers:
        x0,z0,x1,z1=win.bounds
        face.prism(win,-.24,-.214,GLASS,'dark casement inside loggia')
        for x in (x0+.025,(x0+x1)/2,x1-.025):face.box(x,(z0+z1)/2,.043,z1-z0,.062,-.144,SASH,'gallery sash stile')
        face.box((x0+x1)/2,z0+(z1-z0)*.72,x1-x0,.056,.062,-.144,SASH,'gallery window transom')
    # The top loggia presents a shallow opening with scooped and stepped corner haunches.
    y=.835;front=Facade(b,(l,y),(r,y),'Upper loggia | garden opening')
    arch=Polygon([(l-.01,8.70),(r+.01,8.70),(r+.01,10.28),(r-.13,10.28),
                  (r-.17,10.45),(r-.39,10.55),(r-.50,10.73),(r-.66,10.78),
                  (l+.66,10.78),(l+.50,10.73),(l+.39,10.55),(l+.17,10.45),(l+.13,10.28),(l-.01,10.28)])
    profile=box(l,8.70,r,11.325).difference(arch)
    front.prism(profile,-.34,.0,SCULPT,'solid spandrel with stepped haunches')
    solid(b,l,r,y,back+.10,10.77,10.86,STONE,'Upper loggia | soffit')
    for x0,x1 in ((l,l+.12),(r-.12,r)):
        solid(b,x0,x1,y,back,.48,11.32,STONE,'Garden | side returns of central recess')
    # Black and grey stone rosette directly in front of the door on the landing in photograph 03.
    ring=Point(0,.83).buffer(.242,quad_segs=14 if lod else 30).difference(Point(0,.83).buffer(.207,quad_segs=14 if lod else 30))
    petals=[]
    for a in np.linspace(0,2*np.pi,8,endpoint=False):
        u=np.array([math.cos(a),math.sin(a)]);v=np.array([-u[1],u[0]]);q=np.array([0,.83])
        petals.append(Polygon([q+.048*u,q+.12*u+.04*v,q+.185*u,q+.12*u-.04*v]))
    b.plan_prism(unary_union([ring,*petals]),.5605,.563,INLAY,'Entrance | circular stone inlay')
def add_front(b,lod=False):
    data=json.loads((HERE/'front-facet-geometry.json').read_bytes());levels=data['sill_head_z']
    for hand in ('west','east'):
        p=data[hand+'_facets_local_xy']
        for j,(a,z) in enumerate(zip(p,p[1:])):
            face=Facade(b,a,z,'Garden | '+hand+' bay '+str(j+1))
            style=('outer','broad','inner')[j]if hand=='west'else ('inner','broad','outer')[j]
            if style=='broad':
                world=(sum(data['broad_opening_jamb_abs_x_m'])/2)*(1 if hand=='east'else -1)
                center_u=world-(a[0]+z[0])/2;width=1.038
                closed=[False,hand=='east',True]
            else:
                center_u=0;width=data['narrow_openings'][style+'_width_m']
                closed=[style=='outer',hand=='east' or style=='outer',True]
            bay(face,(style,center_u,width,levels,closed,hand!='east'or style!='outer'),lod)
    center(b,lod)
