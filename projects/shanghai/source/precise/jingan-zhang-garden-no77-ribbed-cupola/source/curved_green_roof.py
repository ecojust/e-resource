"""Source-based front half of the green ribbed roof at No. 77, Shanghai's Zhang Garden."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image

ID='jingan-zhang-garden-no77-ribbed-cupola'
METAL='Weathered green roof sheet';SEAM='Raised dark green standing seam';JOINT='Horizontal sheet lap'
STONE='Cream drum';PANEL='Recessed panel face';SHADOW='Underside of the cornice';EDGE='Bronze-coloured edge'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [
 (METAL,[1,1,1],.72),(SEAM,[.064,.238,.190],.74),(JOINT,[.132,.367,.289],.78),
 (STONE,[.73,.647,.527],.91),(PANEL,[.597,.524,.414],.9),(SHADOW,[.35,.287,.236],.91),(EDGE,[.24,.21,.164],.78)]}
# Roof radius as a function of height, obtained from the visible side and crown.
PROFILE=[(.0,1.),(.19,.984),(.40,.944),(.60,.883),(.78,.790),(.91,.666),(.974,.515),(1.,.34),(1.01,.16),(1.012,.035)]
R=1.63;BASE=1.02;RISE=1.33
def point(a,nr,z):
    return R*nr*sin(a),-R*nr*cos(a),z
def texture():
    p=Path(__file__).with_name('green-sheet.png')
    if not p.is_file():
        rng=np.random.default_rng(615);y,x=np.mgrid[0:320,0:480]
        waves=5.1*np.sin(2*pi*x/9.8)+1.9*np.sin(2*pi*x/4.9)
        variation=waves+rng.normal(0,3,x.shape)+rng.normal(0,2,(1,x.shape[1]))+2.4*np.cos(x/65-y/120)
        rgb=np.array([101,151,131])+variation[:,:,None];Image.fromarray(rgb.clip(0,255).astype('u1')).quantize(119).save(p)
    PALETTE[METAL]['texture']=str(p)
def radius_at(h):return np.interp(h,[p[0]for p in PROFILE],[p[1]for p in PROFILE])
def add_building(b,far=False):
    texture();limit=1.52;n=30 if far else 60
    angles=np.linspace(-limit,limit,n+1)
    def curved(levels,angle_range,mat,label):
        v=[point(a,r,z)for z,r in levels for a in angle_range]
        m=len(angle_range);faces=[]
        for j in range(len(levels)-1):
            for i in range(m-1):
                k=j*m+i;faces.append((k,k+1,k+m+1,k+m))
        b.add(v,faces,mat,label)
    curved([(0.,.918),(.605,.918),(.71,.931),(.842,.936),(.935,.974)],angles,STONE,'Visible front of cylindrical drum')
    for angle in np.linspace(-1.294,1.294,5):
        spread=.224;xs=np.linspace(angle-spread,angle+spread,7 if far else 11)
        curved([(.193,.921),(.503,.921)],xs,PANEL,'Inset rectangular panel face')
        for t in [.178,.503]:
            curved([(t,.922),(t+.024,.932),(t+.043,.924)],xs,STONE,'Narrow moulding above or below the inset')
        for edge in xs[[0,-1]]:
            curved([(.182,.932),(.536,.932)],np.array([edge-.01,edge+.01]),STONE,'Upright end of panel')
    for z,r,thick,mat,label in [(.098,.934,.048,STONE,'Lower drum moulding'),(.736,.958,.048,SHADOW,'Shadow under dentils'),(.826,.985,.072,STONE,'Rounded stone bed below roof'),(.906,1.014,.053,EDGE,'Metal strip at eaves'),(.958,1.006,.06,JOINT,'Turned foot of copper sheets')]:
        curved([(z,r-.024),(z+.009,r),(z+thick,r),(z+thick+.012,r-.016)],angles,mat,label)
    for a in np.linspace(-1.465,1.465,33):
        curved([(.757,.974),(.829,.974)],np.array([a-.018,a+.018]),STONE,'Small tooth under the top moulding')
    levels=[(BASE+h*RISE,rad)for h,rad in PROFILE]
    curved(levels,angles,METAL,'Shallow ribbed sheet roof cut at the sides')
    roof=b.parts[-1]
    roof['texcoords']=[[(a+limit)/(2*limit),1-h/1.013]for h,r in PROFILE for a in angles]
    for a in [-1.38,-.9,-.42,.09,.61,1.12]:
        pts=[point(a,rad+.004,z)for z,rad in levels]
        b.tube(pts,.019 if far else .025,SEAM,sides=6 if far else 10,label='Curved raised standing seam')
    for h in [.22,.46,.695,.89]:
        rad=radius_at(h);b.tube([point(a,rad+.001,BASE+h*RISE)for a in angles],.008,JOINT,sides=5 if far else 8,label='Horizontal panel overlap')
    # The photographed cap is a short bare metal pipe with a flared foot.
    q=np.linspace(-pi,pi,22 if far else 38)
    curved([(2.354,.07),(2.429,.052),(2.47,.04),(2.685,.04),(2.69,.032)],q,SEAM,'Central pipe with flared base')
    top=[point(a,.032,2.69)for a in q[:-1]];b.add(top,[(0,i,i+1)for i in range(1,len(top)-1)],SEAM,'Capped central pipe')
