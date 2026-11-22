"""Test every outer brick, representative hood, transom and independently photographed surface."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from daren_photo_plane import camera_matrix
import street_brick_arcade as a


def check(path,far=False):
    scene=SerialScene(path);rows=json.loads(a.SECTIONS.read_text())['openings'];physical=[];photo=[]
    def trace(label,start,direction,end,accepted,group,*,camera=None,uv=None):
        hit=scene.ray(start,direction,end);material=hit['material'] if hit else None
        r=dict(target=label,first=material,matched=material in accepted)
        if camera:r.update(camera=camera,native_pixel=uv)
        else:r.update(start_xyz_m=[round(float(v),4)for v in start],expected=list(accepted))
        group.append(r)
    def surface(label,xz,accepted):trace(label,[xz[0],-.25,xz[1]],[0,1,0],.92,accepted,physical)
    for o in rows:
        i=o['number'];x=o['center'];sp=o['spring'];s=o['sill'];divisions=a._joint_stations(o)
        for j,(low,hi) in enumerate(zip(divisions,divisions[1:])):
            target=a._point(o,(low+hi)/2,.101)
            if o['partition_left']+.003 < target[0] < o['partition_right']-.003:
                surface(f'{i:02d} radial brick {j+1}',target,[a.BRICKS[(i+1)%5] if far else a.BRICKS[(3*j+i+j//5)%5]])
        if not far:
            for j,t in enumerate(divisions[1:-1]):
                pt=a._point(o,t,.104)
                if o['partition_left']+.004<pt[0]<o['partition_right']-.004:
                    surface(f'{i:02d} recessed mortar joint {j+1}',pt,[a.MORTAR])
        for t in [.45,.86,1.24,1.63,2.02,2.38,2.73]:
            for offset,material in [(.214,a.TRIM),(.241,a.BEAD),(.273,a.TRIM),(.303,a.BEAD)]:
                pt=a._point(o,t,offset)
                if o['partition_left']+.003<pt[0]<o['partition_right']-.003:
                    surface(f'{i:02d} projecting hood at {offset:.3f}',pt,[material])
        if i==8:
            for q in [-.14,0.,.14]:surface('08 solid orange timber', [x+q,(sp+s)/2],[a.TIMBER])
        else:
            count,levels=o['glazing_grid'];left=x-o['half_width']+.058;step=(2*o['half_width']-.116)/count
            for j in range(count):
                for k in [0,levels-1]:
                    zz=s+.060+(k+.47)*(sp+.05-s-.060)/levels
                    surface(f'{i:02d} inset glass {j+1}.{k+1}',[left+(j+.28)*step,zz],a.GLASS)
            for j in range(1,count):
                surface(f'{i:02d} vertical steel {j}',[left+j*step,s+.11],[a.FRAME])
            surface(f'{i:02d} stone sill',[x-.03,s-.048],[a.SILL])
    controls=json.loads((HERE/'brick-arcade-check-pixels.json').read_text())['pixels']
    mats={'radial brick':[*a.BRICKS,a.MORTAR,a.TRIM,a.BEAD],'grey masonry':[a.GREY],
          'glazing or steel':[*a.GLASS,a.FRAME,a.GRILLE], 'painted door':[a.TIMBER], 'sill':[a.SILL]}
    for name,groups in controls.items():
        p=camera_matrix(name);eye=-np.linalg.solve(p[:,:3],p[:,3]);inv=np.linalg.inv(p[:,:3]);
        for label,points in groups.items():
            for px in points:
                trace(label,eye,inv@[*px,1],85,mats[label],photo,camera=name,uv=px)
    return dict(asset=scene.asset,mode='far' if far else 'near',physical_count=len(physical),
                physical_passed=sum(i['matched']for i in physical),source_pixels=len(photo),
                source_matched=sum(i['matched']for i in photo),physical=physical,photographic=photo)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--lod',action='store_true');q=p.parse_args()
    j=check(q.mesh,q.lod);q.output.write_text(json.dumps(j,indent=1)+'\n')
    print(j['physical_passed'],'/',j['physical_count'],'physical;',j['source_matched'],'/',j['source_pixels'],'source')
    for r in j['physical']+j['photographic']:
        if not r['matched']:print(r.get('camera','physical'),r['target'],r.get('native_pixel',r.get('start_xyz_m')),r['first'])
    raise SystemExit(int(j['physical_count']!=j['physical_passed']))
