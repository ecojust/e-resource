"""Build the city browser case from the current Xinen church west porch contract and a supplied signed previous city."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
import json,runpy
from shapely.geometry import shape

HERE=Path(__file__).resolve().parent
P=HERE.parents[2]
ID='jingan-xinen-church-west-porch'

def load(path):
    return json.loads(path.read_bytes())

def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--geometry',default=HERE,type=Path)
    cli.add_argument('--parent',type=Path,required=True)
    cli.add_argument('--catalog',type=Path)
    cli.add_argument('--catalog-sha256')
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--required-order',type=int,default=322)
    args=cli.parse_args()
    parent=load(args.parent)
    assert parent['order']==args.required_order
    catalog_path=Path(parent['root'])/'projects/shanghai/data/candidate-city-integrations.json'
    assert sha256(catalog_path.read_bytes()).hexdigest()==parent['catalog_sha256']
    if args.catalog is not None:
        assert args.catalog_sha256 and sha256(args.catalog.read_bytes()).hexdigest()==args.catalog_sha256
        catalog_path=args.catalog
    catalog=load(catalog_path)
    assert not any(v['id']==ID for v in catalog['models'])
    ref=load(P/'source/precise'/ID/'footprint-review.json')
    g=load(args.geometry/'placement-geometry.json');contract=load(args.geometry/'final-placement-contract.json')
    assert contract['id']==g['id']==ID and len(g['ground_probes'])==66
    mask=shape(contract['replacement_geometry']);assert mask.geom_type=='Polygon'
    case=dict(id=ID,addedOwners=[3149],residualCutProbe=[-4.6,2.8],neighbors=[v['owner']for v in g['neighbors']],
        addedTriangles=len(mask.exterior.coords)-3,sourceSectionCount=g['cap_segments'],
        front=dict(center=[0.,0.],elevation=3.2,pitch=53,zoom=20.35,bearingOffset=1.),
        roof=dict(center=[0.,6.36],elevation=12.21,pitch=52,zoom=20.12,bearingOffset=5.),
        ground=[dict(name=r['name'],xy=r['xy'],expected=r['expected_map'],modelObstacle=r['model_obstacle'],cut=r['source_cut'])for r in g['ground_probes']],
        neighborGround={r['owner']:r['center_wgs84']for r in g['neighbors']})
    bind=runpy.run_path(str(HERE.parent/'empire-mansions-v1/verify-placement.py'))['bind_prior']
    row=bind(case,catalog,ref['frozen_macro'],ref['near_tiles'][0])
    args.out.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
