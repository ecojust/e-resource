"""Check measured apertures, doors, section clearance and roof in all three exported meshes."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import numpy as np

PROJECT=Path(__file__).resolve().parents[3]
ID='huangpu-fifth-textile-warehouse-river-front'
SCENE=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def inspect(scene, dims):
    tests=[]
    def ray(label, origin, direction, length, materials, coordinate, bounds):
        hit=scene.ray(origin,direction,length)
        ok=hit and hit['material'] in materials and bounds[0]<=hit['point_enu_m'][coordinate]<=bounds[1]
        assert ok,(label,origin,materials,bounds,hit)
        tests.append(dict(feature=label,origin=origin,ray=direction,observed=hit))
    def front(label,x,z,materials,lo,hi):
        ray(label,[x,-.90,z],[0,1,0],3.5,materials,1,[lo,hi])
    for level,rows in dims['windows'].items():
        for idx,row in enumerate(rows,1):
            x,w,b,t=[row[n]for n in ('center','width','sill','head')]
            h=t-b
            name=level+' '+str(idx)+' '
            front(name+'shallow arch crown',x,t-.065,['Charcoal arch linings'],.101,.112)
            front(name+'deep fanlight',x,t-h*.13,['Charcoal arch linings'],.256,.268)
            front(name+'opening jamb',x+w/2-.019,b+.68,['Warm grey cement window reveals'],-.050,-.043)
            front(name+'pale lime surround',x+w/2+.088,b+.68,['Pale lime window surrounds'],-.107,-.044)
            cage=[]
            for offset in np.linspace(-.34,.34,19):
                rh=scene.ray([x+w*offset,-.9,b+.21],[0,1,0],1.)
                if rh and rh['material']=='Steel flower basket wire' and -.343<=rh['point_enu_m'][1]<=-.30:cage.append(rh)
            assert cage,name
            tests.append(dict(feature=name+'visible front wire and brackets',observed=cage[0]))
            glass=set()
            for frac in (-.24,-.10,.10,.24):
                hit=scene.ray([x+w*frac,-.80,b+.60*h],[0,1,0],2.)
                if hit:glass.add(hit['material'])
            expected={'Muted sky in warehouse glass','Cool shaded side window glass'}
            assert glass&expected,(name,glass)
            tests.append(dict(feature=name+'glazing',materials=sorted(glass)))
            colours=set()
            for u in np.linspace(x-w*.30,x+w*.30,13):
                for z in [b+.02,b+.17,b+.225,b+.29]:
                    hit=scene.ray([u,-.63,z],[0,1,0],.60)
                    if hit:colours.add(hit['material'])
            assert {'Deep green window plants','Yellow green hanging leaves'}&colours
            assert {'Crimson window flowers','Bright red petal tips'}&colours
            tests.append(dict(feature=name+'planted wire basket',materials=sorted(colours)))
    door=dims['street']['portal']
    x=door['center'];w=door['width']
    for j in (-.34,-.21,.18,.32):
        for h in (.68,1.76):
            origin=[x+w*j,-.87,h]
            assert scene.ray(origin,[0,1,0],2.11) is None
            hit=scene.ray(origin,[0,1,0],2.53)
            assert hit and 1.46<=hit['point_enu_m'][1]<=1.52
            tests.append(dict(feature='Deep public entrance',origin=origin,observed=hit))
        for y in (.14,.43,1.13):
            ray('Threshold passing through existing wall',[x+w*j,y,1.29],[0,0,-1],1.30,
                ['Grey vestibule threshold'],2,[door['sill']-.002,door['sill']+.002])
    for side in (-1,1):
        jamb=x+side*w/2
        for y in (.13,.42,.88,1.16):
            ray('Lined vestibule jamb',[jamb-side*.28,y,1.13],[side,0,0],.31,
                ['Portal inset stone bevel'],0,[jamb-.001,jamb+.001])
    for y in (.11,.39,1.13):
        ray('Continuous vestibule soffit',[x+.39,y,door['head']-.43],[0,0,1],.49,
            ['Portal inset stone bevel'],2,[door['head']-.001,door['head']+.001])
    for side in (-1,1):
        front('Broad cement pier',side*dims['pillar_distance']/2,6.60,['Taupe cement pilasters'],-.159,-.151)
        front('Red brick spandrel edge',side*10.15,8.14,['Brick spandrel beneath upper windows','Red brick over the river bays','Weathered cement bands','Pale mineral edging'],-.22,.01)
        x=side*(dims['wall_width']/2-.30)
        ray('Roof over the inspected flank',[x,2.15,18.3],[0,0,-1],8.,
            ['Dull corrugated metal roof','Oxidised rainwater metal'],2,[10.90,11.65])
    x=dims['wall_width']/2-.30
    # At low height the west return stops before 1305. The upper wall resumes
    # above the independently checked height of that retained neighbouring roof.
    assert scene.ray([x-.7,2.3,4.8],[1,0,0],1.4) is None
    ray('Upper return above western neighbour',[x-.7,2.3,7.3],[1,0,0],1.4,
        ['Blue and red warehouse brick with lime residue'],0,[x-.24,x-.18])
    tests.append(dict(feature='West neighbour clearance',origin=[x-.7,2.3,4.8],passed=True))
    return tests


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('decoded_folder',type=Path)
    cli.add_argument('output',type=Path)
    args=cli.parse_args();folder=args.decoded_folder
    dims=json.loads((PROJECT/'source/precise'/ID/'source/dimensions.json').read_bytes())
    manifest=json.loads((folder/'manifest.json').read_bytes())
    models={}
    for role,path in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        asset=manifest['assets'][role];scene=SCENE(folder/path)
        assert digest(folder/asset['file'])==asset['sha256'] and len(scene.tri)==asset['triangles']
        models[role]=dict(asset_sha256=asset['sha256'],decoded_sha256=digest(folder/path),triangles=len(scene.tri),tests=inspect(scene,dims))
    args.output.write_text(json.dumps(dict(passed=True,model=ID,models=models),indent=2)+'\n')
    print({k:len(v['tests'])for k,v in models.items()})


if __name__=='__main__':
    main()
