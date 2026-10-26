"""Map only individually inspected CC0 glass panes, preserving original JPEG.

Every chosen glass pane has its own quadrilateral; the front-plane camera fit
is deliberately not applied through the external colonnade or onto sidewalls.
"""
from pathlib import Path
import hashlib,json
import numpy as np
HERE=Path(__file__).resolve().parent


def homography(quad):
    a=[];bb=[]
    for (u,v),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],quad):
        a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);bb.extend([x,y])
    return np.r_[np.linalg.solve(a,bb),1].reshape(3,3)


def register(builder,panes):
    controls=json.loads((HERE/'photo-glass-controls.json').read_text())
    image=HERE/controls['image'];raw=image.read_bytes()
    assert len(raw)==controls['image_bytes'] and hashlib.sha256(raw).hexdigest()==controls['image_sha256']
    out=[]
    for window in controls['windows']:
        # All arched fanlight sectors remain unprojected. Only body rectangles
        # with actual inspected glazing quadrilaterals are selected.
        candidates=[p for p in panes if p['label'].startswith(window['model_window_prefix']) and abs(p['polygon'].area-(p['bounds'][2]-p['bounds'][0])*(p['bounds'][3]-p['bounds'][1]))<1e-8]
        candidates.sort(key=lambda p:(-round(p['polygon'].centroid.y,7),p['polygon'].centroid.x))
        assert len(candidates)==len(window['panes']),(window['id'],len(candidates),len(window['panes']))
        for pane,ctl in zip(candidates,window['panes']):
            l,bot,r,top=pane['bounds'];f=pane['facade'];h=homography(ctl['source_stored_quad_px'])
            target=[p for p in builder.parts if p['label']==pane['label']];assert len(target)==1
            def uv(p,h=h,l=l,r=r,bot=bot,top=top,f=f):
                pu=float(np.dot(np.asarray(p)-f.center,f.t))
                q=h@np.array([(pu-l)/(r-l),(top-p[2])/(top-bot),1.])
                return [q[0]/q[2]/5184,q[1]/q[2]/3456]
            builder.photograph_parts(image,uv,lambda p:p is target[0],name='PhotoFacade_Bund09_RegisteredGlass',roughness=.42,orientation={'rawSize':[5184,3456],'exifOrientation':1,'uvConvention':'stored-pixels'})
            out.append({'part':pane['label'],'window':window['id'],'row_from_top':ctl['row_from_top'],'column_from_left':ctl['column_from_left'],'model_bounds_uz_m':[l,bot,r,top],'glass_depth_m':pane['glass_depth_m'],'frame_depth_m':pane['frame_depth_m'],'source_stored_quad_px':ctl['source_stored_quad_px'],'stored_uv_corners':[uv(f.point(u,z,pane['glass_depth_m'][1])) for u,z in [(l,top),(r,top),(r,bot),(l,bot)]]})
    return {'schema':'bund09-per-pane-photo-uv-evidence-v1','image':controls['image'],'image_bytes':len(raw),'image_sha256':controls['image_sha256'],'source_author':'Suicasmo','license':'CC0-1.0','source_date':'2025-05-01','source_url':controls['source_url'],'window_count':len(controls['windows']),'glazing_parts':len(out),'mapped_material':'PhotoFacade_Bund09_RegisteredGlass','source_pixels_resampled':False,'stone_or_frames_textured':False,'control_sha256':hashlib.sha256((HERE/'photo-glass-controls.json').read_bytes()).hexdigest(),'scope':controls['scope'],'per_pane':out}
