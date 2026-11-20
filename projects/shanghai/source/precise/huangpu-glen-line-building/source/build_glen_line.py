"""Model the east front and southeast corner of Shanghai's Glen Line Building."""
import json,math,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering
P=json.loads((HERE/'parameters.json').read_bytes())
ID=P['id'];FONT=HERE/'fonts/GlenRegisterSubset.otf'
META={'id':ID,'name':'格林邮船大楼（外滩28号临江正面与东南街角）','status':'photo-informed-partial-exterior',
      'scope':'The river-facing east frontage, rounded Beijing East Road corner, street return and stepped crown of the Glen Line Building.',
      'model_scope_zh':'中山东一路28号临江五轴立面、北京东路2号东南圆角与沿街近段、凸窗、高壁柱、石栏和收分多边形塔冠。西翼与其余屋面保留城市底图。',
      'viewer_page':'glen-line-building.html','audit_directory':'data/audit/glen-line-building-v1/',
      'coordinate_convention':'glTF X north along the front, Y up, Z east toward the river.',
      'source_register':'source/precise/'+ID+'/reference-review.json','map_reference_license':'OpenStreetMap / Overture Maps, ODbL-1.0.',
      'inscription_font_license':'SIL Open Font License 1.1, Noto Serif CJK SC subset','interiors_modeled':False}
PAL={'ashlar':{'color':[.483,.444,.378],'roughness':.89},'limestone':{'color':[.537,.486,.399],'roughness':.88},
     'carved pale stone':{'color':[.662,.589,.475],'roughness':.84},'upper stone':{'color':[.396,.363,.303],'roughness':.9},
     'stone joint':{'color':[.341,.314,.262],'roughness':.93},'bronze window frame':{'color':[.126,.129,.104],'metallic':.26,'roughness':.47},
     'recessed glass':{'color':[.123,.175,.192],'metallic':.24,'roughness':.28},'deep transom':{'color':[.115,.105,.078],'roughness':.61},
     'dark bronze':{'color':[.253,.181,.110],'metallic':.46,'roughness':.42},'letter brass':{'color':[.350,.235,.152],'metallic':.37,'roughness':.53},
     'wrought iron':{'color':[.142,.146,.134],'metallic':.42,'roughness':.56},'roof':{'color':[.292,.264,.213],'roughness':.91}}
# Main front starts just north of its rounded southeast return.
AXES=np.array([-4.48,-.68,1.46,3.60,7.48])-1.505
ROWS=[(5.03,2.52),(9.80,2.34),(13.67,2.41),(17.61,1.93),(22.88,2.15)]


class Corner(Facade):
    def __init__(self,b,label):
        super().__init__(b,[-8.80,3.83],[-5.61,0],label)
        self.length=5.52

    def point(self,u,z,d=0):
        a=(u/self.length+.5)*math.pi/2
        c,s=math.cos(a),math.sin(a)
        norm=np.array([-3.83*c,-3.19*s,0.]);norm/=np.linalg.norm(norm)
        return np.array([-5.61-3.19*c,3.83-3.83*s,z])+norm*d

    def prism(self,poly,back,front,material='limestone',label='wall'):
        # Keep a faceted, rounded masonry corner in the silhouette. Each strip
        # preserves the same continuous unwrapped window and arch opening.
        if poly.is_empty:return
        low,_,high,_=poly.bounds
        cuts=sorted(set([low,high,*[u for u in np.linspace(-self.length/2,self.length/2,7)if low<u<high]]))
        for a,c in zip(cuts,cuts[1:]):
            band=poly.intersection(box(a,-2,c,48))
            if not band.is_empty and band.area>1e-7:
                self.builder.prism(band,back,front,self.point,material,self.label+'/'+label)

    def box(self,u,z,w,h,depth=.3,d=0,material='carved pale stone',label='trim'):
        self.prism(box(u-w/2,z-h/2,u+w/2,z+h/2),d-depth/2,d+depth/2,material,label)


def cornice(f,z,profile,material='carved pale stone'):
    for delta,height,project in profile:
        f.beam(z+delta,height,project,material,label='projecting stone cornice')


def stone_rail(f,u,z,width,lod):
    f.box(u,z,width,.13,.54,.16,'carved pale stone','balcony floor')
    f.box(u,z+.56,width,.105,.44,.21,'carved pale stone','balcony handrail')
    n=max(2,round(width/.55))
    for k in range(n+1):
        x=u-width/2+k*width/n
        f.box(x,z+.29,.075,.53,.30,.20,'limestone','stone railing post')
    for k in range(n):
        x=u-width/2+(k+.5)*width/n;w=width/n
        for sign in [-1,1]:
            f.line((x+sign*w*.36,z+.10,.21),(x-sign*w*.36,z+.50,.21),.034,'carved pale stone',5 if lod else 7,'crossed stone baluster')


def archivolt(f,x,base,w,h,lod):
    spring=base+h-w/2
    segments=9 if lod else 15
    for k in range(segments):
        lo=k*math.pi/segments+.008;hi=(k+1)*math.pi/segments-.008
        outer=w/2+(.27 if k!=segments//2 else .38)
        poly=Polygon([(x+r*math.cos(a),spring+r*math.sin(a))for r,a in ((w/2,lo),(w/2,hi),(outer,hi),(outer,lo))])
        f.prism(poly,-.006,.149 if k!=segments//2 else .21,'carved pale stone','radial keyed voussoir')


def ground(f,axes,main,lod):
    doors=[];windows=[]
    for i,x in enumerate(axes):
        if main and i in (1,2,3):
            w=1.54 if i==2 else 1.32;door=opening(x,.175,w,3.29)
            doors.append((x,door))
        else:
            w=1.61 if main else min(1.72,f.length*.58/len(axes));h=2.65
            windows.append((x,w,h,opening(x,.48,w,h,w/2,14 if lod else 26)))
    holes=[s for _,s in doors]+[s for *_,s in windows]
    f.wall(.13,4.77,holes,.48,'ashlar')
    free=unary_union([s.buffer(.115)for s in holes])
    for k in range(7):
        lo=.18+k*.612
        f.prism(box(-f.length/2,lo,f.length/2,lo+.563).difference(free),-.025,.080 if k%2 else .105,'limestone','coursed rustic ashlar')
    for x,w,h,s in windows:
        f.window(s,3,3,trim=False,label='arched ground sash')
        archivolt(f,x,.48,w,h,lod)
    for x,s in doors:
        f.window(s,2,2,frame='dark bronze',label='inset river entrance')
        for sign in (-1,1):
            f.box(x+sign*.21,1.38,.031,.46,.12,-.09,'letter brass','door pulls')
    if main:
        for x in [(axes[1]+axes[2])/2,(axes[2]+axes[3])/2]:
            xy=f.point(x,0,.19)
            f.builder.lathe(xy[:2],[(.17,.251),(.32,.251),(.42,.198),(.49,.185),(3.56,.173),(3.62,.205),(3.79,.242)],
                            'carved pale stone',12 if lod else 24,'East entrance/paired stone supports')
            f.box(x,3.84,.55,.17,.54,.18,'carved pale stone','column abacus')
        x=axes[2]
        f.box(x,3.76,6.09,.30,.64,.13,'carved pale stone','three-door lintel')
        # Scalloped centre nameplate and arched stone surround over the middle portal.
        plaque=opening(x,3.80,1.87,1.17,.61,16 if lod else 26)
        f.prism(plaque,-.02,.20,'upper stone','central doorway cartouche')
        f.prism(plaque.buffer(.13).difference(plaque),.14,.29,'carved pale stone','cartouche surround')
        for sg in (-1,1):
            xx=x+sg*1.36;f.box(xx,4.14,.38,.21,.44,.13,'carved pale stone','cartouche shoulder')
    cornice(f,4.38,[(0,.15,.23),(.18,.16,.31),(.33,.11,.38)])


def body(f,axes,main,lod):
    # The two middle tiers at the centre project from the wall as a canted oriel.
    rows=ROWS[:4]
    tasks=[]
    for j,(base,height)in enumerate(rows):
        for i,x in enumerate(axes):
            w=(1.32 if i in (0,4)else 1.16)if main else min(1.4,f.length*.49/len(axes))
            if main and i==2 and j in (2,3):continue
            tasks.append((x,j,w,opening(x,base,w,height)))
    f.wall(4.70,20.86,[q[3]for q in tasks],.44,'limestone')
    for x,j,w,s in tasks:
        f.window(s,2 if lod else 3,3 if j!=3 else 2,trim=False,label='street sash and reveal')
        f.box(x,s.bounds[3]+.09,w+.22,.14,.26,.045,'limestone','window head')
        if j in (1,2) and (not main or abs(x)>3):
            f.box(x,s.bounds[1]-.26,w+.17,.14,.28,.10,'carved pale stone','sill block')
        if j==0:
            stone_rail(f,x,4.54,w+.39,lod)
    if main:
        c=AXES[2]
        # Vertical, canted return surfaces have their own real panes, rather
        # than a shallow panel pasted over a flat centre window.
        outline=[(c-1.06,0),(c-.72,-.43),(c+.72,-.43),(c+1.06,0)]
        for a,b in zip(outline,outline[1:]):
            a=(a[0]+1.505,a[1]);b=(b[0]+1.505,b[1]);o=Facade(f.builder,a,b,'East/canted oriel')
            hs=[opening(0,base,max(.20,o.length-.19),h)for base,h in [ROWS[2],ROWS[3]]]
            o.wall(13.31,20.37,hs,.14,'limestone')
            for s in hs:o.window(s,1 if o.length<.8 else (2 if lod else 3),2,trim=False,label='canted oriel glazing')
            for z in (13.29,13.51,16.39,17.19,20.12):
                o.beam(z,.16,.24,label='oriel stone apron')
        for q in (.71,.45,.26):
            z=13.18-(.72-q)*.64
            f.box(c,z,q*2,.15,.52,.14,'carved pale stone','oriel corbel')
        for u in [(axes[0]+axes[1])/2-.07,(axes[3]+axes[4])/2+.07]:
            f.box(u,14.23,.72,10.63,.30,.10,'limestone','two giant flat pilaster shafts')
            f.box(u,14.18,.53,9.70,.13,.26,'upper stone','recessed pilaster face')
            f.box(u,19.75,.88,1.19,.44,.15,'carved pale stone','carved capital field')
            for off in (-.24,.24):
                pts=[f.point(u+off+.10*math.cos(t),20.03+.11*math.sin(t),.405)for t in np.linspace(0,math.tau,10 if lod else 18)]
                f.builder.tube(pts,.055,'limestone',5 if lod else 7,'East giant order/scrolls')
            for k in range(3):
                f.box(u,19.44+k*.20,.64-.10*k,.08,.13,.405,'limestone','relief blocks')
            for off in (-.39,.39):
                for step in range(4):
                    f.box(u+off,19.11+step*.33,.17,.17,.18,.285,'limestone','capital side blocks')
            for z,w in [(9.48,.96),(9.71,.84),(20.39,1.04),(20.59,1.19)]:
                f.box(u,z,w,.13,.55,.19,'carved pale stone','pilaster course and abacus')
        f.box(c,9.10,8.76,.63,.50,.12,'carved pale stone','present clearing-house frieze')
        add_facade_lettering(f,'SHANGHAI CLEARING HOUSE',c,9.10,8.29,.34,.381,.416,'letter brass',label='present English inscription',font=FONT)
    cornice(f,8.73,[(0,.13,.22),(.58,.20,.33)])
    cornice(f,20.77,[(0,.21,.31),(.23,.22,.51),(.51,.20,.83),(.77,.20,.91),(.96,.13,.79)])
    for k in range(max(3,round(f.length/.56))):
        n=max(3,round(f.length/.56));u=((k+.5)/n-.5)*f.length
        f.box(u,21.10,.235,.24,.60,.27,'carved pale stone','dentil course')


def attic(f,axes,lod):
    hs=[opening(x,22.38,min(1.26,f.length*.61/len(axes)),2.04)for x in axes]
    f.wall(21.74,25.65,hs,.39,'upper stone')
    for x,s in zip(axes,hs):
        f.window(s,2 if lod else 3,3,trim=True,label='attic sash')
        stone_rail(f,x,21.95,s.bounds[2]-s.bounds[0]+.26,lod)
    for z,h,d in [(25.31,.18,.32),(25.68,.23,.60),(26.12,.23,.37),(26.31,.16,.50)]:
        f.beam(z,h,d,label='attic and parapet')


def setback_wings(b,lod):
    # Both recent oblique and frontal photographs show windows and iron rails
    # on the upper level behind the front attic, flanking the arched pavilion.
    for label,x0,x1,window_x in [('south',-6.73,-1.97,-5.03),('north',4.91,8.04,6.65)]:
        y0,y1=2.36,8.47
        outline=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for j,(a,e) in enumerate(zip(outline,outline[1:]+outline[:1])):
            f=Facade(b,a,e,'Upper setback/'+label+' '+str(j+1))
            apertures=[]
            if j==0:
                apertures=[opening(window_x-(x0+x1)/2,26.86,1.22,1.84)]
            elif (label=='north' and j==1) or (label=='south' and j==3):
                apertures=[opening(u,26.86,1.02,1.78) for u in (-1.42,1.42)]
            f.wall(26.30,29.07,apertures,.32,'upper stone')
            for opening_shape in apertures:
                f.window(opening_shape,2,3,trim=True,label='setback attic sash')
            for z,h,d in [(28.99,.14,.26),(29.18,.15,.37),(29.34,.11,.28)]:
                f.beam(z,h,d,label='upper setback cornice')
            if j==0 or (label=='south' and j==3) or (label=='north' and j==1):
                post_n=max(3,round(f.length/.48))
                for k in range(post_n+1):
                    u=f.length*(k/post_n-.5)
                    f.line((u,29.42,0),(u,29.94,0),.027,'wrought iron',5,'terrace rail uprights')
                    if k<post_n:
                        u1=u+f.length/post_n
                        f.line((u,29.55,0),(u1,29.86,0),.020,'wrought iron',5,'crossed terrace rail')
                        if not lod:f.line((u,29.86,0),(u1,29.55,0),.020,'wrought iron',5,'crossed terrace rail')
                for z in (29.53,29.93):
                    f.line((-f.length/2,z,0),(f.length/2,z,0),.031,'wrought iron',6,'terrace handrail')
        b.plan_prism(Polygon(outline),29.27,29.40,'roof','Upper setback/'+label+' terrace slab')


def crown(b,lod):
    c=1.47;plan=[(c-2.48,1.28),(c+2.48,1.28),(c+3.51,2.31),(c+3.51,6.09),(c+2.46,7.14),
                 (c-2.46,7.14),(c-3.51,6.09),(c-3.51,2.31)]
    poly=Polygon(plan)
    for j,(a,e)in enumerate(zip(plan,plan[1:]+plan[:1])):
        f=Facade(b,a,e,'Tiered crown/east arch' if j==0 else 'Tiered crown/canted returns')
        if j==0:
            s=opening(0,26.60,1.79,2.16,.86,14 if lod else 26)
            f.wall(26.21,29.55,[s],.33,'upper stone');f.window(s,3,3,trim=True,label='central pavilion arched sash')
        else:f.wall(26.21,29.55,[],.26,'upper stone')
        cornice(f,29.45,[(0,.17,.31),(.19,.11,.40)])
    for low,high,inset,mat in [(29.69,31.08,.16,'upper stone'),(31.04,31.20,.05,'carved pale stone'),
                                (31.20,31.53,.29,'upper stone'),(31.53,32.08,.42,'upper stone'),
                                (32.08,32.23,.35,'carved pale stone'),(32.23,33.24,.62,'upper stone'),
                                (33.24,33.41,.52,'limestone'),(33.41,33.82,.78,'upper stone'),
                                (33.82,34.77,.89,'upper stone'),(34.77,35.02,.76,'limestone'),
                                (35.02,35.13,.95,'roof')]:
        b.plan_prism(poly.buffer(-inset,join_style=2),low,high,mat,'Tiered crown/eight-sided masonry stages')
    fr=Facade(b,(c-2.47,1.43),(c+2.47,1.43),'Crown lettering')
    add_facade_lettering(fr,'上海清算所',0,30.40,4.17,.59,.035,.084,'letter brass',label='five characters',font=FONT)
    b.tube([[c,4.1,35.0],[c,4.1,39.78]],.040,'wrought iron',7 if lod else 11,'Tiered crown/flag mast')


def assemble(b,lod):
    p=np.array(P['study_uv_m']);plan=Polygon(p[:-1]);front=Facade(b,p[0],p[1],'East river front')
    curved=Corner(b,'Southeast corner')
    side=Facade(b,p[3],p[4],'South frontage');jog=Facade(b,p[4],p[5],'South setback')
    south=[-.24*side.length,.24*side.length]
    for f,axes,main in [(front,AXES,True),(curved,[0],False),(side,south,False),(jog,[0],False)]:
        ground(f,axes,main,lod);body(f,axes,main,lod);attic(f,axes,lod)
    link=Facade(b,p[5],p[6],'South short ashlar return')
    link.wall(.13,26.27,[],.24,'limestone')
    for z in (.8,1.4,2.0,2.6,3.2,3.8,4.46,8.73,9.31,20.77,21.28,21.74,25.68,26.24):
        link.beam(z,.09,.22,label='short return course')
    north=Facade(b,p[1],p[2],'North narrow return');north.wall(.12,26.27,[],.24,'limestone')
    back=Facade(b,p[2],p[3],'West study section');back.wall(.12,26.29,[],.18,'limestone')
    b.plan_prism(plan,0,.165,'ashlar','Building/ground footprint')
    b.plan_prism(plan,26.19,26.40,'roof','Building/flat roof west cutoff')
    setback_wings(b,lod)
    crown(b,lod)


if __name__=='__main__':
    from final_preview import finish
    build(HERE,META,PAL,assemble)
    finish()
