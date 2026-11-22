"""The twelve-pier building's street shops, number 204 gate, flat roof and rear outline."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient

HERE=Path(__file__).resolve().parent
DATA=HERE.parent/'measurements'
STONE='Street | washed grey stone'
GARLAND='Street | exposed stone edging'
SHADOW='Street | stone recess'
BAND='Street | weathered horizontal courses'
BRONZE='Shops | bronze facing'
RAIL='Shops | dark metal frame'
GLASS='Shops | dusk glass'
SIGN='Shops | blank enamel sign board'
PALE='Rear | grey-white stucco'
ROOF='Roof | grey waterproofing'
PLINTH='Street | pavement and granite'
PLAQUE='Portal | municipal tablet'
GREEN='Portal | enamel street number'
WHITE='Portal | raised white lettering'
SOFFIT='Portal | shaded soffit'
DARK='Rear | steel window shadow'

def finish(rgb):
    value=np.array(rgb)/255
    return {'color':np.where(value<=.04045,value/12.92,((value+.055)/1.055)**2.4).tolist(),'roughness':.84,'metallic':0.}
PALETTE={name:finish(color) for name,color in [
    (STONE,(164,155,143)),(GARLAND,(180,170,153)),(SHADOW,(125,116,103)),(BAND,(143,138,130)),
    (BRONZE,(69,57,48)),(RAIL,(49,50,49)),(GLASS,(65,76,79)),(SIGN,(41,43,43)),(PALE,(179,181,173)),
    (ROOF,(115,117,114)),(PLINTH,(139,138,129)),(PLAQUE,(181,185,176)),(GREEN,(44,99,77)),(WHITE,(224,224,206)),
    (SOFFIT,(103,101,94)),(DARK,(76,81,78))]}
PALETTE[GLASS]['roughness']=.35
PALETTE[PLAQUE]['texture']=str(HERE/'204-protection-tablet.png')

class Face:
    def __init__(self,b,start,end,name):
        self.b=b;self.o=np.array(start);delta=np.array(end)-self.o;self.length=np.linalg.norm(delta)
        self.u=delta/self.length;self.n=np.array([-self.u[1],self.u[0]]);self.name=name
    def xyz(self,x,z,d):
        p=self.o+self.u*x+self.n*d
        return (p[0],p[1],z)
    def solid(self,shape,front,rear,material,detail):
        if shape.is_empty:return
        if shape.geom_type!='Polygon':
            for g in shape.geoms:self.solid(g,front,rear,material,detail)
            return
        if shape.area<.000002:return
        self.b.prism(orient(shape,sign=1),-rear,-front,lambda x,z,y:self.xyz(x,z,-y),material,self.name+' | '+detail)
    def rect(self,left,bottom,right,top,front,rear,mat,name):
        if right>left and top>bottom:self.solid(box(left,bottom,right,top),front,rear,mat,name)

def glazing(face,row,band,lod):
    i=row['bay'];L=face.length
    l,r=np.multiply(row['opening_proportions'],L)
    modern=i<=2; lower=.09 if i in (5,8) else .23
    top=min(band-.43,row['glazing_head_m']);frame=BRONZE if modern else STONE
    head=band+.10
    field=box(-.025,0,L+.025,head)
    face.solid(field.difference(box(l,lower,r,top)),.42,.67,frame,'shop casing')
    if modern:
        for t in np.arange(.66,L,.83):
            face.rect(t,.015,t+.012,lower,.412,.437,RAIL,'vertical panel joint')
        face.rect(l-.05,top-.025,r+.05,top+.033,.358,.456,BRONZE,'opening drip')
    else:
        face.rect(l-.048,top+.055,r+.048,head-.21,.38,.459,RAIL,'sign frame')
        face.rect(l,top+.105,r,head-.267,.362,.393,SIGN,'recessed blank fascia')
        face.rect(l-.078,lower-.015,r+.078,lower+.044,.311,.461,BAND,'sill')
    if i==8:
        a,b=np.multiply(row['internal_divisions'],r-l)+l
        face.rect(a,lower,b,top,.436,.691,BAND,'stone between two entries')
        pieces=[(l,a),(b,r)]
    else:
        seams=[l,*[l+(r-l)*x for x in row['internal_divisions']],r]
        pieces=list(zip(seams,seams[1:]))
    for j,(a,b) in enumerate(pieces):
        recessed=i in (5,8) and (i==8 or j==1)
        d=.97 if recessed else .54
        face.solid(box(a,lower,b,top).difference(box(a+.038,lower+.047,b-.038,top-.054)),d-.061,d+.033,RAIL,'glazing bars')
        face.rect(a+.025,lower+.035,b-.025,top-.037,d+.01,d+.051,GLASS,'shop window')
        if recessed:
            face.rect(a,lower,b,lower+.055,.422,d+.03,PLINTH,'recessed doorway threshold')
            for x in (a,b-.034):face.rect(x,lower,x+.034,top,.423,d+.05,RAIL,'door jamb return')
    face.rect(.475,head-.16,L-.475,head-.074,.319,.479,BAND,'continuous fascia course')
    face.rect(.475,head-.073,L-.475,head,.291,.494,STONE,'fascia cap')

def polygonal_letter(face,points,front,material,name,size):
    face.solid(LineString(points).buffer(size,cap_style='flat',join_style='mitre'),front,front+.004,material,name)

def tablets(face,photo,k):
    # Both tablets are on the right pier in Gao Yihan's closer date. Gao Can's earlier photograph
    # shows a smaller 204 marker on the opposite side of the entrance.
    h=np.array(photo['local_P'])[:,[0,2,3]]
    def coord(u,v):
        s=np.linalg.solve(h,[u,v,1]);return k*s[:2]/s[2]
    def region(bounds):
        l,b=coord(bounds[0],bounds[3]);r,t=coord(bounds[2],bounds[1]);return l,b,r,t
    l,b,r,t=region([1464,2272,1519,2311])
    face.rect(l,b,r,t,.175,.257,GREEN,'204 street number enamel')
    digits=[[(1475.5,2280.5),(1476.9,2278),(1479.2,2277),(1481.1,2278.9),(1481.7,2281.1),(1476.8,2292.5),(1483.0,2292.5)],
            [(1487,2278),(1488.6,2277),(1490.4,2277.8),(1492.1,2281.4),(1493.2,2289.1),(1492.1,2292.6),(1490.2,2293),(1488.2,2291.2),(1486.8,2285.7),(1486.3,2280),(1487,2278)],
            [(1504.8,2293.1),(1502.2,2276.8),(1498.5,2288.5),(1505.4,2288.6)]]
    for digit,stroke in zip('204',digits):
        polygonal_letter(face,[coord(u,v) for u,v in stroke],.169,WHITE,'street number digit '+digit,.0058)
    l,b,r,t=region([1449,2365,1555,2462])
    face.rect(l-.008,b-.009,r+.008,t+.009,.185,.255,BAND,'heritage protection tablet mount')
    face.rect(l,b,r,t,.173,.193,PLAQUE,'municipal heritage plaque')
    part=face.b.parts[-1];vertices=np.array(part['vertices']);uv=np.column_stack(((vertices[:,:2]-face.o)@face.u-l,vertices[:,2]-b))
    uv/=np.array([r-l,t-b]);part['texcoords']=uv.tolist()

def street_gate(face,band,lod):
    source=json.loads((DATA/'204-front-metric-camera.json').read_text())
    k=face.length/source['width_m'];data=source['crown_relief']
    shape=lambda points:Polygon(np.asarray(points)*k)
    jambs=np.asarray(data['jambs'])*k;l=(jambs[0,0]+jambs[1,0])*.5;r=(jambs[2,0]+jambs[3,0])*.5
    n=17 if lod else 39
    front=np.array(data['front_edge'])*k
    f=np.polynomial.Polynomial.fit(front[:,0],front[:,1],2)
    xs=np.linspace(l,r,n);zs=f(xs);rim=np.column_stack((xs,zs))
    opening=Polygon([(l,-.15),(r,-.15),*rim[::-1].tolist()])
    extent=box(.487,0,face.length-.492,band+.085)
    holes=[shape(obs) for obs in data['ogees']];tablet=shape(data['centre'])
    field=extent.difference(opening).difference(tablet)
    for hole in holes:field=field.difference(hole)
    face.solid(field,.377,.555,STONE,'stone face around four blind ogees')
    for j,hole in enumerate(holes):
        face.solid(hole.buffer(.001),.541,.584,SHADOW,f'blind ogee {j+1} backing')
        face.solid(hole.buffer(.031,join_style='mitre').difference(hole),.334,.390,GARLAND,f'pointed niche {j+1} moulding')
    face.solid(tablet.buffer(.001),.525,.563,SHADOW,'recessed centre cartouche')
    face.solid(tablet.buffer(.026,join_style='mitre').difference(tablet),.344,.392,GARLAND,'central tablet edge')
    thickness=.105
    face.solid(Polygon([*rim.tolist(),*np.column_stack((xs,zs+thickness))[::-1].tolist()]),.302,.431,GARLAND,'projecting lower edge of segmental arch')
    face.solid(Polygon([*np.column_stack((xs,zs-.025)).tolist(),*np.column_stack((xs,zs+.029))[::-1].tolist()]),.337,.626,BAND,'inner arch fillet')
    face.solid(Polygon([*np.column_stack((xs,zs-.084)).tolist(),*np.column_stack((xs,zs+.005))[::-1].tolist()]),.555,1.04,SOFFIT,'visible recessed soffit')
    for x in (l-.045,r):face.rect(x,0,x+.047,max(0,min(f(x),band)),.387,1.04,BAND,'stone jamb facing')
    for j,(lo,hi,dy) in enumerate([(band-.24,band-.19,.341),(band-.165,band-.09,.302),(band-.077,band+.074,.269)]):
        face.rect(.475,lo,face.length-.475,hi,dy,.556,GARLAND if j==2 else BAND,'horizontal cornice '+str(j+1))
    tablets(face,source,k)
    return l,r

def cut_to_plinth(face,x0,x1,width,apex,spring):
    xx=np.linspace(x0,x1,25);m=(x0+x1)*.5
    zz=apex-(apex-spring)*((xx-m)/((x1-x0)*.5))**2
    arc=np.column_stack((xx,zz))
    return Polygon([(x0,-.12),(x1,-.12),*arc[::-1].tolist()]),arc

def parapet_and_rear(b,front,back,gate,opening,roof_z,lod):
    # The outer roof edge finishes immediately behind the brick facade. The folded outer line,
    # and the re-entrant courtyard ring, stay independent of a guessed full rectangle.
    from continental_street_wall import Bay
    offsets=[]
    for idx in range(len(front)-1):
        bay=Bay(idx)
        stations=np.linspace(0.,bay.width,7 if lod else 13)
        offsets.extend(np.asarray(bay.point(u,.812,roof_z)[:2]) for u in stations[int(idx>0):])
    rear=np.array(back)
    roof_ring=Polygon([*offsets,*rear[::-1]])
    b.plan_prism(orient(roof_ring,sign=1),roof_z-.205,roof_z,ROOF,'Flat roof | courtyard perimeter')
    # The right rear corner of the cadastral polygon meets the passage bay. Its rear opening
    # is displaced toward the court, as seen in the front photograph through the vaulted way.
    rear_segments=list(zip([offsets[0],*rear],[*rear,offsets[-1]]))
    mainrear=None;rear_interval=None
    for j,(a,c) in enumerate(rear_segments):
        face=Face(b,c,a,'Courtyard | wall '+str(j+1));length=face.length
        outline=box(0,.0,length,roof_z-.13)
        if j==3:
            left=.22;right=left+min(3.59,.41*length)
            cut,arch=cut_to_plinth(face,left,right,length,3.34,2.91)
            mainrear=face;rear_interval=(right,left);outline=outline.difference(cut)
            # The photograph from the court includes the stepped stone head and the nearest
            # section of the adjacent steel window on its right. The far end is outside the image.
            extra_l=right+.72;extra_r=extra_l+.93
            side_light=box(extra_l,.69,extra_r,3.11);outline=outline.difference(side_light)
            face.solid(side_light.difference(box(extra_l+.082,.77,extra_r-.079,3.036)),-.056,.158,BAND,'adjacent return window stone surround')
            face.rect(extra_l+.079,.764,extra_r-.077,3.04,.104,.181,GLASS,'adjacent courtyard glass')
            for zz in (.99,1.46,1.9,2.34,2.78):
                face.rect(extra_l+.08,zz,extra_r-.077,zz+.024,.078,.111,DARK,'courtyard glazing bar')
            face.rect(extra_l+.48,.76,extra_l+.513,3.03,.072,.11,DARK,'courtyard steel mullion')
            thick=np.array([0.,.052,.094,.139])
            depths=[(-.109,-.065),(-.145,-.09),(-.104,-.064)]
            for k,(low,high) in enumerate(zip(thick,thick[1:])):
                polygon=Polygon([*[(x,z+low) for x,z in arch],*[(x,z+high)for x,z in arch[::-1]]])
                face.solid(polygon,*depths[k],BAND if k==1 else STONE,'moulded rear arch fillet '+str(k+1))
            for x in [left-.23,right+.01]:
                face.rect(x,0,x+.22,2.985,-.072,.145,STONE,'rear arch pier')
                for z in [.69,1.23,1.87,2.52,2.91]:face.rect(x-.012,z,x+.232,z+.035,-.093,-.003,BAND,'stone joints')
            centre=(left+right)*.5
            panel=Polygon([(left-.10,3.31),(right+.10,3.31),(right+.10,3.70),(centre+1.17,3.70),(centre+1.17,4.09),(centre-1.17,4.09),(centre-1.17,3.70),(left-.10,3.70)])
            face.solid(panel,-.067,.022,PALE,'stepped parapet panel over courtyard arch')
            for z,width in [(3.70,1.87),(4.09,1.18)]:face.rect(centre-width,z,centre+width,z+.062,-.084,.012,BAND,'stepped courtyard doorway cornice')
            # One broad, three-light window directly over the rear arch is visible in figure 16.
            midpoint=(left+right)/2
            aperture=box(midpoint-1.39,4.90,midpoint+1.39,7.16);outline=outline.difference(aperture)
            face.solid(aperture.difference(box(midpoint-1.32,4.98,midpoint+1.32,7.08)),-.014,.24,BAND,'rear steel window outer frame')
            for col in range(3):
                u0=midpoint-1.32+col*.88;face.rect(u0,4.98,u0+.88,7.08,.12,.155,GLASS,'rear passage upper light')
                face.rect(u0+.026,4.99,u0+.051,7.07,.092,.13,DARK,'rear steel upright')
            for h in (5.42,5.92,6.43,6.79):face.rect(midpoint-1.32,h,midpoint+1.32,h+.034,.092,.135,DARK,'rear horizontal steel rail')
            face.solid(Polygon([*arch.tolist(),*[(q[0],q[1]+.129) for q in arch[::-1]]]),-.094,.146,STONE,'rear arch crown')
            face.rect(left-.19,3.583,right+.19,3.68,-.092,.12,BAND,'rear doorway string')
        face.solid(outline,0,.236,PALE,'courtyard return and eaves')
        face.rect(0,roof_z-.12,length,roof_z+.108,-.066,.26,BAND,'rear coping')
    left,right=opening;ends=[mainrear.xyz(u,0,.14)[:2] for u in rear_interval]
    for i,(x,finish) in enumerate(zip((left,right),ends)):
        start=gate.xyz(x,0,.985)[:2]
        side=Face(b,start,finish,'204 passage');side.rect(0,0,side.length,3.005,-.012,.089,SOFFIT,'passage sidewall '+str(i+1))
    floor=Polygon([gate.xyz(left,0,.41)[:2],gate.xyz(right,0,.41)[:2],ends[1],ends[0]])
    b.plan_prism(orient(floor,sign=1),-.052,.01,PLINTH,'204 passage | paved floor')
    ceiling=Polygon([gate.xyz(left,0,1.015)[:2],gate.xyz(right,0,1.015)[:2],ends[1],ends[0]])
    b.plan_prism(orient(ceiling,sign=1),3.47,3.63,SOFFIT,'204 passage | ceiling beyond the street arch')

def add_shops_and_roof(builder,lod=False):
    obs=json.loads((DATA/'street-shops-roof-and-passages.json').read_text())
    layout=json.loads((DATA/'street-frontage-layout.json').read_text())
    front=np.asarray(layout['pier_tip_axes_m'],float)
    for i,row in enumerate(obs['ground_bays']):
        glazing(Face(builder,front[i],front[i+1],f'Storefront {i+1:02d}'),row,layout['height_m']['band'],lod)
    gate=Face(builder,front[-2],front[-1],'204 passage')
    opening=street_gate(gate,layout['height_m']['band'],lod)
    parapet_and_rear(builder,front,obs['rear_ring_N_to_S'],gate,opening,layout['roof_finished_above_street_m'],lod)
