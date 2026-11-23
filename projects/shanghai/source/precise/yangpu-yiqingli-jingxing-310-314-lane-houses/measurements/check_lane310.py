"""Compare observed image points on the lane-310 gate and inner facade with the delivered mesh."""
from pathlib import Path
import argparse, json, sys
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

POINTS=[
('left shaft',257,414,'pale dressed stone'),('right shaft',535,422,'pale dressed stone'),
('red left field',279,398,'red mineral finish'),('red right field',555,423,'red mineral finish'),
('left round',281,268,'red mineral finish'),('right round',556,267,'red mineral finish'),
('right panel at left sign height',556,329,'red mineral finish'),('green enamel',267,324,'enamel number plate'),
('left crown apron',278,235,'dark stone moulding'),('right square cornice',555,232,'dark stone moulding'),
('left red cap',283,218,'red mineral finish'),('right red cap',557,209,'red mineral finish'),
('right boundary render',661,310,'patched basement render'),('right wall cap',682,267,'dark stone moulding'),
('east upper gable brick',682,141,'washed red bricks'),('west upper gable brick',328,124,'washed red bricks'),
('east stone frame',719,107,'pale dressed stone'),('west upper border',358,107,'pale dressed stone'),
('east gable head brick',614,65,'washed red bricks'),('east gable rail',677,65,'dark stone moulding'),
('east upper sash light',594,149,'weathered glass'),('east upper sash head',608,125,'dark stone moulding'),
('central tile',425,156,'brown clay roof tile'),('eave gutter',461,179,'aged green gutter'),
('clerestory glass',427,202,'weathered glass'),('red gate wall',464,226,'red brick in pale mortar'),
('pediment centre',452,250,'pale dressed stone'),('arch moulding',445,238,'dark stone moulding'),
('right stone scroll shoulder',491,294,'pale dressed stone'),('lower right scroll outline',505,290,'dark stone moulding'),('tablet field',458,295,'patched basement render'),
('inner west leaf',418,451,'dark blue timber'),('inner east leaf',463,456,'dark blue timber'),
('lower dark leaves',450,469,'dark blue timber')]
def check(path,local):
    data=json.loads((HERE/'310-gate-and-gables-camera.json').read_bytes())
    camera=np.array(data['display_camera_P_reference'])
    if not local:
        sys.path.insert(0,str(HERE.parent/'source'))
        from build_model import placed_matrix
        placement=json.loads((HERE.parent/'source/house-placements.json').read_bytes())['house_310']
        camera=camera@np.linalg.inv(placed_matrix(placement))
    inv=np.linalg.inv(camera[:,:3]);eye=-inv@camera[:,3]
    mesh=SerialScene(path);rows=[]
    for name,u,v,expected in POINTS:
        hit=mesh.ray(eye,inv@[u,v,1],55)
        exact=bool(hit and expected in hit['material'])
        rows.append({'name':name,'reference_px':[u,v],'material_expected':expected,'first_hit':hit,'exact':exact})
    return {'mesh':mesh.asset,'local_model':local,'reference_width_px':880,'matched':sum(r['exact'] for r in rows),'count':len(rows),'rows':rows}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path);cli.add_argument('--local',action='store_true')
    args=cli.parse_args();doc=check(args.mesh,args.local);args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(doc['matched'],doc['count'],[(r['name'],None if not r['first_hit'] else r['first_hit']['material']) for r in doc['rows'] if not r['exact']])
