"""Reproject both dated exterior photographs and test the published editable window geometry."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'source';PROJECT=HERE.parents[3]
sys.path[:0]=[str(SRC),str(PROJECT/'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder
import three_arches as body
Scene=runpy.run_path(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene']

def camera(view,layout):
    face,first,w,sill=body.settings(layout);base=(first-.5*w,sill)
    H=np.array(view['H_local_width_units_to_image'])
    m=np.array([[1/w,0,-base[0]/w],[0,1/(w*body.HEIGHT),-base[1]/(w*body.HEIGHT)],[0,0,1.]])
    G=H@m; width,height=view['image_size']; f=view['nominal_focal_px']
    K=np.array([[f,0,width/2],[0,f,height/2],[0,0,1.]])
    L=np.linalg.solve(K,G); ry,rz=L[:,0],L[:,1]
    rx=np.cross(ry,rz); rx=rx/np.linalg.norm(rx)*np.sqrt(np.linalg.norm(ry)*np.linalg.norm(rz))
    M=np.column_stack([K@rx,G[:,:2]]);T=G[:,2]-M[:,0]*face
    origin=-np.linalg.solve(M,T)
    if origin[0]<face:
        M[:,0]*=-1;T=G[:,2]-M[:,0]*face
        origin=-np.linalg.solve(M,T)
    return M,origin

def sample(case):
    # Pixel coordinates are fixed on the independently dated photographs.
    if case=='gao05':
        groups={'red brick':[(128,323),(194,324),(259,332)],'fanlight':[(127,350),(193,354),(259,360)],
                'upper glazing':[(126,382),(192,386),(258,389)],'lower glazing':[(122,422),(190,423),(255,424)],
                'red casing':[(106,384),(175,389),(242,390)],
                'stone sill':[(120,449),(189,450),(254,451)]}
    else:
        groups={'red brick':[(204,115),(505,125),(803,119)],'fanlight':[(176,237),(468,239),(780,241)],
                'upper glazing':[(196,380),(477,380),(794,382)],'lower glazing':[(210,555),(498,553),(804,551)],
                'red casing':[(276,388),(574,388),(873,388)],'inner jamb edge':[(140,390),(436,390),(746,390)]}
        # Coordinates were digitized on the separately rectified 2018 image.
        H=np.array(STUDY['views']['commons2018']['H_local_width_units_to_image'])
        groups={name:[project(H,(-.65+x*5.52/999,1.55-y*1.65/710)).tolist() for x,y in xy]for name,xy in groups.items()}
    return groups

def project(H,p):
    row=H@[*p,1];return row[:2]/row[2]

def inspect(file,layout):
    scene=Scene(file);rows=[]
    for n,v in STUDY['views'].items():
        M,O=camera(v,layout)
        for label,pts in sample(n).items():
            allow={'red brick':[*body.BRICKS,body.MORTAR],'upper glazing':[body.LIGHT],
                   'lower glazing':[body.LIGHT],'fanlight':[body.GLASS_CAP],'red casing':[body.TRIM],
                   'stone sill':[body.LEDGE],'inner jamb edge':[body.TRIM]}[label]
            for j,(u,vv) in enumerate(pts):
                hit=scene.ray(O.copy(),np.linalg.solve(M,[u,vv,1]),100)
                rows.append(dict(view=n,window=j+1,feature=label,source_pixel=[u,vv],allowed=allow,actual=hit,
                                 passed=bool(hit and hit['material'] in allow)))
    return dict(asset=scene.asset,passed_count=sum(r['passed']for r in rows),total=len(rows),cases=rows)

def build(out,lod,layout):
    b=Builder(dict(body.PALETTE));body.add_three_arches(b,lod,layout)
    volume=0.;count=0;triangles=0
    for part in b.parts:
        V=np.asarray(part['vertices']);T=np.asarray(part['triangles'])
        _,inv=np.unique(V.round(7),axis=0,return_inverse=True);ts=inv[T]
        edges=Counter(tuple(edge) for t in ts for edge in zip(t,np.roll(t,-1)))
        assert all(edges[e]==1 and edges[e[::-1]]==1 for e in edges),part['label']
        xyz=V[T];d=np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6
        assert d>0;volume+=d;count+=1;triangles+=len(T)
    b.save(out,dict(id='three-small-arched-windows',geometry_license='MIT'))
    return dict(editable_solids=count,closed_and_positive=count,triangles=triangles,total_individual_volume_m3=volume)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('out',type=Path);cli.add_argument('--layout',type=Path);cli.add_argument('models',nargs='*',type=Path)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    layout=json.loads(args.layout.read_bytes()) if args.layout else {}
    STUDY=json.loads((HERE/'triple-window-calibration.json').read_bytes())
    native={};roles=args.models
    if not roles:
        for lod in [False,True]:
            f=args.out/('triple-far.glb' if lod else 'triple-near.glb');native[f.name]=build(f,lod,layout);roles.append(f)
    geometry=[inspect(f,layout)for f in roles]
    (args.out/'triple-window-checks.json').write_text(json.dumps(dict(editable=native,geometry=geometry),ensure_ascii=False,indent=2)+'\n')
    for row in geometry:
        print(row['asset']['file'],row['passed_count'],row['total'],[(r['view'],r['feature'],r['window'],r['actual']['material']if r['actual']else None)for r in row['cases']if not r['passed']])
