"""Compare fixed pixels from the two 2020 street panoramas with the first delivered GLB surface."""
from pathlib import Path
import argparse,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from materials import PLASTER,CEMENT,DENTIL,FRAME,GLASS,GRILLE,DARK,ROOF,WOOD
from placement import Facade
WINDOW=(GLASS,FRAME)
ORNAMENT=(DARK,GRILLE)
TRIM=(CEMENT,DENTIL,ROOF)
FIELD=(PLASTER,)
SAMPLES={
'south':[
 ('south third-storey window',298,178,WINDOW),('south window upper glass',295,158,WINDOW),
 ('plaster below south upper window',302,215,FIELD),('plaster below curved upper wall',260,219,FIELD),
 ('south arched clear lower pane',291,290,WINDOW),('south arched fanlight',292,263,WINDOW),
 ('plaster above arch',293,234,FIELD),('plaster south of arch',268,278,FIELD),
 ('wide middle window lower pane',370,316,WINDOW),('wide middle window upper pane',369,287,WINDOW),
 ('front field between the middle and north lights',395,296,FIELD),
 ('north arched glass',428,321,WINDOW),('plaster immediately north of arch',441,322,FIELD),
 ('central third-storey south sash',366,218,WINDOW),('central third-storey north sash',376,226,WINDOW),
 ('plaster below central decorative apron',371,265,FIELD),('north upper pane',425,265,WINDOW),
 ('north end wall above belt',440,333,FIELD),('main wall below the high south eave',219,110,FIELD)],
'east':[
 ('south upper window',170,108,WINDOW),('south upper right pane',186,84,WINDOW),
 ('plaster to south of upper window',129,116,FIELD),('plaster under south upper sill',178,150,FIELD),
 ('first fanlight central pane',154,208,WINDOW),('south arched lower pane',149,247,WINDOW),
 ('plaster above southern fanlight',157,172,FIELD),('plaster left of lower central window',261,225,FIELD),
 ('wide middle glass lower right',342,260,WINDOW),('wide middle upper left pane',301,206,WINDOW),
 ('plaster above central lintel',315,171,FIELD),('middle upper south light',300,96,WINDOW),
 ('middle upper north light',350,92,WINDOW),('pier between upper lights',326,90,FIELD),
 ('south octagonal grille',303,145,ORNAMENT),('north octagonal grille',346,145,ORNAMENT),
 ('plaster beyond apron',367,156,FIELD),('north fanlight glass under curved head',536,210,WINDOW),
 ('north arched clear lower pane',542,255,WINDOW),('plaster north of fanlight',572,249,FIELD),
 ('field below north upper window',539,153,FIELD),('south curved upper wall',112,144,FIELD),
 ('straight north-end plaster',579,149,FIELD),('plaster south of numbered entrance',241,344,FIELD)]}

def inspect(mesh):
    scene=SerialScene(mesh);f=Facade(None,along=(.0185,.99983))
    data=json.loads((HERE/'street-facade-dimensions.json').read_bytes());results={}
    for station in data['stations']:
        name=station['station'];P=np.array(station['P']);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        origin=np.array(f.point(*eye));rows=[]
        for feature,x,y,materials in SAMPLES[name]:
            xyz=eye+inv@[x,y,1];direction=np.array(f.point(*xyz))-origin
            hit=scene.ray(origin,direction,75)
            rows.append({'feature':feature,'working_pixel':[x,y],'expected_materials':materials,'first_hit':hit,'matched':bool(hit and hit['material'] in materials)})
        results[name]={'matched':sum(r['matched'] for r in rows),'total':len(rows),'pixels':rows}
    return {'mesh':scene.asset,'source_panorama_ids':data['source_panorama_ids'],'native_raster':[1200,890],'working_raster':[720,534],'stations':results}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path);arg=parser.parse_args()
    r=inspect(arg.mesh);arg.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    for name,station in r['stations'].items():print(name,station['matched'],station['total'],[(p['feature'],p['first_hit'] and p['first_hit']['material'])for p in station['pixels'] if not p['matched']])
