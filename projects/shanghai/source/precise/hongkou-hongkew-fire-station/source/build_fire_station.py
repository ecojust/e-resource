"""Public street exterior of the 1917 Hongkew Fire Station at the Wusong–Wujin corner."""
from pathlib import Path
import json
import math
import sys

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

PARAM = json.loads((HERE/'parameters.json').read_bytes())
ID = PARAM['id']
META = dict(id=ID, name='虹口救火会临街旧楼与瞭望塔', status='photo-informed-partial-exterior',
            scope='Concave southwest gallery, two historic corner wings, public street returns and square masonry lookout. A long eastern street wing continues in the base city.',
            model_scope_zh='吴淞路560号沿街旧楼，四开间凹弧、两层敞廊、两端清水砖翼及其公共街面和方形瞭望塔。东向长翼余段沿用城市底图。',
            source_register='source/precise/'+ID+'/reference-review.json',viewer_page='hongkew-fire-station.html',
            audit_directory='data/audit/hongkew-fire-station-v1/',interiors_modeled=False,
            coordinate_convention='glTF +X across the southwest frontage towards Wujin Road, +Y up, +Z out towards the street. Origin at the midpoint of the concave facade chord.',
            map_reference_license='OpenStreetMap / Overture Maps, ODbL-1.0.',
            inscription_font_license='SIL Open Font License 1.1; Noto Serif CJK SC Regular subset.')
PAL = {
    'red facing brick':{'color':[.46,.156,.087],'roughness':.92},
    'brick accent':{'color':[.36,.105,.065],'roughness':.93},
    'pale stone':{'color':[.76,.70,.59],'roughness':.86},
    'stone bands':{'color':[.65,.602,.512],'roughness':.88},
    'white painted frame':{'color':[.76,.72,.645],'roughness':.68},
    'recessed glass':{'color':[.112,.166,.181],'roughness':.24,'metallic':.24},
    'dark opening':{'color':[.047,.065,.065],'roughness':.91},
    'gate red':{'color':[.43,.028,.022],'roughness':.64},
    'gate blue':{'color':[.052,.083,.36],'roughness':.61},
    'cast iron':{'color':[.10,.105,.092],'roughness':.55,'metallic':.42},
    'cornice letters':{'color':[.32,.23,.127],'roughness':.50,'metallic':.34},
    'roof membrane':{'color':[.25,.253,.241],'roughness':.90},
    'roof tiles':{'color':[.435,.186,.117],'roughness':.86},
    'tower roof':{'color':[.24,.244,.218],'roughness':.68,'metallic':.13},
}
points = np.array(PARAM['source_uv_m'])
cut_x = PARAM['east_cut_x_m']
arc_span = 8.60
cornice = 13.65


def arc_y(x):
    # The intermediate source vertices resolve the recessed centre of the curved wall.
    return 6.62 - .03158*x*x + .031*x


def line_cut(a,b,x):
    return a + (b-a) * ((x-a[0])/(b[0]-a[0]))


def ring_box(builder,center,w,d,z,h,material,label):
    builder.box([center[0],center[1],z],[w,d,h],material,label=label)


def outer_pier(f,x,w,bottom,top,material='pale stone'):
    f.box(x,(top+bottom)/2,w,top-bottom,.37,.07,material,'stone pier')
    z=bottom+.40
    while z<top-.16:
        f.box(x,z,w+.035,.065,.43,.082,'stone bands','pier joints')
        z+=.49


def wing(f,bays,lod):
    step=f.length/bays
    xs=[(i+.5-bays/2)*step for i in range(bays)]
    for lower,upper,base,wh,mat in [(0,4.46,1.32,1.76,'pale stone'),(4.46,8.83,5.05,2.90,'red facing brick'),(8.83,13.30,9.43,2.65,'red facing brick')]:
        holes=[opening(x,base,min(1.72,step*.59),wh)for x in xs]
        face=f.wall(lower,upper,holes,material=mat)
        for h,x in zip(holes,xs):
            f.window(h,2,2,frame='white painted frame',trim=False)
            f.prism(h.buffer(.155,join_style='mitre').difference(h),-.10,.145,'pale stone','window surround')
            f.box(x,base-.10,h.bounds[2]-h.bounds[0]+.42,.16,.38,.10,'stone bands','projecting sill')
            if lower==4.46:f.box(x,base+wh+.13,h.bounds[2]-h.bounds[0]+.46,.15,.38,.09,'pale stone','window head')
        if lower==0:
            for h in [1.09,1.75,2.39,3.07,3.72,4.26]:
                f.prism(face.intersection(box(-f.length/2,h,f.length/2,h+.034)),.010,.032,'stone bands','base coursing')
        elif not lod:
            # Fine, short brick variations remain subordinate to the pale stone surrounds.
            for ix in range(bays*4):
                u=(ix+.5)*f.length/(bays*4)-f.length/2
                dz=lower+.3+.13*(ix%3)
                f.box(u,dz,.21,.06,.045,.006,'brick accent','brick variation')
    for x in [-f.length/2+.18,f.length/2-.18]:outer_pier(f,x,.36,0,13.32)
    for z,h,d in [(.23,.42,.23),(4.44,.21,.25),(8.88,.19,.20),(13.12,.18,.30),(13.40,.23,.38),(13.62,.16,.44)]:
        f.beam(z,h,d,material='pale stone',label='stone ledge')
    n=max(4,round(f.length/(.48 if lod else .33)))
    for i in range(n):f.box((i+.5-n/2)*f.length/n,13.20,.125,.15,.25,.16,'stone bands','cornice dentils')


def garage(f):
    w=f.length-.61
    hole=opening(0,.05,w,4.27)
    f.wall(0,4.70,[hole],thickness=.52,material='pale stone')
    f.prism(hole,-.32,-.26,'gate red','closed door leaf')
    f.box(0,.65,w-.04,1.16,.075,-.19,'gate blue','blue door foot')
    f.box(0,2.86,w-.23,2.47,.065,-.18,'recessed glass','upper door glazing')
    for t in [-.5,-.25,0,.25,.5]:f.box(t*(w-.11),2.16,.096,4.16,.095,-.10,'gate red','door stiles')
    for z in [1.33,2.19,3.09,4.12]:f.box(0,z,w-.1,.095,.11,-.097,'gate red','door crossbars')


def balcony(f,z,lod):
    f.box(0,z,f.length+.04,.22,1.84,-.65,'pale stone','balcony floor')
    f.box(0,z+.17,f.length+.026,.11,.29,.115,'stone bands','balcony plinth')
    f.box(0,z+1.04,f.length+.04,.14,.29,.115,'pale stone','balcony handrail')
    n=max(3,math.ceil(f.length/(.30 if lod else .23)))
    for i in range(n):
        x=(i+.5-n/2)*f.length/n
        f.box(x,z+.60,.105,.75,.15,.13,'white painted frame','open balusters')


def badge(f,z):
    f.box(0,z,.58,.66,.061,.22,'cast iron','balustrade badge')
    pts=[f.point(.195*math.cos(a),z+.25*math.sin(a),.262)for a in np.linspace(0,2*math.pi,23)]
    f.builder.tube(pts,.019,'stone bands',5,'Gallery/iron emblem rim')
    for u in [-.085,.085]:f.line((u,z-.12,.266),(0,z+.16,.266),.017,'stone bands',5,'emblem ribs')


def galleries(builder,lod):
    bays=np.linspace(-arc_span,arc_span,5)
    strips=np.linspace(-arc_span,arc_span,25 if not lod else 13)
    for i,(a,b)in enumerate(zip(bays,bays[1:])):
        f=Facade(builder,(a,arc_y(a)),(b,arc_y(b)),'Bay '+str(i+1));garage(f)
        back=Facade(builder,(a,arc_y(a)+1.54),(b,arc_y(b)+1.54),'Gallery back '+str(i+1))
        for bottom,top in [(4.68,8.93),(8.93,13.04)]:
            hole=opening(0,bottom+.26,min(2.15,back.length*.55),2.91)
            back.wall(bottom,top,[hole],thickness=.30,material='pale stone')
            back.window(hole,3,3,frame='cast iron',trim=False)
        for z in [4.76,8.97]:badge(f,z+.59)
    for i,(a,b)in enumerate(zip(strips,strips[1:])):
        f=Facade(builder,(a,arc_y(a)),(b,arc_y(b)),'Curved galleries')
        for z in [4.76,8.97]:balcony(f,z,lod)
        for z,h,d in [(12.94,.24,.42),(13.20,.35,.34),(13.52,.18,.52),(13.66,.10,.54)]:
            f.beam(z,h,d,material='pale stone',label='curved cornice')
        for q in ([-.25,.25] if not lod else [0]):f.box(q*f.length,13.38,.115,.14,.26,.12,'stone bands','cornice dentils')
    for x in bays:
        # Curved bracket under the upper cornice, applied at the four-bay division.
        f=Facade(builder,(x-.4,arc_y(x-.4)),(x+.4,arc_y(x+.4)),'Gallery divisions')
        for z in [4.55,8.78,12.78]:
            pts=[f.point(0,z-.61,-.26),f.point(0,z-.40,-.15),f.point(0,z-.17,.04),f.point(0,z,.18)]
            builder.tube(pts,.077,'stone bands',6,'Gallery divisions/brackets')
    for char,outline in lettering_shapes('HONGKOU FIRE STATION',7.32,.355,font=HERE/'fonts/HongkewCornice.otf'):
        if lod:
            outline=outline.simplify(.007,preserve_topology=True)
        cx=outline.centroid.x
        f=Facade(builder,(cx-.25,arc_y(cx-.25)),(cx+.25,arc_y(cx+.25)),'Street inscription')
        f.prism(affinity.translate(outline,xoff=-cx,yoff=13.145),.146,.181,'cornice letters','raised letters')


def hipped_roof(builder,x,y,w,d,z,rise,label):
    # Small, independently observed glazed/tiled roof volumes on the public front wings.
    a,b,c,e=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)]
    l=(x-w*.25,y,z+rise);r=(x+w*.25,y,z+rise)
    builder.add([a,b,c,e,l,r],[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],'roof tiles',label)
    builder.tube([l,r],.065,'roof tiles',8,label+'/ridge')


def tower(builder,lod):
    # The city outline supplies three outside sides of the square lookout projection.
    cx,cy=-1.03,18.48;w=4.82
    rect=np.array([(cx-w/2,cy-w/2),(cx+w/2,cy-w/2),(cx+w/2,cy+w/2),(cx-w/2,cy+w/2)])
    for j,(a,b) in enumerate(zip(rect,np.roll(rect,-1,axis=0))):
        f=Facade(builder,a,b,'Lookout '+str(j+1))
        windows=[]
        if j==0:windows=[opening(0,17.35,.92,2.35)]
        f.wall(13.52,26.85,windows,material='red facing brick')
        if windows:
            h=windows[0];f.window(h,2,3,frame='cast iron',trim=False)
            f.prism(h.buffer(.20,join_style='mitre').difference(h),-.09,.14,'pale stone','shaft window surround')
        for q in [-1,1]:outer_pier(f,q*(w/2-.15),.32,13.55,26.93)
        arch=opening(0,28.24,2.43,1.34,arch=1.22,segments=13 if lod else 27)
        bell_face=f.wall(26.85,32.55,[arch],material='pale stone')
        f.prism(arch,-.40,-.32,'dark opening','recessed arched light')
        for z in [27.48,27.95,28.48,29.00,29.54,30.08,30.62,31.16]:
            f.prism(bell_face.intersection(box(-w/2,z,w/2,z+.033)),.009,.033,'stone bands','dressed bell courses')

        # Mitred faces would otherwise place coincident skins at the square corners.
        # The dressed stone corner blocks stand ahead of both meeting wall ends.
        for side in [-1,1]:
            x=side*(w/2-.25)
            f.box(x,29.69,.54,5.61,.30,.135,'pale stone','stone belfry corner')
            for z in [27.75,29.05,30.05,31.03,31.83]:
                f.box(x,z,.57,.052,.31,.147,'stone bands','belfry corner joints')

        f.prism(arch.buffer(.135,join_style='mitre').difference(arch),0,.12,'stone bands','arched surround')
        f.box(0,28.88,.14,1.30,.19,-.12,'pale stone','arch mullion')
        for z,h,d in [(26.73,.24,.37),(27.05,.20,.31),(28.18,.15,.21),(30.67,.12,.18),(31.79,.13,.23),(32.24,.23,.36),(32.53,.21,.59)]:
            f.beam(z,h,d,material='stone bands',label='tower cornice')
    ring_box(builder,(cx,cy),5.37,5.37,32.68,.15,'roof membrane','Lookout/square roof')
    for a,b in zip(rect,np.roll(rect,-1,axis=0)):
        f=Facade(builder,a,b,'Lookout gallery')
        for i in range(9):f.box((i-4)*.54,33.11,.054,.79,.054,.12,'cast iron','roof rail posts')
        f.box(0,33.50,w+.15,.065,.065,.12,'cast iron','roof handrail')
    radius=1.55;angles=np.arange(6)*2*math.pi/6+math.pi/6
    ring=np.array([(cx+radius*math.cos(a),cy+radius*math.sin(a))for a in angles])
    for a,b in zip(ring,np.roll(ring,-1,axis=0)):
        f=Facade(builder,a,b,'Hexagonal lantern');hole=opening(0,33.31,.61,1.09)
        f.wall(32.73,34.75,[hole],thickness=.13,material='pale stone')
        f.window(hole,1,1,frame='cast iron',trim=False)
    brim=np.array([(cx+1.74*math.cos(a),cy+1.74*math.sin(a),34.78)for a in angles]);tip=(cx,cy,35.10)
    builder.add([*brim,tip],[(i,(i+1)%6,6)for i in range(6)],'tower roof','Lookout/low hexagonal cap')
    builder.tube([(cx,cy,35.04),(cx,cy,37.83)],.037,'cast iron',6,'Lookout/public roof finial')
    for a in angles[::2]:
        builder.tube([(cx+1.44*math.cos(a),cy+1.44*math.sin(a),34.78),(cx,cy,36.25)],.012,'cast iron',4,'Lookout/mast stays')


def assemble(builder,lod):
    cfront=line_cut(points[10],points[9],cut_x);cback=line_cut(points[3],points[4],cut_x)
    left,right=(-arc_span,arc_y(-arc_span)),(arc_span,arc_y(arc_span))
    spans=[(points[15],points[14],3,'Wusong Road'),(points[14],left,2,'West entrance wing'),
           (right,points[10],2,'East entrance wing'),(points[10],cfront,2,'Wujin return')]
    for a,b,n,name in spans:wing(Facade(builder,a,b,name),n,lod)
    galleries(builder,lod);tower(builder,lod)
    rear=[cfront,cback,points[3],points[2],points[1],points[0],points[18],points[17],points[16],points[15]]
    for a,b in zip(rear,rear[1:]):
        f=Facade(builder,a,b,'Retained edge')
        f.wall(.12,13.37,thickness=.20,material='red facing brick')
    pts=[points[15],points[14],left,*[(x,arc_y(x))for x in np.linspace(-arc_span,arc_span,25)[1:-1]],right,points[10],*rear]
    study=Polygon(pts)
    assert study.is_valid
    builder.plan_prism(study,0,.10,'stone bands','Front wings/footing')
    builder.plan_prism(study,13.42,13.58,'roof membrane','Front wings/flat terrace')
    for x,y,w,d,rise in [(-13.8,9.4,8.6,3.65,.93),(12,10.23,4.65,3.30,.91)]:
        ring_box(builder,(x,y),w-.18,d-.18,14.17,1.16,'pale stone','Terrace/low roof block')
        hipped_roof(builder,x,y,w,d,14.75,rise,'Terrace/visible tile roofs')


if __name__=='__main__':
    from final_preview import finish
    build(HERE,META,PAL,assemble)
    finish()
