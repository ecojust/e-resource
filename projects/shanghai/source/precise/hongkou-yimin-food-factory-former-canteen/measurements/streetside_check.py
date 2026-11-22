"""Cast source image rays and wall-normal probes at the original and independently decoded meshes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene, material_appearance

def read(path):
    return json.loads(path.read_bytes())

SURVEY = read(HERE / 'streetside-image-measurements.json')
LAYOUT = read(HERE.parent / 'source/hall-layout.json')
U = np.array(SURVEY['baseline_unit_east_north'])
NORMAL = np.array([-U[1], U[0]])
SCALE = LAYOUT['length'] / (56.0 - 2.7)
WIDTH = LAYOUT['width']

def survey_camera(view, pixel):
    """Map a ray to author coordinates using the surveyed common facade endpoints."""
    az, tilt = np.radians([view['bearing'], view['pitch']])
    width, height = view['frame_size']
    focal = width / (2 * math.tan(math.radians(view['horizontal_field_of_view'] / 2)))
    right, up = (pixel[0] - width / 2) / focal, (height / 2 - pixel[1]) / focal
    forward = np.array([math.sin(az), math.cos(az)])
    lateral = np.array([math.cos(az), -math.sin(az)])
    horizontal = (math.cos(tilt) - up * math.sin(tilt)) * forward + right * lateral
    vertical = math.sin(tilt) + up * math.cos(tilt)
    east_north = np.array(view['local_station_en_m'])
    origin = np.array([WIDTH - east_north @ NORMAL, (east_north @ U - 2.7) * SCALE, view['road_device_height_m']])
    direction = np.array([-horizontal @ NORMAL, (horizontal @ U) * SCALE, vertical])
    return origin, direction

def category(material):
    if material is None:
        return 'open'
    name = material.partition('|')[-1].strip()
    if any(term in name for term in ('wooden', 'bevelled', 'metal door pull')):
        return 'wooden door'
    if any(term in name for term in ('reflect', 'window glass', 'glazing', 'fixed frame', 'dark sash')):
        return 'fenestration'
    return 'masonry or trim'

def summarize(hit):
    return dict(material=hit['material'], point_m=np.round(hit['point_enu_m'], 4).tolist(), triangle=hit['triangle_index']) if hit else None

def inspect(path):
    scene = SerialScene(path)
    photo_rows, normals = [], []
    openings = {(r['number'],r['level']):r for r in LAYOUT['faces']['street']}
    for r in SURVEY['measurements']:
        opening = openings[r['axis'],r['level']]
        door = opening['kind']=='street-door'
        expected_class = 'wooden door' if door else 'fenestration'
        for pick in r['physical_reads']:
            if not pick['readable']:
                continue
            view = SURVEY['views'][pick['view']]
            origin, ray = survey_camera(view,pick['pixel'])
            hit = scene.ray(origin,ray,42)
            observation = summarize(hit)
            material = observation['material'] if observation else None
            photo_rows.append(dict(axis=r['axis'],level=r['level'],view=pick['view'],pixel=pick['pixel'],surface=observation,
                                   observed_class=expected_class,first_surface_class=category(material),same_class=category(material)==expected_class))
        for side in (-1,1):
            z = opening['sill'] + (.49 if door else .45)*(opening['crown']-opening['sill'])
            along = opening['center'] + side * opening['width'] * .24
            hit = scene.ray([WIDTH+1.5,along,z],[-1,0,0],2.6)
            label = 'Canteen | raised wooden door panels' if door else 'Canteen | '+('smoke grey reflective window glass' if r['level']=='upper' else 'shaded ground-floor window glass')
            normals.append(dict(axis=r['axis'],level=r['level'],side=side,expected_material=label,surface=summarize(hit),match=bool(hit and hit['material']==label)))
    return scene,dict(asset=scene.asset,image_rays=photo_rows,image_class_matches=sum(r['same_class'] for r in photo_rows),direct_mesh_probes=normals,
                      direct_mesh_matches=sum(r['match'] for r in normals))

def make_board(scene,path,output):
    colors=material_appearance(path)['materials']
    rgb={}
    for name,item in colors.items():
        v=np.array(item['baseColorFactor'][:3]);v=np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)
        rgb[name]=tuple(np.clip(np.rint(255*v),0,255).astype(int))
    scale=22;left=50;base=306;w=1340;canvas=Image.new('RGB',(w,424),(246,245,240));draw=ImageDraw.Draw(canvas)
    points=scene.tri
    # Render the entire independent mesh orthographically, with the normal of the road wall toward the viewer.
    visible=np.ptp(points[:,:,1],axis=1)*np.ptp(points[:,:,2],axis=1)>.00006
    for i in np.where(visible)[0][np.argsort(points[visible,:,0].mean(axis=1),kind='stable')]:
        face=points[i];poly=[(round(left+scale*y),round(base-scale*z)) for _,y,z in face]
        draw.polygon(poly,fill=rgb[scene.materials[scene.mi[i]]])
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    title=ImageFont.truetype(font_path,22);small=ImageFont.truetype(font_path,13)
    draw.text((left,13),'Yimin food factory  |  Former canteen along Xiangyanqiao Road',font=title,fill='#252a29')
    draw.text((left,44),'SW facade from the delivered mesh. Below: independently read camera rays on the mapped wall.',font=small,fill='#404947')
    palette={'upper':'#14788a','ground':'#b35d28'}
    draw.line((left,337,left+LAYOUT['length']*scale,337),fill='#999d96',width=1)
    for item in SURVEY['measurements']:
        y0=328 if item['level']=='upper' else 347
        xs=[left+(r['independently_read_wall_axis_m']-2.7)*SCALE*scale for r in item['physical_reads'] if r['readable']]
        if len(xs)==2:draw.line((min(xs),y0,max(xs),y0),fill=palette[item['level']],width=2)
        for x in xs:draw.ellipse((x-2,y0-2,x+2,y0+2),fill=palette[item['level']])
        if item['level']=='ground':
            x=left+(item['axis'] and next(q['center'] for q in LAYOUT['faces']['street'] if q['level']=='ground' and q['number']==item['axis']))*scale
            draw.text((x-5,355),str(item['axis']),font=small,fill='#202925')
    draw.text((left,389),'Blue: upper windows   |   Rust: street-level openings   |   6 and 7: two-leaf timber doors   |   NW at left, SE at right',font=small,fill='#37433b')
    canvas.save(output,quality=94)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('meshes',type=Path,nargs='+');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--board',type=Path)
    args=parser.parse_args();reports=[]
    for i,path in enumerate(args.meshes):
        scene,report=inspect(path);reports.append(report)
        if i==0 and args.board:make_board(scene,path,args.board)
        print(path.name,report['direct_mesh_matches'],len(report['direct_mesh_probes']),report['image_class_matches'],len(report['image_rays']))
        del scene
    out=dict(method='Image rays use the measured camera frame, heading, altitude and two surveyed facade endpoints. They retain street geolocation and small facade-depth errors; actual masonry hits remain in the results. Separate wall-normal pane and door-panel probes test the material at each reconstructed opening twice.',survey_sha256=hashlib.sha256((HERE/'streetside-image-measurements.json').read_bytes()).hexdigest(),meshes=reports)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
    if not all(row['direct_mesh_matches']==56 for row in reports):raise SystemExit(1)

if __name__=='__main__':
    main()
