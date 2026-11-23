"""Measure the first street-facing surface of the rebuilt portal at both detail levels."""
import argparse
from hashlib import sha256
import json
from math import pi,sin,cos
from pathlib import Path
import sys

import numpy as np
from shapely import maximum_inscribed_circle


AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
SOURCE = PROJECT/'source/precise/huangpu-puguang-ymca-east-entrance/source'
sys.path[:0] = [str(SOURCE), str(PROJECT/'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder, Facade
from stone_entrance import (add_entrance, letters, ENGLISH, SOUTH, NORTH, PORTAL_MATERIALS,
                            CUT, EDGE, STONE, WOOD, METAL, FACE, INK, PANEL, GLASS)


def strokes(text, x, z, width, height, label):
    # Sample the interior of the largest continuous portion of each glyph.
    for char, shape in zip(text.replace(' ',''), letters(text,width,height,True)):
        centre=maximum_inscribed_circle(shape,tolerance=.0004).coords[0]
        yield (label+' '+char,float(x+centre[0]),float(z+centre[1]))


def probes():
    targets = [
        ('portal lettering surround',-1.59,5.80,.129,STONE),
        ('north dated surround',3.828,4.51,.295,STONE),
        ('south dated surround',-3.9,3.56,.295,STONE),
        ('arch inner ribbon',0.95,3.806,.172,EDGE),
        ('keystone',.115,4.29,.281,STONE),
        ('southern square shaft',-2.075,3.29,.334,STONE),
        ('northern square shaft',2.045,3.29,.334,STONE),
        ('north volute core',2.045+.336,6.065,.515,STONE),
        ('south volute core',-2.075-.336,6.065,.515,STONE),
        ('clock ivory face',.121,3.485,-.331,FACE),
        ('clock metal rim',.453,3.363,-.302,METAL),
        ('dark clock frame',.477,3.363,-.317,WOOD),
        ('clock minute hand',-.065,3.251,-.310,INK),
        ('clock hub',0,3.363,-.299,METAL),
        ('fanlight glass',.40,3.68,-.537,GLASS),
        ('amber fanlight timber grid',.81,3.56,-.477,WOOD),
        ('north inner door panel',.21,2.04,-.529,PANEL),
        ('south inner door panel',-.21,2.04,-.529,PANEL),
        ('timber top rail',0,2.708,-.359,WOOD),
        ('rebated threshold',.76,.051,.026,EDGE),
        ('top edge below lower central sash',0,6.331,.213,EDGE),
    ]
    for i,numeral in enumerate(('XII','I','II','III','IIII','V','VI','VII','VIII','IX','X','XI')):
        angle=i*pi/6
        glyph=max(letters(numeral,.034*len(numeral)+.005,.099,True),key=lambda g:g.area)
        px,pz=maximum_inscribed_circle(glyph,tolerance=.0003).coords[0]
        x=.32*sin(angle)+px*cos(angle)+pz*sin(angle)
        z=3.363+.32*cos(angle)-px*sin(angle)+pz*cos(angle)
        targets.append(('Roman '+numeral,x,z,-.325,INK))
    for text,z,width,height in zip(ENGLISH,(5.891,5.527,5.143),(1.35,2.13,3.12),(.234,.234,.212)):
        for label,x,z0 in strokes(text,0,z,width,height,'lintel'):
            targets.append((label,x,z0,.115,CUT))
    for main,date,side in [(*SOUTH,-1),(*NORTH,1)]:
        for text,axis,scale,z0,z1 in [
            (main,side*3.075,.224,4.64,2.77),
            (date,side*(3.075+.536),.094,4.58,2.77)]:
            for i,char in enumerate(text):
                z=z0+(z1-z0)*i/(len(text)-1)
                for label,x,zc in strokes(char,axis,z,scale,scale,'pier'):
                    targets.append((label,x,zc,.284,CUT))
    return targets


class StreetRays:
    def __init__(self,builder):
        triangles,material,group=[],[],[]
        for part in builder.parts:
            face=np.asarray(part['vertices'])[part['triangles']]
            triangles.extend(face)
            material.extend([part['material']]*len(face))
            group.extend([part['label']]*len(face))
        self.set_faces(np.asarray(triangles),material,group)

    def set_faces(self,triangles,material,group):
        self.points=triangles
        self.material=material
        self.group=group
        self.x=self.points[:,:,0]
        self.z=self.points[:,:,2]
        self.depth=-self.points[:,:,1]
        self.det=(self.z[:,1]-self.z[:,2])*(self.x[:,0]-self.x[:,2])+(self.x[:,2]-self.x[:,1])*(self.z[:,0]-self.z[:,2])

    def hit(self,x,z):
        idx=np.flatnonzero((abs(self.det)>1e-12)&(self.x.min(axis=1)<=x)&(x<=self.x.max(axis=1))&
                           (self.z.min(axis=1)<=z)&(z<=self.z.max(axis=1)))
        u, h = self.x[idx], self.z[idx]
        a=((h[:,1]-h[:,2])*(x-u[:,2])+(u[:,2]-u[:,1])*(z-h[:,2]))/self.det[idx]
        b=((h[:,2]-h[:,0])*(x-u[:,2])+(u[:,0]-u[:,2])*(z-h[:,2]))/self.det[idx]
        inside=(a>=-1e-8)&(b>=-1e-8)&(a+b<=1+1e-8)
        if not inside.any():return None
        idx,a,b=idx[inside],a[inside],b[inside]
        d=a*self.depth[idx,0]+b*self.depth[idx,1]+(1-a-b)*self.depth[idx,2]
        k=int(np.argmax(d));i=idx[k]
        return float(d[k]),self.material[i],self.group[i]


def check_decoded(work):
    out={}
    records=json.loads((work/'delivered-decode.json').read_text())
    assert {r['variant'] for r in records}=={'raw','web','lod'}
    for record in records:
        role=record['variant']
        actual=work/(role+'.glb')
        assert sha256(actual.read_bytes()).hexdigest()==record['sha256']
        tri_path=work/('delivered-'+role+'-triangles.f64')
        mat_path=work/('delivered-'+role+'-materials.u16')
        gltf=np.fromfile(tri_path,np.float64).reshape(-1,3,3)
        ids=np.fromfile(mat_path,np.uint16)
        assert len(gltf)==len(ids)==record['triangles']
        coords=gltf[:,:,[0,2,1]].copy()
        coords[:,:,1]*=-1
        mats=np.asarray(record['material_names'])[ids]
        ray=StreetRays.__new__(StreetRays)
        ray.set_faces(coords,mats,mats)
        hits=[]
        items=probes()+[('lower central sash',.34,6.60,-.27,'sky grey upper glass')]
        for label,x,z,expect,material in items:
            hit=ray.hit(x,z)
            if not hit or abs(hit[0]-expect)>.003 or hit[1]!=material:
                raise ValueError((role,label,x,z,expect,material,hit))
            hits.append({'detail':label,'x_m':round(x,6),'z_m':round(z,6),
                         'first_surface_d_m':round(hit[0],6),'material':str(hit[1])})
        out[role]={'asset_sha256':record['sha256'],'triangles':len(ids),'probes':hits}
    return out


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--decoded',type=Path,help='Directory populated by the delivered-model GLTFLoader extractor')
    args=p.parse_args()
    if args.decoded:
        args.out.write_text(json.dumps(check_decoded(args.decoded),ensure_ascii=False,indent=2)+'\n')
        return
    results={}
    for role,lod in [('full',False),('lod',True)]:
        builder=Builder(PORTAL_MATERIALS)
        add_entrance(Facade(builder,(-3.97,0),(3.97,0),'Sichuan Road'),lod)
        rays=StreetRays(builder);records=[]
        for label,x,z,expect,material in probes():
            hit=rays.hit(x,z)
            if not hit or abs(hit[0]-expect)>.003 or hit[1]!=material:
                raise ValueError((role,label,x,z,expect,material,hit))
            records.append(dict(detail=label,x_m=round(x,6),z_m=round(z,6),front_d_m=round(hit[0],5),
                                material=hit[1],mesh_group=hit[2]))
        assert rays.hit(0,6.61) is None  # upper sash is independently built by the adjoining wall
        results[role]={'triangles':len(rays.det),'probes':records,'open_to_upper_wall_at':[0,6.61]}
    rec=dict(source_sha256=sha256((SOURCE/'stone_entrance.py').read_bytes()).hexdigest(),
             font_sha256=sha256((SOURCE/'entrance_fonts/PuguangEntranceStudy.otf').read_bytes()).hexdigest(),
             axes='x north, z up, d toward Sichuan Middle Road, all metres; isolated entrance geometry',
             checks=results)
    args.out.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
    print({role:len(data['probes']) for role,data in results.items()})


if __name__=='__main__':
    main()
