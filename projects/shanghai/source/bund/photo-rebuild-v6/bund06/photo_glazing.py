"""Real separate panes with manually registered, unmodified CC0 source pixels."""
from pathlib import Path
import json,hashlib
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import pieces
HERE=Path(__file__).resolve().parent

def homography(quad):
    a=[];b=[]
    for (u,v),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],quad):
        a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);b.extend([x,y])
    return np.r_[np.linalg.solve(a,b),1].reshape(3,3)

def geometry_digest(parts):
    h=hashlib.sha256()
    for p in parts:
        h.update(p['label'].encode());h.update(np.asarray(p['vertices'],dtype='<f8').tobytes());h.update(np.asarray(p['triangles'],dtype='<i8').tobytes())
    return h.hexdigest()

class RegisteredGlazing:
    def __init__(self):
        self.controls=json.loads((HERE/'photo-glass-controls.json').read_text())
        self.image=HERE/self.controls['image'];data=self.image.read_bytes()
        assert len(data)==self.controls['image_bytes'] and hashlib.sha256(data).hexdigest()==self.controls['image_sha256']
        self.windows={w['label']:w for w in self.controls['windows']};self.jobs=[];self.fallback=[]
    def panes(self,f,shape,label,rows,columns,depth):
        inner=shape.buffer(-min(.085,(shape.bounds[2]-shape.bounds[0])*.2),join_style=2)
        ix0,iz0,ix1,iz1=inner.bounds;ctl=self.windows.get(label)
        xf=ctl['vertical_boundaries_from_left'] if ctl else np.linspace(0,1,columns+1)
        yf=ctl['horizontal_boundaries_from_top'] if ctl else np.linspace(0,1,rows+1)
        x=[ix0+(ix1-ix0)*q for q in xf];y=[iz1-(iz1-iz0)*q for q in yf]
        cols=len(x)-1;rows=len(y)-1;polygons=[]
        for r in range(rows):
            for c in range(cols):
                def bx(k):return 0 if k in [0,cols] else .038 if ctl and k==ctl['heavy_mullion_column'] and r>=ctl['heavy_transom_boundary'] else .014
                def by(k):return 0 if k in [0,rows] else .035 if ctl and k==ctl['heavy_transom_boundary'] else .014
                l=x[c]+bx(c);right=x[c+1]-bx(c+1);top=y[r]-by(r);bottom=y[r+1]+by(r+1)
                pane=inner.intersection(box(l,bottom,right,top))
                for pi,p in enumerate(pieces(pane)):
                    if p.area<1e-8:continue
                    polygons.append(p);start=len(f.builder.parts);plabel=f'{label}-pane-r{r}-c{c}'
                    if pi:plabel+=f'-piece{pi}'
                    f.prism(p,-depth-.04,-depth-.02,'recessed glass',plabel)
                    selected=next((q for q in ctl['panes'] if q['row_from_top']==r and q['column_from_left']==c),None) if ctl else None
                    if selected and selected['selected']:
                        for part in f.builder.parts[start:]:self.jobs.append((f,part,(l,bottom,right,top),selected,depth))
                    else:self.fallback.append({'part':plabel,'reason':selected['fallback_reason'] if selected else 'No individually inspected clear photographic pane control; retained procedural glass'})
        # Single shared-node solid frame, including its own mullions and returns.
        frame=shape.buffer(-.018,join_style=2).difference(unary_union(polygons))
        f.prism(frame,-depth+.015,-depth+.085,'bronze window frame',label+'-continuous-frame-grid')
    def apply(self,b):
        before=geometry_digest(b.parts);records=[]
        for f,part,bounds,ctl,depth in self.jobs:
            l,bottom,right,top=bounds;h=homography(ctl['source_stored_quad_px'])
            def uv(p,h=h,l=l,bottom=bottom,right=right,top=top,f=f):
                p=np.asarray(p);u=float(np.dot(p-f.center,f.t));v=(top-p[2])/(top-bottom);s=(u-l)/(right-l)
                q=h@np.array([s,v,1]);x,y=q[:2]/q[2]
                return [x/5184,y/3456]
            b.photograph_parts(self.image,uv,lambda p,target=part:p is target,name='PhotoFacade_Bund06Glass',roughness=.48,orientation=self.controls['orientation'])
            corners=[uv(f.point(u,z,-depth-.02)) for u,z in [(l,top),(right,top),(right,bottom),(l,bottom)]]
            error=float(np.max(np.abs(np.asarray(corners)*[5184,3456]-ctl['source_stored_quad_px'])))
            assert error<1e-7
            records.append({'part':part['label'],'row_from_top':ctl['row_from_top'],'column_from_left':ctl['column_from_left'],'bounds_facade_u_z_m':bounds,'source_stored_quad_px':ctl['source_stored_quad_px'],'stored_uv_corners':corners,'corner_error_px':error})
        after=geometry_digest(b.parts);assert before==after
        return {'schema':'bund06-photo-pane-report-v1','source':{k:self.controls[k] for k in ['image','image_bytes','image_sha256','author','license','date','source_url','orientation','scope','limitations','control_method']},'controls_sha256':hashlib.sha256((HERE/'photo-glass-controls.json').read_bytes()).hexdigest(),'photo_material':'PhotoFacade_Bund06Glass','photographed_windows':len(self.windows),'photographed_panes':len(records),'procedural_fallback_panes':len(self.fallback),'geometry_unchanged_by_uv_assignment':True,'geometry_before_sha256':before,'geometry_after_sha256':after,'frame_or_stone_photographed':False,'original_image_reencoded':False,'panes':records,'fallback':self.fallback}
