"""Check the exported Ningbo Road facade and its three published photographic references."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('project', type=Path, help='Shanghai project directory')
parser.add_argument('output', type=Path, help='Destination for the JSON report')
parser.add_argument('--photo-directory', type=Path, help='Optional local copies named by their SHA-256')
opts = parser.parse_args()
project = opts.project.resolve()
slug = 'huangpu-shanghai-money-guild-front'
source = project/'source/precise'/slug
assets = project/'assets/models/candidates'/slug
review = json.loads((source/'reference-review.json').read_bytes())
manifest = json.loads((assets/'manifest.json').read_bytes())
sys.path.insert(0, str(source/'source'))
from build_model import META
from check_surfaces import check_triangles
from guild_front import AXES

def triangles(file):
    data=file.read_bytes()
    n=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+n]);binary=memoryview(data)[28+n:]
    def values(index):
        acc=doc['accessors'][index];view=doc['bufferViews'][acc['bufferView']]
        kind={5123:'<u2',5125:'<u4',5126:'<f4'}[acc['componentType']]
        width={'SCALAR':1,'VEC3':3}[acc['type']]
        offset=view.get('byteOffset',0)+acc.get('byteOffset',0);size=np.dtype(kind).itemsize
        return np.ndarray((acc['count'],width),dtype=kind,buffer=binary,offset=offset,
                          strides=(view.get('byteStride',width*size),size))
    coords=[];materials=[]
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            pos=values(prim['attributes']['POSITION']).copy()
            ind=values(prim['indices']).reshape(-1,3)
            coords.append(pos[ind][:,:,[0,2,1]]*[1,-1,1]);materials.extend(
                [doc['materials'][prim['material']]['name']]*len(ind))
    return np.concatenate(coords),np.array(materials),doc

def check_meshes():
    decoder = project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    previous = json.loads((project/'data/audit/shanghai-money-guild-front-v1/preflight/actual-three-surfaces.json').read_bytes())
    rows = {}
    with tempfile.TemporaryDirectory() as scratch:
        for role in ('raw','full','lod'):
            entry = manifest['assets'][role]
            raw = assets/entry['file']
            signature = sha256(raw.read_bytes()).hexdigest()
            assert signature == entry['sha256']
            decoded = raw
            if role != 'raw':
                decoded = Path(scratch)/(role+'.glb')
                subprocess.run(['node', decoder, raw, decoded, project/'vendor/meshopt_decoder.module.js'], check=True)
            geometry, labels, _ = triangles(decoded)
            observations = check_triangles(geometry, labels, role == 'lod')
            assert entry['triangles'] == observations['triangle_count']
            former = previous[role]
            for a,b in zip(observations['rays'], former['rays'], strict=True):
                assert a['name'] == b['name'] and a['material'] == b['material'] and a['passed'] and b['passed']
                if a['distance_m'] is None:
                    assert b['distance_m'] is None
                else:
                    assert np.isclose(a['distance_m'], b['distance_m'], atol=1e-8,rtol=0)
            features = {}
            for label in ('each balcony has a separate front deck','separate balcony handrail','a genuine iron opening reaches the recessed balcony glass','stone console projects from the wall below deck'):
                measures = [row for row in observations['rays'] if row['name'] == label]
                by_bay = {}
                for centre in AXES:
                    points = [m for m in measures if abs(m['origin'][0]-centre) < 2]
                    assert points
                    depths = [3-m['distance_m'] for m in points]
                    by_bay[str(centre)] = {'samples':len(points),'minimum_m':round(min(depths),4),'maximum_m':round(max(depths),4)}
                features[label] = by_bay
            rows[role] = {'sha256':signature,'triangles':len(geometry),'successful_rays':len(observations['rays']),'projection_from_front_wall_m':features}
    return rows


def check_photos():
    wiki = review['2015_photograph']
    historical = {'url':'https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cc/276_Ningbo_Rd._Shanghai.JPG/1280px-276_Ningbo_Rd._Shanghai.JPG','sha256':wiki['image_sha256'],'size':[1280,1926]}
    photos = []
    for entry in [historical,*review['independent_photographs']]:
        cached = opts.photo_directory/entry['sha256'] if opts.photo_directory else None
        if cached and cached.is_file():
            data = cached.read_bytes()
        else:
            with urlopen(Request(entry['url'], headers={'User-Agent':'Mozilla/5.0'}), timeout=35) as resp:
                data = resp.read()
        assert sha256(data).hexdigest() == entry['sha256']
        with Image.open(BytesIO(data)) as img:
            img.load()
            assert list(img.size) == entry['size']
        photos.append({k:entry[k] for k in ('url','sha256','size')})
    return photos

assert META['id'] == manifest['id'] and len(AXES) == 3
report = {'model':slug,'photos':check_photos(),'bay_axes_m':list(AXES),'assets':check_meshes()}
opts.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
