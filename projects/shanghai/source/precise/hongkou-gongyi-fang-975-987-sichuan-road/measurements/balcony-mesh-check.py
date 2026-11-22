"""Use unfiltered first intersections to inspect both balcony levels in a serialized GLB."""
import argparse
import gzip
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

IRON='Balcony | blackened wrought iron'
DECK='Balcony | mineral deck and nosing'
STONE='Gongyi 3 | grey-beige washed aggregate'
TRIM='Gongyi 3 | pale stone dressings'


def check(path):
    layout=json.loads((HERE.parent/'source/front-layout.json').read_bytes())
    reference=json.loads((HERE/'balcony-photo-traces.json').read_bytes())
    scene=SerialScene(path)
    edges=layout['bay_edges']
    depth=layout['balcony_depth']
    span=float(np.median(np.diff(edges)))
    pier=.097*span
    height=.235*span
    rows=[]

    def ray(label,start,target,expected,length=None):
        origin=np.array(start,dtype=float)
        target=np.array(target,dtype=float)
        distance=float(np.linalg.norm(target-origin))
        surface=scene.ray(origin,target-origin,distance+.045 if length is None else length)
        error=float(np.linalg.norm(np.array(surface['point_enu_m'])-target)) if surface else None
        passed=surface is None if expected is None else (
            surface is not None and expected==surface['material'] and error<.003)
        rows.append(dict(feature=label,start=origin.round(4).tolist(),end=target.round(5).tolist(),
                         first=surface,expected=expected,error_m=error,passed=passed))

    for level,floor in enumerate(layout['balcony_z'],2):
        for i,(a,c) in enumerate(zip(edges,edges[1:]),1):
            left=a+pier/2
            width=c-a-pier
            y=-depth+.43*pier-.021
            bottom=floor+.033*height
            top=floor+.858*height
            def uv(x,v):return np.array([left+width*x/670,y,top-v*(top-bottom)/176])
            prefix=f'L{level} bay {i} '
            for label,u,v in [('six-spoke hub',339,88),('hoop at west side',319,88),
                              ('inner left fold',235,134.6),('outer left fold',56,39.3),
                              ('inner right fold',436,39.6),('outer right fold',617,135.),
                              ('long spindle',132,90),('bottom marginal ring',488,155.8),
                              ('rail across spindle head',152,21),('upper-right spoke, previous aperture reading',345,74),
                              ('horizontal extension beyond hoop',312,88)]:
                target=uv(u,v)
                ray(prefix+label,target+[-.010,-.64,.044],target,IRON)
            for n,(u,v) in enumerate([(120,98),(339,73),(230,91),(520,70),(325,79),(352,99)],1):
                target=uv(u,v)
                ray(prefix+f'visible iron aperture {n}',target+[0,-.42,0],target+[0,.15,0],
                    None,.57)
            x=(a+c)*.5
            rail_y=-depth+pier*.43-.012-pier*.405*.5
            ray(prefix+'stone handrail',[x,rail_y-.6,top+.033],[x,rail_y,top+.033],TRIM)
            ray(prefix+'floor slab',[x,-depth-.5,floor-.13],[x,-depth,floor-.13],DECK)
            ray(prefix+'slab nosing',[x,-depth-.5,floor-.023],[x,-depth-.026,floor-.023],TRIM)
        for i,x in enumerate(edges,1):
            front=depth+.028
            prefix=f'L{level} pier {i} '
            for label,z,y,material in [
                ('washed front',floor+height*.48,-front,STONE),
                ('top cap',floor+height*.964,-front-.043,TRIM),
                ('floor carried above the slot',floor-.195,-.45*depth,DECK)]:
                target=[x,y,z]
                start=[x,y-.5,z] if label!='floor carried above the slot' else [x,y,z-.80]
                ray(prefix+label,start,target,material)
            for sign in (-1,1):
                # From the open space between the two brackets, toward each
                # independent side face under the deck. No material prefilter.
                y=-.46*depth
                z=floor-.26
                target=[x+sign*(.249-.138)*pier,y,z]
                ray(prefix+f'console inner cheek {sign}',[x,y,z],target,STONE)
    # The restorer's independent after-repair camera is registered on masonry,
    # thresholds and nosings. Test the visible faces above those nosings.
    # Keep the image locations even at the cropped left border.
    calibrated=json.loads((HERE/'repaired-front-pixel-camera.json').read_bytes())
    anchors=calibrated['anchors']
    def anchor(kind,index):
        return next(r['xyz'] for r in anchors if r['feature']==kind and r['bay_axis']==index)
    sx=anchor('upper balcony nosing',10)[0]/edges[-1]
    old0=anchor('lower balcony nosing',10)[2]
    old1=anchor('upper balcony nosing',10)[2]
    z0,z1=layout['balcony_z']
    sz=(old1-old0)/(z1-z0)
    metric=np.diag([sx,1.,sz,1.])
    metric[2,3]=old0-sz*z0
    projection=np.asarray(calibrated['P'])@metric
    eye=-np.linalg.solve(projection[:,:3],projection[:,3])
    image_hits=[]
    for level,indices in [('upper',[(14,205),(194,205),(379,205),(562,204),(747,205)]),
                          ('lower',[(15,347),(195,347),(380,347),(562,345),(746,344)])]:
        for pier_id,uv in enumerate(indices,6):
            direction=np.linalg.solve(projection[:,:3],[*uv,1.])
            intersection=eye+direction*(-depth-.028-eye[1])/direction[1]
            # The opening in front of the rail is empty. Spatial acceleration
            # in SerialScene narrows the candidate triangles by ray bounds.
            first=scene.ray(eye,direction,np.linalg.norm(intersection-eye)+1.4)
            passed=(first is not None and first['material'] in (TRIM,STONE)
                    and abs(first['point_enu_m'][1]+depth+.028)<.075)
            image_hits.append(dict(photo='chapter_15',level=level,pier=pier_id,uv=uv,
                                   pier_front_plane_xyz=intersection.tolist(),first=first,passed=passed))
    return dict(repaired_photo_first_intersections=image_hits,
                repaired_photo_hits=sum(q['passed'] for q in image_hits),
                repaired_photo_total=len(image_hits),asset=scene.asset,protocol='Photographic ironwork line drawing, front faces, four physical apertures per bay, and two separate corbels per pier. All first hits use the complete scene.',
                photographic_sources=[item['id'] for item in reference['source_images']],
                total=len(rows),hits=sum(r['passed'] for r in rows),observations=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('asset',type=Path)
    p.add_argument('output',type=Path)
    opt=p.parse_args()
    result=check(opt.asset)
    packed=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
    if opt.output.suffix=='.gz':
        packed=gzip.compress(packed,mtime=0)
    tmp=opt.output.with_name(opt.output.name+'.new')
    tmp.write_bytes(packed);tmp.replace(opt.output)
    print(result['hits'],result['total'],[(r['feature'],r['first']) for r in result['observations'] if not r['passed']][:6])
    print('Photographic first intersections',result['repaired_photo_hits'],result['repaired_photo_total'])
    raise SystemExit(result['hits']!=result['total'] or result['repaired_photo_hits']!=result['repaired_photo_total'])
