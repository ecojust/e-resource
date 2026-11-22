"""Brick parapets, pilaster returns and short stone bands on the store's curved northwest corner."""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.ndimage import median_filter

from crown_plane import EYE,INVERSE,on_wall
from street_path import xyz

MEASUREMENT=Path(__file__).resolve().parents[1]/"measurements/corner-crown-features.json"
from material_names import MATERIAL as BRICK,TEXTURE
JOINT="Fine recessed crown mortar"
COPING="Weathered grey roof coping"
LIMESTONE="Toothed stone bands on the parapet"
PALETTE={BRICK:{"color":[1.,1.,1.],"roughness":.91,"texture":str(TEXTURE)},
         JOINT:{"color":[.344,.254,.194],"roughness":.97},
         COPING:{"color":[.366,.345,.310],"roughness":.83},
         LIMESTONE:{"color":[.598,.512,.405],"roughness":.86}}


@lru_cache(maxsize=1)
def observations():
    return json.loads(MEASUREMENT.read_bytes())


def projection_at(station,profiles):
    height=.018
    for start,crest,edge,r in profiles:
        if start<=station<=edge:
            if station<crest:
                alpha=(station-start)/max(crest-start,1.e-8)
            else:
                width=min(.035,(edge-crest)*.24)
                alpha=min(1.,(edge-station)/max(width,1.e-8))
            height=max(height,.018+r*np.clip(alpha,0.,1.))
    return height


def solid_strip(builder,marks,bottom,top,front,back,material,label):
    """Close each strip along the real curve, retaining its returns and lower edge."""
    if len(marks)<2:return
    vertices=[];faces=[]
    for s,lo,hi,pr,rear in zip(marks,bottom,top,front,back):
        if hi<lo-1.e-7:raise ValueError("Inverted crown course "+label)
        vertices.extend([xyz(s,lo,pr),xyz(s,hi,pr),xyz(s,lo,rear),xyz(s,hi,rear)])
    for i in range(len(marks)-1):
        a=4*i;b=a+4
        faces.extend([(a,b,b+1,a+1),(a+3,b+3,b+2,a+2),
                      (a+1,b+1,b+3,a+3),(a+2,b+2,b,a)])
    n=len(vertices)-4;faces.extend([(0,1,3,2),(n,n+2,n+3,n+1)])
    builder.add(vertices,faces,material,label)


def ruled_strip(builder,marks,low,high,front,back,material,label):
    marks=np.unique(np.round(marks,7))
    if len(marks)<2:return
    solid_strip(builder,marks,[low(s) for s in marks],[high(s) for s in marks],
                [front(s) for s in marks],[back(s) for s in marks],material,label)


@lru_cache(maxsize=1)
def layout():
    survey=observations()
    profiles=[]
    for row in survey['ribs_at_row_930']:
        a,b=row['dark_return_px'];c=row['lit_edge_u_px']
        profiles.append((*[on_wall(u,930.,.018)[0] for u in (a,b,c)],row['estimated_projection_m']))
    # The coping follows the projecting brick pilasters. Intersect the actual
    # offset contour so a raking ray meets the nearest exposed return.
    breaks=[s for a,b,c,_ in profiles for s in (a,b,c-min(.035,(c-b)*.24),c)]
    marks=np.unique(np.r_[np.arange(-6.,16.,.025),breaks])
    outline=np.array([xyz(s,0.,projection_at(s,profiles)+.019)[:2] for s in marks])
    edges=np.diff(outline,axis=0)
    delta=outline[:-1]-EYE[:2]
    def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
    def rim_point(u,v):
        direction=INVERSE@np.array([u,v,1.])
        den=cross(direction[:2],edges)
        dist=np.divide(cross(delta,edges),den,out=np.full(len(edges),np.nan),where=abs(den)>1.e-12)
        frac=np.divide(cross(delta,direction[:2]),den,out=np.full(len(edges),np.nan),where=abs(den)>1.e-12)
        keep=np.flatnonzero((frac>=0.)&(frac<=1.)&(dist>0.))
        j=keep[np.argmin(dist[keep])]
        return marks[j]+frac[j]*(marks[j+1]-marks[j]),EYE[2]+dist[j]*direction[2]
    top=[]
    for part in survey['roof_sections_px']:
        stations=[];elevations=[]
        for u,v in part:
            s,z=rim_point(u,v)
            stations.append(s);elevations.append(z)
        arr=np.column_stack((stations,elevations))
        arr=arr[np.argsort(arr[:,0])]
        # Smooth the roughly one-photo-pixel texture at a weathered coping rim.
        # The traced image edge already has a median antialiasing filter.
        # Smoothing elevation again would round off real coping return corners.
        top.append(arr)
    # Each jump in the photographic outline belongs to the common end of two
    # adjacent raised parapets. Preserve one shared station for their side faces.
    for a,b in zip(top[:-1],top[1:]):
        mid=(a[-1,0]+b[0,0])/2.
        a[-1,0]=b[0,0]=mid
    openings=[(a[0,0],a[-1,0],a[0,2],a[-1,2]) for a in stone_head_sections()]
    return profiles,top,openings


@lru_cache(maxsize=1)
def stone_head_sections():
    """Rows are [street station, window head, brick transition, projection, photo u]."""
    measured=json.loads((MEASUREMENT.parent/"ribbed-stone-window-heads.json").read_bytes())
    result=[]
    for panel in measured["panels"]:
        baseline=panel["bounds_source_samples"]
        valleys=np.array([r["u_at_reference_row"] for r in panel["long_flute_shadows"]])
        pitch=float(np.median(np.diff(valleys)))
        divisions=np.r_[valleys[0]-pitch,valleys,valleys[-1]+pitch]
        rows=[]
        for row in baseline:
            u=row["u_at_reference_row"]
            j=np.clip(np.searchsorted(divisions,u,side="right")-1,0,len(divisions)-2)
            t=np.clip((u-divisions[j])/(divisions[j+1]-divisions[j]),0.,1.)
            # Exposed longitudinal ribs turn smoothly into the dark, narrow
            # valleys between them. Their silhouettes are measured independently.
            out=.082+.079*np.sqrt(max(0.,1.-((t-.5)/.5)**2))
            s0,z0=on_wall(*row["lower_px"],out);s1,z1=on_wall(*row["top_px"],out)
            rows.append([.5*(s0+s1),z0,z1,out,u])
        rows=np.asarray(rows)
        # A depth change may put two adjoining projected samples on nearly
        # the same station. The front remains a continuous, forward-facing sheet.
        # Parametrize by the baseline stations, retaining the true measured lip heights.
        rows[:,0]=[on_wall(float(u),930.,.11)[0]for u in rows[:,4]]
        result.append(rows)
    return result


def add_ribbed_heads(builder,lod):
    measured=json.loads((MEASUREMENT.parent/"ribbed-stone-window-heads.json").read_bytes())
    for index,(section,observation) in enumerate(zip(stone_head_sections(),measured["panels"]),1):
        us=section[:,4]
        ids=set(range(0,len(section),3 if lod else 1))
        ids.update([0,len(section)-1])
        for r in observation["long_flute_shadows"]:
            j=int(np.argmin(abs(us-r["u_at_reference_row"])))
            ids.update(q for q in [j-1,j,j+1] if 0<=q<len(section))
        face=section[sorted(ids)]
        solid_strip(builder,face[:,0],face[:,1],face[:,2],face[:,3],np.full(len(face),-.058),
                    LIMESTONE,f"Ribbed stone window head {index}")


def add_dentil_band(builder,lod,index,observation,profiles):
    # The small squares are carved recesses within one continuous stone band.
    # Assemble a shallow backing, thin top rim, low fascia and individual
    # projecting lands between the observed slots. The slots stay visibly open.
    coords=np.array(observation['lip_polyline_px'])
    # The band sits just proud of its brick face; its projection is an estimate.
    rough_bounds=sorted(on_wall(u,v,.205)[0] for u,v in coords[[0,-1]])
    candidates=[rough_bounds[0]-.18,rough_bounds[1]+.18]
    candidates.extend(s for a,b,c,_ in profiles for s in (a,b,c) if candidates[0]<s<candidates[1])
    front=max(.194,max(projection_at(s,profiles) for s in candidates)+.075)
    st=np.array([on_wall(u,v,front) for u,v in coords]);a,b=st[0,0],st[-1,0]
    def lip(s):return np.interp(s,st[:,0],st[:,1])
    def constant(t):return lambda _s:t
    dense=np.linspace(a,b,max(3,int((b-a)/(.18 if lod else .09))+1))
    # Section thickness is estimated from the actual local image scale, at the
    # centre of the exposure. Do not assume equal pixel heights at all six bands.
    k=len(coords)//2;u,v=coords[k]
    _,zt=on_wall(u,v,front);_,zb=on_wall(u,v+24.,front)
    rise=np.clip(zt-zb,.20,.35)
    depth=front-.058
    ruled_strip(builder,dense,lambda s:lip(s)-rise,lip,constant(depth),constant(front-.187),
                LIMESTONE,f"Crown band {index+1} recessed bed")
    ruled_strip(builder,dense,lambda s:lip(s)-rise*.19,lambda s:lip(s)+rise*.025,
                constant(front+.016),constant(depth),LIMESTONE,f"Crown band {index+1} upper lip")
    ruled_strip(builder,dense,lambda s:lip(s)-rise,lambda s:lip(s)-rise*.68,
                constant(front-.014),constant(depth),LIMESTONE,f"Crown band {index+1} lower fascia")
    holes=[]
    for slot in observation['slots']:
        u,v=slot['centre_px'];left,right=slot['left_right_u_px']
        s0=on_wall(left,v,front)[0];s1=on_wall(right,v,front)[0]
        if s1>s0:holes.append((max(a,s0),min(b,s1)))
    cursor=a
    for piece,(l,r) in enumerate(sorted(holes)+[(b,b)],1):
        if l>cursor+.012:
            marks=np.linspace(cursor,l,max(2,int((l-cursor)/.075)+1))
            ruled_strip(builder,marks,lambda s:lip(s)-rise*.68,lambda s:lip(s)-rise*.19,
                        constant(front),constant(depth),LIMESTONE,f"Crown band {index+1} dentil {piece}")
        cursor=max(cursor,r)


def add_corner_crown(builder,lod):
    survey=observations();profiles,tops,openings=layout()
    bottom=survey['underside_elevation_m']
    station_events=[value for a,b,c,_ in profiles for value in (a,b,c-.035,c)]
    solid_faces=0
    for num,edge in enumerate(tops,1):
        start,end=edge[0,0],edge[-1,0]
        bounds=sorted({start,end,*[s for o in openings for s in o[:2] if start<s<end]})
        def roof(s):return float(np.interp(s,edge[:,0],edge[:,1]))
        def main_front(s):return projection_at(s,profiles)
        def rear(s):return -.36
        for j,(a,b)in enumerate(zip(bounds[:-1],bounds[1:]),1):
            mid=(a+b)/2
            aperture=next((o for o in openings if o[0]<=mid<=o[1]),None)
            head=None if aperture is None else stone_head_sections()[openings.index(aperture)]
            def sill(s,head=head):
                return max(bottom,np.interp(s,head[:,0],head[:,2])) if head is not None else bottom
            step=.16 if lod else .085
            marks=np.linspace(a,b,max(2,int((b-a)/step)+1)).tolist()
            marks.extend(k for k in station_events if a<k<b)
            marks=np.unique(np.round(marks,7))
            ruled_strip(builder,marks,sill,lambda s:roof(s)-.059,main_front,rear,
                        BRICK,f"Stepped crown brick section {num}.{j}")
            solid_faces+=1
        cap_marks=np.linspace(start,end,max(2,int((end-start)/(.13 if lod else .065))+1)).tolist()
        cap_marks.extend(s for s in station_events if start<s<end)
        cap_marks.extend(edge[:,0])
        ruled_strip(builder,cap_marks,lambda s:roof(s)-.059,roof,
                    lambda s:main_front(s)+.019,lambda s:-.386,
                    COPING,f"Coping over crown step {num}")
    add_ribbed_heads(builder,lod)
    for index,band in enumerate(survey['dentil_bands']):
        add_dentil_band(builder,lod,index,band,profiles)
    return solid_faces
