"""Raycast the actual decoded package and assign part names by matching oriented triangle coordinates."""
from pathlib import Path
import argparse,collections,hashlib,json,sys
import numpy as np

def corner_keys(triangles):
    data=np.rint(triangles*10000).astype('<i4')
    starts=np.lexsort((data[:,:,2],data[:,:,1],data[:,:,0]),axis=1)[:,0]
    order=(starts[:,None]+np.arange(3))%3
    canonical=data[np.arange(len(data))[:,None],order]
    return canonical.reshape(-1,9).view('V36').ravel()

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('camera_checker_dir',type=Path)
    cli.add_argument('raw',type=Path)
    cli.add_argument('decoded',type=Path)
    cli.add_argument('out',type=Path)
    a=cli.parse_args()
    sys.path.insert(0,str(a.camera_checker_dir))
    from check_return_roof import ProjectedMesh,RAY,STATIONS,examine
    read=lambda p:json.loads(p.read_bytes())
    origin=ProjectedMesh(a.raw,read(a.raw.with_suffix('.geometry.json')))
    tri,ind,mats,asset=RAY['load_triangles'](a.decoded)
    labels=np.empty(len(tri),dtype=np.int32)
    raw_keys=corner_keys(origin.tri)
    decoded_keys=corner_keys(tri)
    for m,mat in enumerate(mats):
        table=collections.defaultdict(list)
        for i,label in enumerate(origin.labels):
            if origin.parts[label]['material']==mat:table[raw_keys[i].tobytes()].append(label)
        for i in np.flatnonzero(ind==m):
            key=decoded_keys[i].tobytes()
            if not table[key]:raise ValueError((mat,i,'unmatched triangle'))
            labels[i]=table[key].pop()
        if any(table.values()):raise ValueError((mat,'uncounted original triangles'))
    scene=ProjectedMesh.__new__(ProjectedMesh)
    scene.tri,scene.labels,scene.parts,scene.asset=tri,labels,origin.parts,asset
    stations=read(a.camera_checker_dir/'lawn-return-stations.json')['stations']
    output={}
    for k,picks in STATIONS.items():
        scene.station(stations[k])
        output[k]=examine(scene,picks)
    a.out.write_text(json.dumps({'decoded':asset,'raw':origin.asset,'triangles_matched':len(tri),
          'method':'Match each decoded triangle to an original material and oriented three-corner key at 0.1 mm. Rays use only decoded coordinates.','stations':output},indent=2)+'\n')
    print({k:[r['upper_slope_edge_dy_px']for r in rows if r['feature']=='ridge']for k,rows in output.items()})
if __name__=='__main__':main()
