"""Compare three registered photographs and component sections against an actual decoded GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PRECISE = HERE.parents[1]
sys.path[:0] = [str(HERE.parent/'source'),
    str(PRECISE/'xuhui-pathe-records-office/measurements/city-contact'),
    str(PRECISE/'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements')]
from glb_triangles import SerialScene
from render_riverfront_survey import load_raster, raster, perspective
import zhu_residence_roof as roof


def read(name):
    return json.loads((HERE/name).read_bytes())


def cameras():
    south = read('south-garden-two-view-registration.json')['cameras']
    world = read('east-porch-five-view-world.json')['world']
    q = world['axis_spacing_m']
    local = np.array([[0,1/q,0,-world['southern_column_Y']/q],
                      [-1/q,0,0,world['column_X']/q],[0,0,1/q,-world['sill_Z']/q],[0,0,0,1]])
    east = read('east-porch-three-photo-section.json')['cameras']['gao10']['P_oriented_native']
    return {'south05':np.array(south[0]['projection']), 'south13':np.array(south[1]['projection']),
            'east10': np.asarray(east) @ local}


def photograph_checks(scene):
    reference = read('roof-photographic-observations.json')['fixed_pixel_samples']
    types = {'cap':(roof.LIP,roof.BOARD,roof.TILE,roof.RIDGE), 'cream':(roof.PLASTER,),
             'opening':(roof.FRAME,roof.GLASS), 'frame':(roof.FRAME,), 'apron':(roof.APR,),
             'red_slope':(roof.TILE,roof.RIDGE,roof.LIP), 'eave':(roof.EAVE,roof.CONSOLE)}
    rows=[]
    for view,P in cameras().items():
        inverse = np.linalg.inv(P[:,:3]); eye = -inverse @ P[:,3]
        for part,pixels in reference[view].items():
            for uv in pixels:
                hit=scene.ray(eye, inverse @ [*uv,1.], 70.)
                rows.append({'camera':view,'feature':part,'pixel':uv,
                             'first':hit,'matches':bool(hit and hit['material'] in types[part])})
    return rows


def section_checks(scene,layout):
    _,caps,dormers=roof.roof_features(layout)
    rows=[]
    def cast(name,origin,normal,expected,length):
        first=scene.ray(origin,normal,length)
        rows.append(dict(feature=name,origin=list(origin),normal=list(normal),expected=expected,
                         first=first,matches=bool(first and first['material']==expected)))
    for window in dormers:
        label=window['label'];p=window['loc'];base=window['base'];height=window['height']
        half=window['width']/2;east=window['side']=='east'
        top=base+height;head=top-(.59 if east else .50);pier=.31 if east else .135
        normal=np.asarray(p(0,1,0))-p(0,0,0)
        def front(name,a,z,mat):
            cast(label+' '+name,p(a,-.38,z),normal,mat,.8)
        for t in (-.70,-.35,.35,.70):
            u=t*(half-pier-.052)
            for h in (.16,.28,.72,.88):
                front('glass',u,base+.192+(head-.052-base-.192)*h,roof.GLASS)
            front('head',u,top-.13,roof.PLASTER)
            front('fascia',u,top-.015,roof.BOARD)
        for sign in (-1,1):
            front('jamb',sign*(half-pier*.52),(base+head)/2,roof.PLASTER)
            front('sash stile',sign*(half-pier-.025),(base+head)/2,roof.FRAME)
        if window['lights']==2:
            for h in (.36,.75):
                front('muntin',0,base+.192+(head-.052-base-.192)*h,roof.FRAME)
        if east:
            for a in (-.22,.22):front('transom rail',a,base+.62,roof.FRAME)
        for u in (-.5,0,.5):
            cast(label+' tiled cap',p(u,.2,top+.75),(0,0,-1),roof.TILE,1.05)
    for name,a,b in caps:
        for t in (.23,.51,.78):
            xyz=np.array(a)*(1-t)+np.array(b)*t
            cast(name,xyz+[0,0,.60],(0,0,-1),roof.RIDGE,1.)
    line=roof.garden_eave_lines(layout)
    for i,(a,b) in enumerate(zip(line,line[1:])):
        start,end=np.array(a),np.array(b);axis=end-start;length=np.linalg.norm(axis);axis/=length
        inward=np.array([-axis[1],axis[0]])
        n=max(1,round(length/.58))
        for k in sorted(set((0,n//2,n-1))):
            t=(k+.5)/n
            hit=start*(1-t)+end*t+inward*.50
            cast('south cornice bracket',[*hit,layout['south_eave_z']-.38],(0,0,1),roof.CONSOLE,.60)
        for t in (.26,.71):
            hit=start*(1-t)+end*t-inward*.32
            cast('south cornice lip',[*hit,layout['south_eave_z']+.168],(*inward,0),roof.EAVE,.9)
    return rows


def aerial_checks(scene,layout):
    source=read('four-edition-original-roof-traces.json')
    scale=source['metres_per_pixel']; _,caps,_=roof.roof_features(layout)
    ridge_a,ridge_b=(np.array(p[:2]) for p in caps[0][1:])
    rows=[]
    for edition,item in source['editions'].items():
        lines=item['features']
        sw,se=np.array(lines['south_eaves']['pixels'])
        east=se-sw;east/=np.linalg.norm(east)
        north=np.array([east[1],-east[0]])
        def metric(px):
            v=scale*(px-sw)
            return np.array([-.20+v@east,layout['roof_south_y']+v@north])
        for key in ('south_eaves','north_eaves','west_eaves','main_ridge','east_split'):
            a,b=[metric(q) for q in np.array(lines[key]['pixels'])]
            for t in (.15,.30,.45,.60,.75,.90):
                xy=a+t*(b-a)
                # The rim pixels have a 2–4 px uncertainty. Move only those
                # interior material samples 1.1 m onto the photographed roof.
                offset={'south_eaves':(0,1.1),'north_eaves':(0,-1.1),
                        'west_eaves':(1.1,0)}.get(key,(0,0))
                point=xy+offset
                first=scene.ray([*point,19.],[0,0,-1],15.)
                hit_group=first['material'] if first else None
                record=dict(edition=edition,feature=key,along=t,trace_xy_m=xy.tolist(),
                            tested_xy_m=point.tolist(),first=first,
                            matches=hit_group in (roof.TILE,roof.RIDGE,roof.APR,roof.LIP))
                if key=='main_ridge':
                    direction=ridge_b-ridge_a
                    f=np.clip((xy-ridge_a)@direction/(direction@direction),0,1)
                    record['distance_to_model_ridge_m']=float(np.linalg.norm(xy-ridge_a-f*direction))
                rows.append(record)
    return rows


def make_board(mesh,output):
    cam=cameras()
    plate=Image.new('RGB',(1340,902),'#f6f1e8'); pen=ImageDraw.Draw(plate)
    def label(x,y,value,size,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
        pen.text((x,y),value,font=font,fill='#343330')
    label(40,19,'朱学仁住宅  ·  南园廊和东门上方的三扇老虎窗',30,True)
    label(41,65,'愚园路684号　｜　以完整模型投回刊载照片的视角，并从高处展示屋顶转折。',19)
    sun=np.asarray([.62,-.80,.75],dtype='f');sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    overview=perspective([36,-46,36],[9.4,5.0,9.4],1255,348,1620)
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for P,crop,width,x,y in [(overview,[0,0,1255,348],1255,42,109),
                                 (cam['south05'],[239,40,565,153],790,42,528),
                                 (cam['east10'],[362,9,450,73],392,900,492)]:
            image,_=raster(mesh,lib,width,P,crop,sun,angles)
            plate.paste(image,(x,y))
    label(43,457,'南北红瓦坡与西侧斜脊。东门上方的小窗位于北侧短灰坡，临门的玻璃可见中梃和横档。',18)
    label(43,821,'南园廊两道棚帽与方托檐，2013年9月26日摄影视角。',17)
    label(900,805,'东向老虎窗，图10的原模型投影。',17)
    label(43,863,'暗坡的截取限于照片可见区域；枝叶遮住的北部屋面未补绘窗扇。',16)
    plate.save(output,quality=90,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('result',type=Path)
    parser.add_argument('--board',type=Path)
    args=parser.parse_args()
    scene=SerialScene(args.mesh)
    photo=photograph_checks(scene)
    layout=json.loads((HERE.parent/'source/garden-layout.json').read_bytes())
    section=section_checks(scene,layout)
    aerial=aerial_checks(scene,layout)
    def counts(rows):return {'matches':sum(x['matches'] for x in rows),'total':len(rows)}
    results={'mesh':scene.asset,'triangles':len(scene.tri),'section_count':counts(section),'section_first_hits':section,
             'aerial_count':counts(aerial),'aerial_first_hits':aerial,
             'photos':{key:counts([r for r in photo if r['camera']==key]) for key in cameras()},
             'photograph_first_hits':photo,'evidence_sha256':hashlib.sha256((HERE/'roof-photographic-observations.json').read_bytes()).hexdigest()}
    if args.board:
        make_board(args.mesh,args.board)
        results['board_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.result.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(results['section_count'],results['photos'],results['aerial_count'])
