"""Verify the two courtyard views against material samples distinct from the wall-fit points."""
import argparse,hashlib,json,runpy
from pathlib import Path
from wing_frame import Camera
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
PICKS={
'design':{'brick':[(162,219),(183,226),(214,217),(336,216),(351,224)],'lime':[(178,192),(221,194),(196,197),(333,191)],'oak':[(146,225),(238,222),(322,220),(172,191),(282,193)],'tile':[(151,155),(167,140),(247,138),(340,143)]},
'album':{'brick':[(416,615),(456,610),(470,622),(571,612),(601,625)],'lime':[(418,586),(455,582),(573,581),(591,582)],'oak':[(405,621),(485,618),(562,617),(617,619)],'tile':[(412,506),(465,510),(589,510)]}}
def inspect(asset):
    scene=runpy.run_path(str(HELPER))['SerialScene'](asset)
    names={'brick':'garden brick','lime':'lime infill','oak':'oak framing','tile':'plain tile'}
    rows=[]
    for key,groups in PICKS.items():
        camera=Camera(key)
        for kind,pixels in groups.items():
            for uv in pixels:
                h=scene.ray(camera.C,camera.ray(uv),400);m=h['material'] if h else None
                nearest=None
                if m and names[kind] in m:nearest=[0,0]
                else:
                    for d in [1,2,3,4,6,8,10]:
                        for x,y in [(d,0),(-d,0),(0,d),(0,-d)]:
                            q=scene.ray(camera.C,camera.ray([uv[0]+x,uv[1]+y]),400)
                            if q and names[kind] in q['material']:nearest=[x,y];break
                        if nearest is not None:break
                rows.append(dict(station=key,uv=uv,observed=kind,first_hit=m,matched=nearest==[0,0],nearest_sampled_offset=nearest))
    return {'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256((HERE/'wing-cameras.json').read_bytes()).hexdigest(),'total':len(rows),'exact':sum(x['matched']for x in rows),'rays':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    d=inspect(a.mesh);a.out.write_text(json.dumps(d,indent=2)+'\n');print(d['exact'],d['total'])
