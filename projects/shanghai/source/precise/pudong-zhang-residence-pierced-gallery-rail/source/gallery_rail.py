"""Open gallery panel at the Zhang residence; silhouette coordinates are measured from one front panel."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from shapely.affinity import affine_transform

ID = 'pudong-zhang-residence-pierced-gallery-rail'
RED = 'Weathered red ornament'
RIM = 'Dark red panel borders'
RAIL = 'Dark gallery handrail'
GILT = 'Lighter red ridge of the lower rail'
PALETTE = {RED:dict(color=[1,1,1],roughness=.84), RIM:dict(color=[1,1,1],roughness=.85), RAIL:dict(color=[1,1,1],roughness=.74), GILT:dict(color=[.292,.173,.122],roughness=.79)}
CENTRES=(-.735,-.245,.245,.735)
W=.345
H=1.25
BASE=.12

def texture():
    p=Path(__file__).with_name('red-surface-and-dark-rails.png')
    if not p.exists():
        g=np.random.default_rng(859); h,w=192,224
        coarse=np.asarray(Image.fromarray(g.integers(0,255,(27,34),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        speck=g.normal(0,5.2,(h,w))
        red=np.array([149,72,56])+(.22*coarse+speck)[:,:,None]
        dark=np.array([66,45,40])+(.102*coarse+speck*.64)[:,:,None]
        a=np.concatenate((red,dark),axis=1)
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(160).save(p)
    for m in (RED,RIM,RAIL): PALETTE[m]['texture']=str(p)

def ornament(far):
    # Coordinates on the original front-facing panel: 0 at centre, y increasing from the lower border.
    # One set of cubic Bezier branches made from the right half; the left half is reflected in the panel axis.
    count=5 if far else 11
    strokes=[]
    paths=[
      [(.00,.045),(.08,.07),(.19,.119),(.18,.18),(.168,.216),(.09,.222),(.115,.193)],
      [(.18,.18),(.26,.16),(.34,.208),(.357,.25),(.378,.292),(.344,.318),(.30,.295)],
      [(.038,.332),(.17,.35),(.30,.394),(.325,.454),(.34,.49),(.299,.518),(.252,.491)],
      [(.325,.454),(.399,.457),(.465,.49),(.46,.545)],
      [(.00,.344),(.04,.313),(.153,.298),(.12,.262),(.098,.237),(.012,.26),(.050,.280)],
      [(.00,.549),(.116,.562),(.284,.585),(.337,.631),(.363,.667),(.324,.692),(.28,.673)],
      [(.337,.631),(.403,.608),(.465,.627),(.467,.661)],
      [(.00,.720),(.097,.726),(.163,.756),(.161,.790),(.163,.817),(.08,.823),(.088,.797)],
      [(.161,.79),(.264,.797),(.355,.78),(.404,.805),(.46,.829),(.41,.857),(.355,.843)],
      [(.00,.858),(.08,.872),(.152,.901),(.183,.934),(.195,.953),(.147,.968),(.127,.950)],
      [(.182,.934),(.242,.947),(.324,.944),(.366,.918),(.395,.899),(.342,.890),(.321,.904)],
      [(.00,.089),(.119,.087),(.253,.074),(.335,.044),(.39,.018),(.431,.038),(.411,.053)]
    ]
    for sign in (-1,1):
        for pts in paths:
            points=[]
            for j in range(0,len(pts)-1,3):
                q=np.asarray(pts[j:j+4])
                for t in np.linspace(0,1,count,endpoint=False):
                    x,z=(1-t)**3*q[0]+3*(1-t)**2*t*q[1]+3*(1-t)*t*t*q[2]+t**3*q[3]
                    points.append((sign*x*W,z*H))
            points.append((sign*pts[-1][0]*W,pts[-1][1]*H))
            strokes.append(LineString(points).buffer(.0063,resolution=2 if far else 4))
        # Fine upright rods, interrupted by the centre bud and staggered scrolls.
        for x,lo,hi in ((.245,.345,.55),(.235,.55,.754),(.275,.168,.298)):
            strokes.append(LineString([(sign*x*W,lo*H),(sign*x*W,hi*H)]).buffer(.0042,resolution=2))
    for y in (.545,.716,.863,.328,.088):
        lo=(y-.036)*H; hi=(y+.038)*H
        strokes.append(Polygon([(0,lo),(-.026,(lo+hi)/2-.010),(-.018,hi-.020),(0,hi),(.018,hi-.020),(.026,(lo+hi)/2-.010)]))
    for z in (.097,.857):
        strokes.append(LineString([(-.49*W,z*H),(.49*W,z*H)]).buffer(.006,resolution=2))
    return unary_union(strokes)

def add_building(b,far=False):
    texture()
    for z,w,d,h,m,n in ((.045,2.02,.156,.078,RAIL,'Lower dark structural rail'),(.099,2.02,.117,.021,GILT,'Narrow upper face on lower rail'),(1.40,2.03,.134,.052,RAIL,'Dark handrail beneath the cap'),(1.443,2.06,.161,.039,RAIL,'Projecting handrail cap')):
        b.box((0,0,z),(w,d,h),m,label=n)
    for c in CENTRES:
        for x in (-.5*W,.5*W):
            b.box((c+x,0,BASE+H/2),(.017,.041,H+.020),RIM,label='Side of a narrow red pierced panel')
        for z in (BASE,BASE+H):
            b.box((c,0,z),(W+.016,.042,.024),RIM,label='Red end rail of the panel')
    panel=ornament(far)
    for i,c in enumerate(CENTRES):
        poly=affine_transform(panel,[1,0,0,1,c,BASE])
        parts=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
        for p in parts:
            b.prism(p,-.011,.011,lambda x,z,d:(x,-d,z),RED,f'Mirrored scrolls and central buds of panel {i+1}')
    for part in b.parts:
        if part['material'] in (RED,RIM,RAIL):
            s=.512 if part['material']==RAIL else .009
            part['texcoords']=[(s+.47*min(1,max(0,(x+1.05)/2.10)),.99-.98*min(1,max(0,z/1.48))) for x,y,z in part['vertices']]
