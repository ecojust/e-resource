"""Chongming Zunjing Pavilion: 2005 photo-informed exterior candidate, MIT.

Museum plan dimensions are constraints, not a surveyed wall-line registration.
Only the photographed south facade receives detailed openings; unseen faces
remain explicitly estimated. No source building is hidden by this export.
"""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

import numpy as np
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'common'))
from photo_architecture import Builder, Facade
from roof_helpers import RoofHelpers

ID = 'chongming-zunjing-pavilion'
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

class GlyphContours(BasePen):
    def __init__(self, glyphs):
        super().__init__(glyphs); self.paths=[]; self.current=[]
    def _moveTo(self,p): self.current=[p]
    def _lineTo(self,p): self.current.append(p)
    def _curveToOne(self,a,b,c):
        p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b);c=np.array(c)
        self.current.extend(tuple((1-t)**3*p+3*(1-t)**2*t*a+3*(1-t)*t*t*b+t**3*c) for t in np.linspace(0,1,9)[1:])
    def _qCurveToOne(self,a,b):
        p=np.array(self._getCurrentPoint());a=np.array(a);b=np.array(b)
        self.current.extend(tuple((1-t)**2*p+2*(1-t)*t*a+t*t*b) for t in np.linspace(0,1,9)[1:])
    def _closePath(self):
        if len(self.current)>2: self.paths.append(self.current)
        self.current=[]
    def _endPath(self): self._closePath()

class Pavilion(RoofHelpers):
    def __init__(self,lod=False):
        self.b=Builder(PALETTE);self.lod=lod;self.features=[]
        self.floor=.40;self.hx=9.80;self.hy=7.30
        self.lowerInner=(6.90,4.625)
        self.ux=7.65;self.uy=5.35;self.ridge=4.85;self.breaky=2.55
        self.font=TTFont(HERE/'plaque-glyphs.otf');self.glyphs=self.font.getGlyphSet();self.cmap=self.font.getBestCmap()
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
    def lower(self,field,s,t):
        u=2*s-1;ix,iy=self.lowerInner
        if field<2:x=u*(ix+(self.hx-ix)*t);y=(-1 if field==0 else 1)*(iy+(self.hy-iy)*t)
        else:x=(-1 if field==2 else 1)*(ix+(self.hx-ix)*t);y=u*(iy+(self.hy-iy)*t)
        return np.array([x,y,3.53+1.19*(1-t)**1.55+.38*t**3*abs(u)**8])
    def upper(self,field,s,t):
        u=2*s-1
        if field<2:
            y=self.uy*t;w=self.ridge+(self.ux-self.ridge)*max(0,(y-self.breaky)/(self.uy-self.breaky))
            return np.array([u*w,(-1 if field==0 else 1)*y,6.09+1.31*(1-t)**1.55+.42*t**3*abs(u)**8])
        x=self.ridge+(self.ux-self.ridge)*t;w=self.breaky+(self.uy-self.breaky)*t
        return np.array([(-1 if field==2 else 1)*x,u*w,6.09+1.31*(1-w/self.uy)**1.55+.42*t**3*abs(u)**8])
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
    def roofs(self):
        for tier,fn in [('lower',self.lower),('upper',self.upper)]:
            for field in range(4):self.roof_patch(lambda s,t:fn(field,s,t),tier,field)
        # Gable infills start exactly at the upper hip junction.
        base=self.upper(0,.5,self.breaky/self.uy)[2]-.075
        for side in [-1,1]:
            a=[side*self.ridge,-self.breaky];b=[side*self.ridge,self.breaky]
            f=Facade(self.b,a if side>0 else b,b if side>0 else a,f'upper-gable-{side}')
            outline=Polygon([(-self.breaky,base),(self.breaky,base)]+[(y,self.upper(0,.5,abs(y)/self.uy)[2]-.075) for y in np.linspace(self.breaky,-self.breaky,33)])
            f.prism(outline,-.07,.01,'dark timber','closed-curved-infill')
        # Real open ridge band, seen in the 2005 photograph; motifs simplified.
        f=Facade(self.b,[-self.ridge,0],[self.ridge,0],'ridge')
        for z in [7.47,7.66]:f.box(0,z,self.ridge*2,.065,.19,0,'ridge ceramic','coping')
        for x in np.arange(-self.ridge+.08,self.ridge-.08,.45 if self.lod else .18):
            f.box(float(x),7.56,.035,.15,.12,0,'ridge ceramic','openwork-post')
            if not self.lod:
                self.b.tube([[x-.07,0,7.52],[x,0,7.62],[x+.07,0,7.52]],.014,'ridge ceramic',5,'ridge/estimated-lozenge')
        for side in [-1,1]:
            self.b.tube([[side*(self.ridge+a),0,z] for a,z in [(0,7.48),(.13,7.60),(.18,7.77),(.30,7.88),(.38,7.83)]],.055,'ridge ceramic',10,'ridge/estimated-terminal')
    def column(self,x,y,top,label):
        self.b.lathe((x,y),[(self.floor-.015,.22),(self.floor+.04,.25),(self.floor+.15,.22),(self.floor+.18,.18)],'granite base',16,label+'/stone-foot')
        self.b.lathe((x,y),[(self.floor+.14,.155),(top-.1,.145),(top,.14)],'aged red brown timber',16,label+'/tapered-post')
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
    def walls(self):
        # Base and floor plates, but no navigable interior or invented fitout.
        self.box((0,0,.20),(18.65,14.4,.40),'granite base','documented-foundation')
        for i in range(3):
            height=.10*(i+1);self.box((0,-7.2-(3-i)*.28/2,height/2),(4.9,(3-i)*.28,height),'granite base',f'front-step-{i}')
        self.box((0,0,3.40),(13.8,9.25,.16),'dark timber','estimated-upper-floor')
        for y in [-6.725,6.725]:
            for i,x in enumerate([-9,-5.4,-1.8,1.8,5.4,9]):self.column(x,y,3.48,f'gallery/{y}/post-{i}')
        for x in [-9,9]:
            for i,y in enumerate([-3.36,0,3.36]):self.column(x,y,3.48,f'gallery/{x}/side-post-{i}')
        for edge in range(4):
            f=self.facade(9,6.725,edge,f'gallery-beam-{edge}');f.box(0,3.37,f.length,.22,.25,0,'aged red brown timber','continuous-tie')
            # Small observed geometric transom rhythm, not fictitious characters.
            for k,u in enumerate(np.arange(-f.length/2+.12,f.length/2-.12,.55)):
                pts=[f.point(u-.20,3.20,.10),f.point(u-.20,3.05,.10),f.point(u-.04,3.05,.10),f.point(u-.04,3.15,.10),f.point(u+.16,3.15,.10),f.point(u+.16,3.27,.10)]
                self.b.tube(pts,.022,'aged red brown timber',4,f'gallery/frieze-{edge}-{k}')
            for k,u in enumerate(np.linspace(-f.length/2+.25,f.length/2-.25,max(2,round(f.length/1.2)))):
                for j in range(2):f.box(float(u),3.47+j*.10,.32+j*.17,.09,.38+j*.10,.02,'aged red brown timber',f'gallery/bracket-{k}-{j}')
        front=self.facade(6.9,4.625,0,'south-lower')
        for side in [-1,1]:front.box(side*6.18,1.89,1.44,2.98,.25,-.11,'white lime plaster','side-wall')
        for center in [-3.6,0,3.6]:
            for j in range(4):
                u=center-1.35+j*.90
                front.box(u,.88,.85,.94,.12,0,'aged red brown timber','lower-door-panel')
                front.box(u,.88,.68,.73,.035,.075,'dark timber','recessed-door-field')
                for dx in [-.34,.34]:front.box(u+dx,.88,.026,.73,.032,.099,'worn timber edges','door-moulding')
                for z in [.515,1.245]:front.box(u,z,.68,.026,.032,.099,'worn timber edges','door-moulding')
                # Approximate lobed carving border; no claimed exact motif tracing.
                if not self.lod:
                    pts=[front.point(u+.23*math.cos(t),.85+.27*math.sin(t),.102) for t in np.linspace(0,math.tau,21)]
                    self.b.tube(pts,.012,'worn timber edges',5,'door/estimated-relief-border')
                self.lattice(front,u,1.38,.85,1.69,f'lower-door-{center}-{j}',cols=6,rows=12)
        for x in [-5.4,-1.8,1.8,5.4]:front.box(x,1.85,.16,2.9,.20,.02,'aged red brown timber','door-jamb')
        front.box(0,3.18,13.8,.25,.25,.02,'aged red brown timber','door-head')
        for edge in [1,2,3]:
            f=self.facade(6.9,4.625,edge,f'unobserved-lower-{edge}');f.wall(self.floor,3.48,[],.24,'white lime plaster')
            f.box(0,.55,f.length,.30,.27,-.10,'granite base','base-course')
            for u in np.arange(-f.length/2+.06,f.length/2,2.76):f.box(float(u),1.9,.12,3.0,.06,.025,'aged red brown timber','estimated-structure-post')
        # Upper front: three groups of four small lattice leaves, with boarded
        # end bays, following the photograph rather than repeating ground doors.
        upper=self.facade(6.9,4.625,0,'south-upper')
        upper.box(0,4.10,13.8,1.26,.22,-.10,'dark timber','concealed-intertier-wall')
        for side in [-1,1]:
            upper.box(side*5.52,5.39,2.76,1.50,.16,-.05,'aged red brown timber','boarded-end-bay')
            for u in np.linspace(side*5.52-1.30,side*5.52+1.30,9):upper.box(float(u),5.40,.035,1.42,.055,.055,'worn timber edges','board-edge')
        for center in [-2.76,0,2.76]:
            for j in range(4):
                u=center-1.035+j*.69
                upper.box(u,4.85,.65,.30,.10,.015,'aged red brown timber','upper-leaf-bottom-board')
                self.lattice(upper,u,5.02,.65,.91,f'upper-window-{center}-{j}',cols=6,rows=8)
        for z in [4.70,6.04]:upper.box(0,z,13.8,.15,.24,0,'aged red brown timber','upper-belt')
        for edge in [1,2,3]:
            f=self.facade(6.9,4.625,edge,f'unobserved-upper-{edge}');f.wall(3.48,6.12,[],.18,'aged red brown timber')
            for u in np.arange(-f.length/2+.08,f.length/2,.32):f.box(float(u),5.12,.025,1.88,.04,.025,'worn timber edges','estimated-boarding')
        self.plaques(self.facade(9,6.725,0,'south-gallery-sign'),upper)
    def glyph(self,f,text,u,z,height,material,label,vertical=False,depth=.192):
        step=height*1.17
        for index,ch in enumerate(text):
            pen=GlyphContours(self.glyphs);self.glyphs[self.cmap[ord(ch)]].draw(pen)
            geometry=Polygon()
            for contour in pen.paths:
                p=Polygon(contour)
                if not p.is_valid:p=p.buffer(0)
                geometry=geometry.symmetric_difference(p)
            if geometry.is_empty:continue
            xmin,ymin,xmax,ymax=geometry.bounds;scale=height/(ymax-ymin)
            from shapely.affinity import affine_transform
            cx=u if vertical else u+(index-(len(text)-1)/2)*step
            cz=z-index*step if vertical else z
            geometry=affine_transform(geometry,[scale,0,0,scale,cx-(xmin+xmax)/2*scale,cz-(ymin+ymax)/2*scale])
            f.prism(geometry,depth,depth+.012,material,label+f'/glyph-{index}')
    def plaques(self,lower,upper):
        upper.box(0,5.35,.86,1.40,.10,.13,'dark timber','vertical-plaque')
        upper.box(0,5.35,.72,1.26,.035,.187,'blue plaque','plaque-field')
        for x in [-.42,.42]:upper.box(x,5.35,.024,1.42,.035,.197,'gilt lettering','plaque-border')
        for z in [4.66,6.04]:upper.box(0,z,.86,.024,.035,.197,'gilt lettering','plaque-border')
        self.glyph(upper,'尊經閣',0,5.76,.30,'gilt lettering','name-plaque',vertical=True,depth=.207)
        lower.box(0,3.02,3.55,.42,.10,.14,'dark timber','historic-exhibition-sign')
        self.glyph(lower,'崇明民俗陳列',0,3.02,.27,'green lettering','historic-exhibition-label')
    def finish(self):
        self.walls();self.roofs()
        volumes=[]
        for part in self.b.parts:
            v=np.asarray(part['vertices']);t=np.asarray(part['triangles'])
            volume=float(np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6)
            if volume<0:part['triangles']=[tuple(reversed(f)) for f in part['triangles']];volume=-volume
            if volume<1e-11:raise ValueError(f'Non-solid authored component: {part["label"]}')
            volumes.append(volume)
        self.mark('positive_component_volumes',parts=len(volumes),minimum_m3=min(volumes))
        return self

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    model=Pavilion(args.lod).finish()
    metadata={'id':ID,'name':'崇明学宫尊经阁（2005年照片参照，待地理接入）','axis':'glTF X east / Y up / Z south; building-local axes, not surveyed alignment',
              'scope':'Standalone exterior candidate; no main-map source replacement or collision integration',
              'reference_date':'2005-09-02 (Commons page); EXIF/source date may differ, see register',
              'height_interpretation':'7.5m upper height is ambiguous; authored ridge/display height is an estimate, not a surveyed total',
              'unobserved_faces':'Rear and sides are estimated blank/planked closures, no invented repeated photo windows',
              'lod':args.lod,'copyright':'Original geometry/code MIT. Reference photograph Joshua Wickerham, CC BY-SA 2.0, not embedded. Noto Serif CJK glyphs SIL OFL 1.1.'}
    role='lod' if args.lod else 'raw'
    result=model.b.save(args.out/(ID+f'-{role}.glb'),metadata)
    (args.out/f'{role}-features.json').write_text(json.dumps({'features':model.features,'counts':dict(Counter(x['kind'] for x in model.features))},ensure_ascii=False,indent=2)+'\n')
    (args.out/f'{role}-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['bytes','triangles','parts','bounds_glb']}),flush=True)

if __name__=='__main__':main()
