"""Read an uncompressed or independently decoded gatehouse GLB and cast recorded roof samples."""
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
sys.path[:0] = [str(HERE.parent / 'source'),
                str(PRECISE / 'xuhui-pathe-records-office/measurements/city-contact'),
                str(PRECISE / 'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements')]
from glb_triangles import SerialScene
from render_riverfront_survey import load_raster, raster, perspective
import hengchang_roof as roof

GLAZING = (roof.GLASS, roof.LIGHT)
CLAY = (roof.TILE, roof.CREST, roof.LEAD)
DOCUMENT = HERE / 'roof-and-upper-gutter-observations.json'
LAYOUT = HERE.parent / 'source/gatehouse-layout.json'


def audit_ray(scene, family, feature, origin, direction, materials, length, **extra):
    hit = scene.ray(origin, direction, length)
    return dict(family=family, feature=feature, origin=list(origin), direction=list(direction),
                expected=list(materials), matched=bool(hit and hit['material'] in materials),
                hit=hit, **extra)


def architectural_sections(scene):
    sections = []
    def test(feature, eye, direction, materials, length):
        sections.append(audit_ray(scene, 'section', feature, eye, direction, materials, length))
    # The four-light front and two-light returns are independently recognizable
    # through their glazing and fixed central bars in the winter street views.
    for x in (.99, 2.25, 3.72, 4.97):
        for z in (13.75, 14.45, 14.92):
            test('South cap glazing', (x, -.32, z + .041*x), (0,1,0), GLAZING, .9)
    for x in (1.61975, 2.9225, 4.22525):
        test('South cap mullion', (x,-.32,14.4+.041*x), (0,1,0), (roof.FRAME,), .9)
    for x, dx in ((-.35,1), (6.70,-1)):
        for y in (.88,1.92):
            for z in (13.95,14.58):
                test('Cap end glazing', (x,y,z+.041*x), (dx,0,0), GLAZING, 1.1)
    openings = [(6.74,7.38,12.55,13.69,1,0), (8.33,8.90,12.43,13.6,1,0),
                (9.01,11.93,12.29,13.59,3,.63), (13.22,15.90,12.67,13.49,3,0),
                (17.77,19.28,12.55,13.68,2,0), (21.20,22.17,12.55,13.67,2,0),
                (23.61,25.82,12.75,13.68,2,0), (27.50,32.73,12.73,13.62,3,.65),
                (34.86,35.72,12.51,13.50,1,0)]
    for n,(l,r,a,b,lights,projection) in enumerate(openings, 1):
        for j in range(lights):
            x=l+(r-l)*(j+.5)/lights
            for fraction in (.28,.72):
                test(f'Attic opening {n}, light {j+1}', (x,1.76-projection,a+(b-a)*fraction),
                     (0,1,0), GLAZING, .63)
        # A vertical section through the cap confirms the two projected windows.
        if projection:
            test(f'Attic opening {n}, metal hood', ((l+r)/2,1.82,b+.30),
                 (0,0,-1), (roof.IRON,), .45)
    for x in (7.32, 12.90, 19.62, 23.62, 31.42, 35.12):
        for y in (.85, 1.34, 3.18, 4.68, 6.57, 8.43, 10.78):
            # The two protruding window bays can overhang the highest front tiles.
            test('Visible tile field', (x,y,18), (0,0,-1), CLAY, 10)
        test('Main ridge', (x,5.85,18), (0,0,-1), (roof.CREST,), 8)
    for x in (1.2,3.35,5.28):
        for y,materials in ((.65,(roof.IRON,)),(2.45,(roof.IRON,)),
                            (4.2,CLAY),(7.58,CLAY),(12.40,(roof.IRON,)),(14.99,(roof.IRON,))):
            test('Separate projections and intermediate roof', (x,y,18), (0,0,-1), materials, 14)
    return sections


def photo_checks(scene, record, camera):
    p=np.array(camera, dtype=float)
    inverse=np.linalg.inv(p[:,:3])
    eye=-inverse @ p[:,3]
    front=record['sources']['front']
    samples = [('Four light glazing', front['roof_window_samples_native'], GLAZING),
               ('Lower red shoulder', front['original_tile_samples_native'], CLAY)]
    rows=[]
    for label, pixels, materials in samples:
        for pixel in pixels:
            rows.append(audit_ray(scene,'2018 photograph',label,eye,
                                   inverse @ [*pixel,1],materials,95,source_pixel=pixel))
    # Put the measured upper/lower thin edges on the corresponding model plane.
    # Edge rays may choose either adjoining face; quantify their distance as well.
    for label,y in (('attic_upper_gutter_front',1.88),('south_eave_front_lip',.35)):
        for pixel in front['original_xy'][label]:
            direction=inverse @ [*pixel,1]
            point=eye + direction*(y-eye[1])/direction[1]
            if label=='south_eave_front_lip':
                predicted=10.715
            else:
                predicted=13.805+.22*np.clip((13.4104-point[0])/2.3568,0,1)
            rows.append(audit_ray(scene,'2018 edge',label,eye,direction,
                                  (roof.EAVE,roof.LEAD,roof.TILE,roof.SOFFIT),95,
                                  source_pixel=pixel,edge_delta_z_m=round(float(point[2]-predicted),4)))
    return rows


def aerial_checks(scene, record):
    output=[]
    for edition, source in record['sources']['aerials'].items():
        traces={t['feature']:np.array(t['source_pixels'],dtype=float) for t in source['lines']}
        front=next(v for k,v in traces.items() if k.startswith('east_first_south_eave'))
        ridge=next((v for k,v in traces.items() if k.startswith('east_first_ridge')),None)
        north=traces['east_first_north_line']
        # Long north eaves set direction even if the leafy southern half is missing.
        east=north[1]-north[0]
        east/=np.linalg.norm(east)
        into=np.array([east[1],-east[0]])
        for feature,line,offset in [('south eaves',front,1.),('north eaves',north,-1.),
                                    ('ridge',ridge,0.)]:
            if line is None:
                continue
            for fraction in (.12,.28,.46,.62,.78,.88):
                pixel=line[0]*(1-fraction)+line[1]*fraction
                delta=(pixel-front[0])*record['sources']['scale_m_per_px_in_resampled_tile']
                x=6.34+np.dot(delta,east)
                y=.36+np.dot(delta,into)+offset
                row=audit_ray(scene,'dated aerial',feature,(x,y,19),(0,0,-1),
                              CLAY,15,edition=edition,source_pixel=pixel.tolist(),
                              inside_offset_m=offset)
                if feature=='ridge':row['northing_offset_to_crest_m']=round(float(y-5.85),3)
                output.append(row)
    return output


def rooftop_overview(scene):
    # Frame the surveyed roof materials. A complete tower with its back cover
    # needs a broader field than the facade views use.
    w,h=1260,365
    P=perspective([26,-28,62],[17,6,13],w,h,1100)
    ids=[i for i,name in enumerate(scene.materials) if name in roof.PALETTE]
    vertices=scene.tri[np.isin(scene.mi,ids)].reshape(-1,3)
    screen=vertices @ P[:,:3].T + P[:,3]
    xy=screen[:,:2]/screen[:,2,None]
    low,high=xy.min(axis=0),xy.max(axis=0)
    middle=(high+low)/2
    scale=min((w-55)/(high[0]-low[0]),(h-32)/(high[1]-low[1]))
    recenter=np.array([[scale,0,w/2-scale*middle[0]],
                       [0,scale,h/2-scale*middle[1]],[0,0,1]])
    return recenter @ P


def plate(mesh, output, camera, scene):
    board=Image.new('RGB',(1350,898),'#f7f4ec')
    pen=ImageDraw.Draw(board)
    def label(x,y,text,size,bold=False):
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
        pen.text((x,y),text,font=f,fill='#302f2c')
    label(40,20,'亨昌里　南口屋顶和东侧街屋',31,True)
    label(40,69,'原模型投影　｜　前后两处蓝灰平顶，中间接赭色屋面。东段披瓦后可辨九组阁楼窗。',18)
    light=np.array([.40,-.80,.83]);light/=np.linalg.norm(light)
    angles=[np.degrees(np.arctan2(light[0],light[1]))%360,np.degrees(np.arcsin(light[2]))]
    views=[(rooftop_overview(scene),[0,0,1260,365],1260,44,111),
           (np.array(camera),[115,0,1455,650],468,44,560),
           (np.array(camera),[1450,455,4460,1210],752,545,563)]
    with tempfile.TemporaryDirectory() as tmp:
        lib=load_raster(tmp)
        for p,crop,width,x,y in views:
            image,_=raster(mesh,lib,width,p,crop,light,angles)
            board.paste(image,(x,y))
    label(44,487,'现状屋顶　｜　屋面长轴与前后缘分期从航片描读，罩体与街屋的分界另参照2025年区政府俯照。',18)
    label(44,790,'弄口四格顶窗与短侧窗。',17)
    label(545,790,'赭瓦小披、凸窗和较高的薄檐。均按2018年2月原照视角投影。',17)
    label(44,848,'图内仅使用本项目原创模型及程序材质。街树、设备和远处另一幢的山墙未绘入。',16)
    board.save(output,quality=89,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--board',type=Path)
    args=parser.parse_args()
    record=json.loads(DOCUMENT.read_bytes())
    layout=json.loads(LAYOUT.read_bytes())
    scene=SerialScene(args.mesh)
    rows=architectural_sections(scene)+photo_checks(scene,record,layout['native_camera'])+aerial_checks(scene,record)
    groups={}
    for r in rows:
        counts=groups.setdefault(r['family'],{'matched':0,'total':0})
        counts['matched']+=r['matched']
        counts['total']+=1
    report={'mesh':scene.asset,'triangles':len(scene.tri),'sources_sha256':hashlib.sha256(DOCUMENT.read_bytes()).hexdigest(),'counts':groups,'rays':rows}
    if args.board:
        plate(args.mesh,args.board,layout['native_camera'],scene)
        report['plate_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.report.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    print(groups)
