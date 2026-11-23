"""Build the independently downloadable 1937 wall fragment and render both dated layouts from both stations."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import Builder, PALETTE
from service_materials import BRICK, FRAME
from side_return import READINGS, wall_segment
from wing_frame import WingFrame
from check_mesh import paired_edges
from render_wing_views import digest, engine, lighting, raster

CROPS = {'album':(303,590,403,644),'design':(72,197,150,245)}
SHADOW = 'Eves | unlit 1937 opening'
PANEL_PIXELS = {'album':[(347,604),(353,612),(351,616)],
                'design':[(121,212),(121,217),(93,209),(96,217)]}

def make_piece(frame, path):
    camera=frame.album
    def yz(uv):
        return camera.plane(uv,[0,0,0],[1,0,0])[1:]
    # Within the registered photograph, the frame head lies against the long dark rail.
    reading=np.array([yz(uv) for uv in READINGS['album_features']['dark_low_opening']])
    ymin=reading[[1,2],0].mean();ymax=reading[[0,3],0].mean()
    zmin=reading[[2,3],1].mean();zmax=reading[:2,1].mean()
    hole=box(ymin,zmin,ymax,zmax)
    # Ends follow the outer ends of the visible wall panel; the big neighbouring post is outside this panel.
    y0,y1=sorted(yz(uv)[0] for uv in [(315,613),(397,612)])
    rail_z=np.mean([yz(uv)[1] for uv in [(316,600),(386,600)]])
    b=Builder({**PALETTE,SHADOW:{'color':[.045,.044,.042],'roughness':.97}})
    coverage=box(y0,0,y1,max(rail_z+.055,zmax+.035))
    wall_segment(b,coverage.difference(hole),0,.20,BRICK,'album wall beside small low opening')
    wall_segment(b,box(y0,rail_z-.025,y1,rail_z+.075),-.036,.045,FRAME,'album horizontal band at the head')
    wall_segment(b,hole,.177,.196,SHADOW,'one undivided recessed dark opening')
    counts=[]
    for part in b.parts:
        pos=np.asarray(part['vertices']);tri=np.asarray(part['triangles'])
        _,index=np.unique(pos.round(7),axis=0,return_inverse=True)
        assert paired_edges(index[tri]),part['label']
        xyz=pos[tri]
        vol=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6)
        assert vol>0,part['label']
        counts.append({'label':part['label'],'triangles':len(tri),'volume_m3':vol,'closed_oriented':True})
    b.save(path,{'id':'sassoon-service-wing-west-return-c1937','source':READINGS['album']['archive'],
                 'observed':'One recessed dark opening beneath the horizontal band. The interior is unreadable.',
                 'extent':'West return fragment. Colour and wall thickness follow the larger service-wing reconstruction.',
                 'photos_embedded':False,'geometry_license':'MIT'})
    return dict(components=counts,source_file_sha256=READINGS['album']['image_sha256'],corners=READINGS['album_features']['dark_low_opening'],
                wall_world_axis='X=0, Y into the wing, Z up',hole_yz_bounds_m=list(hole.bounds),
                wall_y_bounds_m=[float(y0),float(y1)],head_rail_z_m=float(rail_z),raw_sha256=digest(path))

def compare(restored, out):
    out.mkdir(parents=True,exist_ok=True);frame=WingFrame();fragment=out/'west-return-1937.glb'
    metadata=make_piece(frame,fragment)
    strips={};checks={}
    import runpy
    helper=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        lib=lighting['make_library'](Path(tmp))
        for model_path,key in [(fragment,'album_layout'),(restored,'design_layout')]:
            scene=runpy.run_path(str(helper))['SerialScene'](model_path)
            checks[key]={}
            for station,pixels in PANEL_PIXELS.items():
                camera=getattr(frame,station)
                checks[key][station]=[{'pixel':uv,'material':(scene.ray(camera.C,camera.ray(uv),450) or {}).get('material')} for uv in pixels]
            del scene
            model=raster.read_glb(model_path)
            painter=lighting['MaterialPass'](lib,model[1],model[2]);a,r,d=lighting['sky_maps'](model[0],lib,raster)
            lib.set_sky(lighting['SAMPLES'],lighting['DEPTH_RESOLUTION'],raster.ptr(a),raster.ptr(r),raster.ptr(d))
            for station,crop in CROPS.items():
                camera=getattr(frame,station);p=camera.K@camera.R@np.column_stack([np.eye(3),-camera.C]);p[:2]+=.5*p[2]
                pic,_,stats=engine['sample_view'](model_path,model,painter,lib,p,crop,440,np.array([-.32,-.70,.65],dtype='float32'),None,2)
                strips[(station,key)]=pic.copy()
    assert all(p['material']==SHADOW for p in checks['album_layout']['album'])
    assert all(p['material']==BRICK for p in checks['design_layout']['album'])
    w=456;h=322
    sheet=Image.new('RGB',(w*2,h*2),'#e8e5dd');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',17,index=2)
    for col,(key,label) in enumerate([('album_layout','1937年照片中的小暗窗'),('design_layout','2014年方案中的两处开窗')]):
        for row,(station,view) in enumerate([('album','相册视角'),('design','设计透视视角')]):
            pic=strips[station,key];x=col*w+8;y=row*h+8;sheet.paste(pic,(x,y))
            draw.text((x,y+278),view+'  ·  '+label,font=font,fill='#292b28')
    figure=out/'west-return-comparison.jpg';sheet.save(figure,quality=93,subsampling=0)
    report=dict(fragment=metadata,main_design_mesh_sha256=digest(restored),cameras_sha256=digest(HERE/'wing-cameras.json'),
                crops=CROPS,layout_by_column=['1937 photograph, wall fragment','2014 design, complete model'],
                first_hit=checks,comparison_sha256=digest(figure),source_pixels_embedded=False)
    (out/'west-return-1937-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('restored',type=Path);parser.add_argument('output',type=Path)
    a=parser.parse_args();compare(a.restored,a.output)
