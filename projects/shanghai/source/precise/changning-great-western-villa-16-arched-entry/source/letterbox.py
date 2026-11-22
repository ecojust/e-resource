"""WQL's rectified slate relief, physical golden digits and the little projecting nameplate shelf."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.spatial import cKDTree
from photo_architecture import Facade
from shapely.geometry import box
from registration import C,HERE
DATA=json.loads((HERE.parent/'measurements/letterbox-relief.json').read_bytes())
from mailbox_material import STONE, TEXTURE
METAL='Black bronzed letter shelf'
EDGE='Worn gunmetal edge'
CORNERS=np.array(C['plaque_corners_enu'])
T=CORNERS[1]-CORNERS[0];WIDTH=np.linalg.norm(T);T/=WIDTH
Z=np.array([0,0,1.])
N=np.cross(T,Z)
HEIGHT=CORNERS[0,2]-CORNERS[3,2]
def pos(u,v,relief):return CORNERS[0]+T*WIDTH*u-Z*HEIGHT*v+N*relief
def uv_at(u,v,where='panel_rect'):
    x,y,a,b=DATA[where];w,h=DATA['atlas_size']
    return [(x+.5+u*(a-x-1))/w,(y+.5+v*(b-y-1))/h]
def relief(u,v):
    pts=np.stack([u.ravel()*WIDTH,v.ravel()*HEIGHT],axis=1);value=np.zeros(len(pts))
    def stroke(points,amplitude,spread):
        p=np.array(points);t=np.r_[0.,np.linalg.norm(np.diff(p,axis=0),axis=1).cumsum()]
        curve=PchipInterpolator(t,p)(np.linspace(0,t[-1],200))*[WIDTH,HEIGHT]
        distance=cKDTree(curve).query(pts)[0]
        return amplitude*np.exp(-.5*(distance/spread)**2)
    # Traces follow the three stems, the five petals and feather-shaped outer leaf in the rectified photograph.
    curves=[[(.48,.773),(.44,.69),(.348,.625),(.242,.575),(.239,.525)],
            [(.405,.77),(.397,.697),(.265,.637),(.126,.598),(.046,.537),(.061,.463)],
            [(.51,.77),(.55,.634),(.62,.533),(.752,.444),(.882,.367),(.939,.273)],
            [(.534,.772),(.60,.619),(.679,.52),(.80,.442),(.926,.367),(.96,.271)],
            [(.581,.77),(.644,.657),(.735,.617),(.847,.601),(.941,.604)],
            [(.64,.433),(.679,.397),(.69,.328),(.751,.265),(.838,.241),(.857,.154),(.93,.101)],
            [(.923,.039),(.889,.094),(.87,.149),(.837,.175)]]
    for i,curve in enumerate(curves):value+=stroke(curve,.009 if i<5 else .016,.009 if i<5 else .018)
    def oval(cx,cy,a,b,h):
        s=((u-cx)/a)**2+((v-cy)/b)**2
        return h*np.sqrt(np.maximum(0,1-s)).ravel()
    for cx,cy,rx,ry in [(.283,.452,.048,.048),(.351,.495,.053,.038),(.283,.550,.044,.044),(.208,.501,.059,.040),(.279,.502,.044,.032)]:
        value+=oval(cx,cy,rx,ry,.012)
    for x,y in [(.705,.601),(.771,.572),(.841,.558),(.914,.548)]:
        value+=oval(x,y,.053,.051,.011)
    cx,cy=DATA['medallion_center_uv'];rx,ry=DATA['medallion_radii_uv']
    rho=np.sqrt(((u-cx)/rx)**2+((v-cy)/ry)**2)
    value+=(-.0045*(rho<1)+.0215*np.exp(-((rho-1.30)/.184)**2)+.005*np.exp(-((rho-1.03)/.069)**2)).ravel()
    digits=np.array(Image.open(HERE/'gilt-digits.png'),float)/255
    imprint=map_coordinates(gaussian_filter(digits,.65),[v.ravel()*(digits.shape[0]-1),u.ravel()*(digits.shape[1]-1)],order=1)
    return value.reshape(u.shape)+imprint.reshape(u.shape)*.009
def plaque_mesh(b,lod):
    nx,ny=(36,54)if lod else(77,119)
    u,v=np.meshgrid(np.linspace(0,1,nx),np.linspace(0,1,ny))
    h=relief(u,v);verts=[];tex=[]
    for su,sv,sh in zip(u.ravel(),v.ravel(),h.ravel()):verts.append(pos(su,sv,sh));tex.append(uv_at(su,sv))
    faces=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;faces.extend([(a,a+nx,a+nx+1),(a,a+nx+1,a+1)])
    # Close the rear and the four returns. The back uses the same mapped stone edge.
    ids=[*range(nx),*[j*nx+nx-1 for j in range(1,ny)],*range(nx*ny-2,nx*(ny-1)-1,-1),*[j*nx for j in range(ny-2,0,-1)]]
    back=[]
    for idx in ids:
        back.append(len(verts));a=u.ravel()[idx];c=v.ravel()[idx];verts.append(pos(a,c,-.035));tex.append(uv_at(a,c))
    center=len(verts);verts.append(pos(.5,.5,-.035));tex.append(uv_at(.5,.5))
    for j,a in enumerate(ids):
        k=(j+1)%len(ids);s=ids[k];fa,fb=back[j],back[k]
        faces.extend([(a,s,fb,fa),(center,fa,fb)])
    b.add(verts,faces,STONE,'Letter box/stone field and raised gilt digits');b.parts[-1]['texcoords']=tex
def box_shelf(b,lod):
    # Two turned posts, the shallow tray and the proud bilingual bronze inscription.
    f=Facade(b,CORNERS[0,:2],CORNERS[1,:2],'Letter box')
    z0=CORNERS[3,2];z=z0+.033
    for i,off in enumerate([-.391,.391]):
        x=WIDTH*off
        f.box(x,z+.092,.041,.185,.044,.073,METAL,'rear strap '+str(i+1))
        p=f.point(x,z,.120);profile=[(z,.024),(z+.012,.031),(z+.022,.024),(z+.054,.016),(z+.060,.022),(z+.148,.019),(z+.160,.027),(z+.171,.019),(z+.184,.025),(z+.203,.017),(z+.209,.004)]
        b.lathe(p[:2],profile,METAL,segments=9 if lod else 19,label='Letter box/turned front post '+str(i+1))
    f.box(0,z,WIDTH*.93,.014,.146,.073,EDGE,'projecting bottom tray')
    f.box(0,z+.024,WIDTH*.87,.030,.027,.129,METAL,'tray front lip')
    f.box(0,z+.11,WIDTH*.747,.096,.024,.134,METAL,'front name rail')
    corners=[(-.34,.145),(.34,.145),(.34,.082),(-.34,.082)]
    verts=[f.point(k*WIDTH,z+oz,.148)for k,oz in corners]+[f.point(k*WIDTH,z+oz,.144)for k,oz in corners]
    b.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],STONE,'Letter box/bilingual name plaque')
    b.parts[-1]['texcoords']=[uv_at(i,j,'label_rect')for i,j in [(0,0),(1,0),(1,1),(0,1)]*2]
