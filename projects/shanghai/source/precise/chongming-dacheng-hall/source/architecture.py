from collections import Counter
import math
import numpy as np
from shapely.geometry import Polygon
from common.photo_architecture import Builder, Facade
from roof_helpers import RoofHelpers
PALETTE = {
    'aged red brown timber': {'color':[.19,.045,.031], 'roughness':.76},
    'worn timber edges': {'color':[.26,.070,.046], 'roughness':.76},
    'dark timber': {'color':[.075,.022,.018], 'roughness':.9},
    'white lime plaster': {'color':[.77,.76,.69], 'roughness':.96},
    'granite base': {'color':[.47,.48,.45], 'roughness':.94},
    'stone joints': {'color':[.23,.24,.22], 'roughness':.98},
    'roof underlay': {'color':[.16,.18,.17], 'roughness':.96},
    'grey tile 0': {'color':[.25,.27,.25], 'roughness':.92},
    'grey tile 1': {'color':[.21,.23,.21], 'roughness':.94},
    'grey tile 2': {'color':[.30,.31,.28], 'roughness':.93},
    'ridge ceramic': {'color':[.32,.34,.31], 'roughness':.9},
    'interior shadow': {'color':[.012,.021,.019], 'roughness':1.},
    'blue plaque': {'color':[.015,.060,.085], 'roughness':.75},
    'gilt lettering': {'color':[.69,.49,.13], 'roughness':.62, 'metallic':.12},
    'green lettering': {'color':[.28,.42,.23], 'roughness':.8},
}
class Architecture(RoofHelpers):
    def mark(self,kind,**kw): self.features.append({'kind':kind,**kw})
    def box(self,c,s,material,label): self.b.box(c,s,material,label=label)
    def facade(self,hx,hy,edge,label):
        points=[[-hx,-hy],[hx,-hy],[hx,hy],[-hx,hy]]
        return Facade(self.b,points[edge],points[(edge+1)%4],label)
    def shell(self,vertices,quads,thickness,material,label):
        lookup={};unique=[];mapping=[]
        for v in vertices:
            key=tuple(np.round(v,10))
            if key not in lookup:lookup[key]=len(unique);unique.append(v)
            mapping.append(lookup[key])
        v=np.array(unique,float);tri=[]
        for face in quads:
            face=[mapping[i] for i in face]
            for k in range(1,len(face)-1):
                t=[face[0],face[k],face[k+1]]
                normal=np.cross(v[t[1]]-v[t[0]],v[t[2]]-v[t[0]])
                if np.linalg.norm(normal)<1e-10:continue
                if normal[2]<0:t.reverse()
                tri.append(tuple(t))
        n=len(v);vs=np.vstack([v,v-[0,0,thickness]])
        faces=tri+[tuple(i+n for i in t[::-1]) for t in tri]
        counts=Counter(tuple(sorted((a,b))) for t in tri for a,b in zip(t,t[1:]+t[:1]))
        for t in tri:
            for a,b in zip(t,t[1:]+t[:1]):
                if counts[tuple(sorted((a,b)))]==1:faces.append((b,a,a+n,b+n))
        self.b.add(vs,faces,material,label)
    def roof_patch(self,point,tier,field):
        n,nu=(5,12) if self.lod else (14,28)
        vs=[point(s,t) for t in np.linspace(0,1,n+1) for s in np.linspace(0,1,nu+1)]
        faces=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(n) for i in range(nu)]
        prefix=f'roof/{tier}/field-{field}'
        self.shell(vs,faces,.075,'roof underlay',prefix+'/closed-shell')
        coordinate_axis=0 if field<2 else 1
        width=lambda t:abs(point(1,t)[coordinate_axis])
        half=width(1);count=round(2*half/(.62 if self.lod else .23))
        for i in range(count):
            c=-half+(i+.5)*2*half/count
            start=0.
            if abs(c)>width(0):
                lo,hi=0.,1.
                for _ in range(25):
                    mid=(lo+hi)/2
                    if width(mid)<abs(c):lo=mid
                    else:hi=mid
                start=hi+.005
            if start>.97:continue
            def course(t):return point((c/max(width(t),1e-9)+1)/2,t)+[0,0,.045]
            pts=[course(t) for t in np.linspace(start,1,6 if self.lod else 15)]
            self.b.tube(pts,.057,f'grey tile {i%3}',6 if self.lod else 10,prefix+f'/parallel-cap-{i}')
            end=pts[-1];out=end-pts[-2];out/=np.linalg.norm(out)
            self.b.tube([end-out*.014,end+out*.055],.076,'ridge ceramic',8 if self.lod else 12,prefix+f'/round-tile-end-{i}')
            if not self.lod:
                for k,t in enumerate(np.linspace(start+.03,.97,max(1,round((1-start)*8)))):
                    p=course(t);direction=course(min(1,t+.003))-course(max(start,t-.003));direction/=np.linalg.norm(direction)
                    self.b.tube([p-direction*.009,p+direction*.009],.061,'grey tile 2',8,prefix+f'/tile-lap-{i}-{k}')
            self.mark('roof_tile_course',tier=tier,field=field)
        self.b.tube([point(s,1)-[0,0,.08] for s in np.linspace(0,1,21)],.075,'aged red brown timber',8,prefix+'/curved-fascia')
        for i,s in enumerate(np.linspace(.03,.97,10 if self.lod else 26)):
            self.b.tube([point(s,t)-[0,0,.16] for t in np.linspace(.35,1,8)],.035,'aged red brown timber',6,prefix+f'/under-eave-rafter-{i}')
        if field<2:
            start=0 if tier=='lower' else self.breaky/self.uy
            for side in [0,1]:
                pts=[point(side,t)+[0,0,.12] for t in np.linspace(start,1,15)]
                self.b.tube(pts,.10,'ridge ceramic',10,prefix+f'/hip-ridge-{side}')
                p=pts[-1];direction=np.array([-1 if side==0 else 1,-1 if field==0 else 1,0.]);direction/=np.linalg.norm(direction)
                self.b.tube([p+direction*a+[0,0,z] for a,z in [(0,0),(.12,.10),(.23,.26),(.29,.45)]],.046,'ridge ceramic',8,prefix+f'/upturned-terminal-{side}')
                if not self.lod:
                    for k,t in enumerate([.78,.87,.93]):self.beast(point(side,t)+[0,0,.16],prefix+f'/estimated-figure-{side}-{k}',.45)
    def lattice(self,f,u,bottom,width,height,label,cols=7,rows=11):
        # Four frame members surround a real open lattice, with no hidden wall
        # filling the aperture. A separate inset dark plane represents unseen interior.
        for x in [u-width/2+.035,u+width/2-.035]:f.box(x,bottom+height/2,.07,height,.11,.035,'worn timber edges',label+'/vertical-frame')
        for z in [bottom+.035,bottom+height-.035]:f.box(u,z,width-.14,.07,.11,.035,'worn timber edges',label+'/horizontal-frame')
        clearw=width-.14;clearh=height-.14
        for i in range(1,cols):f.box(u-clearw/2+clearw*i/cols,bottom+height/2,.018,clearh,.045,.04,'aged red brown timber',label+'/vertical-lattice')
        for i in range(1,rows):f.box(u,bottom+.07+clearh*i/rows,clearw,.018,.045,.04,'aged red brown timber',label+'/horizontal-lattice')
        f.box(u,bottom+height/2,width-.10,height-.10,.015,-.095,'interior shadow',label+'/recessed-interior-backing')
        self.mark('lattice_panel',label=label,grid=[cols,rows],clear_apertures=cols*rows,inset_backing_m=.095,facade={'a':f.a.tolist() if hasattr(f,'a') else None,'u':u,'bottom':bottom,'width':width,'height':height})
