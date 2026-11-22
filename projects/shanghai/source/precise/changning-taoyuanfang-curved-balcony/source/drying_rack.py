"""Four stainless drying poles on independently jointed scissor carriers."""
from pathlib import Path
import json
import numpy as np
from photo_architecture import Facade
from wrought_guard import ribbon
STEEL='Polished drying rod';DARK='Dark scissor steel';LITE='Light scissor steel';PIN='Aged pivot cap';END='Grey rod stopper'
def hardware(b,lod):
    f=Path(__file__).absolute().parent.parent/'measurements/drying-rack.json'
    r=json.loads(f.read_bytes());ends=np.array(r['rod_endpoints_xyz']);span=r['rod_spacing_m']
    for i,(start,stop)in enumerate(zip(*ends)):
        b.tube([start,stop],.0145,STEEL,sides=10 if lod else 20,label='Drying rack/steel pole %d'%(i+1))
        for j,(v,sgn)in enumerate([(start,-1),(stop,1)]):
            b.tube([v-[sgn*.019,0,0],v+[sgn*.006,0,0]],.016,END,sides=8 if lod else 16,label='Drying rack/steel pole %d end %d'%(i+1,j+1))
    for side,x in enumerate([-2.38,1.737]):
        y=ends[0,:,1];z=r['rod_height_m'];name='Folding carrier %d/'%(side+1)
        b.box((x,.5*(min(y)+max(y))+.06,z-.23),(.06,np.ptp(y)+.31,.042),DARK,label=name+'lower rail')
        # Four overlapping X-links run from the folding wall bracket out to the first rod.
        locations=np.r_[y,y[-1]+span]
        def member(y0,z0,y1,z1,xx,mat,label):
            start=np.array([xx,y0,z0]);stop=np.array([xx,y1,z1]);delta=stop-start
            t=delta/np.linalg.norm(delta);axis=np.array([1.,0.,0.]);up=np.cross(axis,t)
            b.box((start+stop)/2,[.019,np.linalg.norm(delta),.039],mat,[axis,t,up],label=name+label)
        for j,(u,v)in enumerate(zip(locations,locations[1:])):
            member(u,z+.018,v,z-.195,x-.014,LITE,'ascending crossed strap')
            member(u,z-.195,v,z+.018,x+.014,DARK,'descending crossed strap')
            for k,(a,h,rad)in enumerate([(u,z+.025,.026),(u,z-.195,.026),(.5*(u+v),z-.083,.018)]):
                endcap=.066 if j==3 and k==2 else .039
                b.tube([[x-endcap,a,h],[x+endcap,a,h]],rad,PIN,sides=9 if lod else 16,label=name+'pivot %d/%d'%(j+1,k+1))
            if not lod:b.box((x-.011,u,z+.008),(.035,.035,.057),'Clamp cast steel',label=name+'upper pole seat')
        for j,u in enumerate([y[0]-.025,y[1],y[2],y[-1]+.10]):
            b.box((x,u,z-.285),(.064,.046,.101),DARK,label=name+'small lower retainer')
        b.box((x,y[-1]+.14,z-.16),(.10,.08,.39),LITE,label=name+'end mounting plate')

        ybase=y[-1]+.10;rear=1.58
        b.box((x,(rear+ybase)/2,z-.24),(.062,rear-ybase,.071),DARK,label=name+'rear attachment runner')
        for j,u in enumerate(np.arange(ybase+.08,rear-.02,.14)):
            b.box((x,u,z-.161),(.042,.042,.139),LITE,label=name+'slotted return rib')
        if side==0:
            # The left folding unit is supported at the inside surface of the dividing cheek.
            for j,u in enumerate([y[1],y[-1]+.11]):
                b.box((-2.56,u,z-.24),(.40,.057,.061),DARK,label=name+'side return to partition')
                b.box((-2.754,u,z-.25),(.052,.085,.18),LITE,label=name+'wall fixing pad')
        else:
            b.box((x,rear+.018,z-.23),(.17,.055,.28),DARK,label=name+'back wall fixing plate')
