"""Arc-length coordinates on the surveyed street edges and an editable perforated shell."""
from pathlib import Path
from math import cos, sin, pi, ceil, radians
import json
import numpy as np
from photo_architecture import Facade

class StreetCorner:
    def __init__(self,builder):
        self.builder=builder
        self.reg=json.loads(Path(__file__).with_name('frontage-registration.json').read_bytes())
        self.center=np.array(self.reg['arc_center_m'])
        self.radius=self.reg['arc_radius_m']
        self.sweep=radians(self.reg['corner_sweep_deg'])
        self.length=self.sweep*self.radius
        self.origin=np.array(self.reg['south_tangent_m'])
        self.end=np.array(self.reg['east_tangent_m'])
        self.east=np.array(self.reg['east_street_direction'])
    def normal_at(self,s):
        theta=-pi/2+min(self.length,max(0.,s))/self.radius
        return np.array([cos(theta),sin(theta)])
    def xy(self,s,d=0):
        n=self.normal_at(s)
        if s<0:return self.origin+[s,0]+n*d
        if s>self.length:return self.end+self.east*(s-self.length)+n*d
        return self.center+n*(self.radius+d)
    def point(self,s,z,d):
        return [*self.xy(s,d),z]
    def flat(self,s,span,d,label):
        return Facade(self.builder,self.xy(s-span/2,d),self.xy(s+span/2,d),label)
    def shell(self,left,right,low,high,back,front,material,label,holes=(),resolution=.48):
        """Stitch the curved outer/inner skins, jambs and cut edges into one mesh."""
        if left>=right or low>=high or back>=front:raise ValueError('Empty street panel')
        # Keep the tangent joins and aperture edges as mesh columns. Openings are
        # stored as arc lengths along the registered façade, including on straight wings.
        cuts={left,right,*[s for s in (0.,self.length)if left<s<right]}
        zcuts={low,high}
        for x0,z0,x1,z1 in holes:
            cuts.update(v for v in (x0,x1)if left<v<right);zcuts.update(v for v in (z0,z1)if low<v<high)
        coarse=sorted(cuts);xs=[coarse[0]]
        for a,b in zip(coarse,coarse[1:]):
            levels=max(1,ceil((b-a)/resolution))if a<self.length and b>0 else 1
            xs.extend([a+(b-a)*i/levels for i in range(1,levels)]+[b])
        zs=sorted(zcuts)
        occupied=set()
        for i,(a,b) in enumerate(zip(xs,xs[1:])):
            for j,(lo,hi) in enumerate(zip(zs,zs[1:])):
                x=(a+b)/2;z=(lo+hi)/2
                if not any(x0<x<x1 and z0<z<z1 for x0,z0,x1,z1 in holes):occupied.add((i,j))
        verts=[];faces=[];lookup={}
        def vertex(i,j,skin):
            key=i,j,skin
            if key not in lookup:
                lookup[key]=len(verts);verts.append(self.point(xs[i],zs[j],front if skin else back))
            return lookup[key]
        for i,j in sorted(occupied):
            corners=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            faces.append([vertex(x,y,1)for x,y in corners])
            faces.append([vertex(x,y,0)for x,y in reversed(corners)])
            neighbours=[(i,j-1),(i+1,j),(i,j+1),(i-1,j)]
            for k,adj in enumerate(neighbours):
                if adj in occupied:continue
                x,y=corners[k];u,v=corners[(k+1)%4]
                faces.append((vertex(x,y,0),vertex(u,v,0),vertex(u,v,1),vertex(x,y,1)))
        if verts:self.builder.add(verts,faces,material,label)
