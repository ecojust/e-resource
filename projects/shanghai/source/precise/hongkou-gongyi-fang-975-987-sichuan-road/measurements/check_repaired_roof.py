"""Compare fixed image observations to the first exposed surface of a delivered mesh."""
import argparse
from hashlib import sha256
import json
from math import cos, hypot, pi, sin
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene


def check(mesh):
    observer = SerialScene(mesh)
    evidence = HERE / 'roof-overhead-fixed-pixels.json'
    fixed = json.loads(evidence.read_text())
    readings = {}
    for key, view in fixed['views'].items():
        south, north = view['street_edge_south_and_north_uv']
        m_per_px = fixed['metric_length_m'] / hypot(north[0] - south[0], north[1] - south[1])
        samples = []
        for row in view['source_points']:
            x, y = row['local_xy_m']
            ray = observer.ray((x, y, 32), (0, 0, -1), 35)
            accepted = {'Gongyi 3 | ' + v for v in row['expected']}
            radius = 0 if ray and ray['material'] in accepted else None
            if radius is None:
                for pixels in (1, 2):
                    for i in range(8):
                        delta = pixels * m_per_px
                        query = (x + delta * cos(pi*i/4), y + delta * sin(pi*i/4), 32)
                        hit = observer.ray(query, (0, 0, -1), 35)
                        if hit and hit['material'] in accepted:
                            radius = pixels
                            break
                    if radius is not None:
                        break
            samples.append(dict(feature=row['feature'], uv=row['uv'], local_xy_m=[x,y],
                                expected=sorted(accepted), first=ray, nearest_radius_pixels=radius))
        readings[key] = dict(acquired=view['acquired'],m_per_image_pixel=m_per_px,
                             direct=sum(r['nearest_radius_pixels']==0 for r in samples),
                             within_two_pixels=sum(r['nearest_radius_pixels'] is not None for r in samples),
                             count=len(samples), samples=samples)
    return dict(asset=observer.asset,triangles=len(observer.tri),observations_sha256=sha256(evidence.read_bytes()).hexdigest(),
                interpretation='第一命中为垂直向下的实际整网首表面，另报相邻像素；异期临时覆盖物和正射边缘阴影可能与默认修后构造有差。',views=readings)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=check(args.mesh)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['asset']['sha256'], [(k,v['direct'],v['within_two_pixels'],v['count']) for k,v in result['views'].items()])
