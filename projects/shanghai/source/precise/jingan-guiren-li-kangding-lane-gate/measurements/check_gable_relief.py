"""Test the first surface reached by samples from the documented public facade."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from gable_relief import xy,homog,STONE,LIP,FRAME,INK,FACE,SHADOW

def check(mesh):
    sc=SerialScene(mesh)
    survey=json.loads((HERE/'carving-plane.json').read_text())
    sign=json.loads((HERE/'lane-inscription.json').read_text())
    H=np.asarray(survey['drawing_to_metric_xz'])
    D=np.asarray(survey['pixel_to_street_photo'])
    R=homog(sign['source_outer_frame'],sign['drawing_outer_frame'])
    samples=[]
    def cast(feature,uv,expected):
        x,z=xy(H,[uv])[0];hit=sc.ray([x,-1,z],[0,1,0],1.04)
        mat=hit['material'] if hit else None
        relief=round(1-hit['distance_m'],4) if hit else None
        valid=bool(hit and mat in expected and -.002<=relief<=.10)
        samples.append(dict(feature=feature,street_pixel=xy(D,[uv])[0].round(2).tolist(),
                            drawing_pixel=np.array(uv).round(2).tolist(),xz_m=[round(x,4),round(z,4)],
                            expected_materials=expected,first_material=mat,outward_m=relief,passed=valid))
    for u,v in [(324,112),(324,130),(324,147),(316,136),(333,136),(319,154),(329,155)]:
        cast('blank mirror field',(u,v),[STONE,LIP])
    for u,v in [(324,82),(324,91),(312,91),(337,92),(308,102),(342,102),(302,121),(345,114),(286,126),(364,127),(319,179),(336,181)]:
        cast('crown, side scroll or rolled frame',(u,v),[STONE,LIP])
    for u,v in [(326,191),(325,200),(326,213),(325,220),(326,239),(326,251),(326,259)]:
        cast('central hanging ornament',(u,v),[LIP,STONE])
    for side,cx,v,tip in [('left',162,209,458),('right',493,194,440)]:
        for u,yy in [(cx,v),(cx-8,v),(cx+13,v),(cx,v+15),(cx,v+20),(cx,v+35),(cx,v+50),(cx+.7,v+110),(cx+1,v+140),(cx-9,v+152),(cx+1,v+153),(cx+12,v+151),(cx+2,tip-43),(cx+2,tip-35),(cx+2,tip-27),(cx+2,tip-19),(cx+2,tip-10),(cx+1,tip-4)]:
            cast(side+' boss, ribbon, transverse swag or scale',(u,yy),[STONE,LIP])
    for side,points in [('left',[(289,160),(282,170),(267,190),(248,205),(230,213),(207,219),(188,219)]),('right',[(359,158),(369,171),(383,185),(399,196),(422,203),(445,205),(465,204)])]:
        for p in points:cast(side+' festoon',p,[STONE,LIP,SHADOW])
    for l in sign['letters']:
        for stroke in l['strokes']:
            poly=Polygon(stroke['exterior'],stroke['holes'])
            cast(l['character']+' photographed dark stroke',xy(R,[poly.representative_point().coords[0]])[0],[INK])
            for ring in stroke['holes']:
                pt=Polygon(ring).representative_point().coords[0]
                cast(l['character']+' photographed open counter',xy(R,[pt])[0],[FACE])
    for p in [(167,45),(243,75),(329,70),(405,92),(320,45),(318,102),(242,107),(426,60),(253,30)]:
        inner=Polygon(sign['face_in_source']).covers(__import__('shapely').Point(*p))
        cast('name field' if inner else 'cement rim',xy(R,[p])[0],[FACE]if inner else[FRAME])
    return dict(model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),count=len(samples),passed=all(i['passed']for i in samples),samples=samples)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();out=check(args.mesh);args.output.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
    print(out['count'],[(x['feature'],x['drawing_pixel'],x['first_material'])for x in out['samples'] if not x['passed']])
    raise SystemExit(0 if out['passed']else 1)
