"""Rebuild both versions of the existing complete V13 library with the revised east doors."""
from argparse import ArgumentParser
import importlib.util
import json
from pathlib import Path
import sys
from shapely.geometry import Polygon

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]/'authoring'
sys.path.insert(0,str(BASE/'common'))
loader=importlib.util.spec_from_file_location('published_yangpu_library',BASE/'build_model.py')
v13=importlib.util.module_from_spec(loader)
loader.loader.exec_module(v13)
from east_entry import add_entry


class Library(v13.Library):
    def __init__(self,lod=False):
        super().__init__(lod)
        self.b.palette={**self.b.palette,'entrance stone recess':{'color':[.61,.565,.477],'roughness':.86}}

    def front(self):
        super().front()
        prefix='east-main-front/arched-entrance'
        # Save the source-produced aperture and its actual east-front frame.
        # Every original part outside this one named assembly remains in order.
        old=[i for i,p in enumerate(self.b.parts)if p['label'].startswith(prefix+'/')]
        markers=[i for i,f in enumerate(self.features)if f['label']==prefix]
        assert old and len(markers)==1 and old==list(range(old[0],old[-1]+1))
        marker=self.features.pop(markers[0])
        original_door=Polygon(marker['polygon_uz'])
        cx,cy,_=marker['face_origin_enu']
        tx,ty,_=marker['tangent_enu']
        f=v13.Facade(self.b,[cx-tx,cy-ty],[cx+tx,cy+ty],'east-main-front')
        start=old[0]
        del self.b.parts[start:old[-1]+1]
        insertion=len(self.b.parts)
        add_entry(self,f,self.front_center_y-cy,original_door)
        revised=self.b.parts[insertion:]
        del self.b.parts[insertion:]
        self.b.parts[start:start]=revised
        self.features.insert(markers[0],self.features.pop())


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--out',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    model=Library(args.lod).build()
    extras=dict(id='yangpu-library',anchor=model.anchor,rotation_y=0,axis='glTF east/up/south, source ENU metres',
        ground_base_m=0,height_estimate_m=22.51,source_footprint_sha256=v13.sha(BASE/'calibration.json'),
        scope='Complete old and modern connected library, two open inner courtyards; exterior only',
        textures_embedded=False,lod_authored_simplification=args.lod,
        copyright='Geometry/code MIT; footprint OpenStreetMap contributors/Overture ODbL-1.0; photo observations attributed separately')
    stats=model.b.save(args.out/'yangpu-library.glb',extras)
    v13.write(args.out/'features.json',dict(features=model.features,counts=dict(v13.Counter(x['kind']for x in model.features)),
        calibration_sha256=v13.sha(BASE/'calibration.json'),lod=args.lod,unmeasured_dimensions_are_estimates=True))
    print(json.dumps({k:stats[k]for k in ['file','triangles','bytes','sha256']}))


if __name__=='__main__':main()
