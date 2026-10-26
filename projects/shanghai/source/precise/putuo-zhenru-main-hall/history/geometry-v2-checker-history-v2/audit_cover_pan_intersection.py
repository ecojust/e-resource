#!/usr/bin/env python3
"""Actual piecewise-planar cover/pan lip intersections, preserving first FAIL.

For each actual upward triangle, find its exact-XY downward triangle. Intersect
cover/pan top-face projections, then clip that cell by the two actual vertical
overlap inequalities. This analyzes serialized solids, not builder formulas.
"""
from pathlib import Path
import argparse, hashlib, json, math, re
import numpy as np
from shapely.geometry import Polygon
from audit_actual_roles_contacts import Audit
from actual_glb import need, filemeta

HERE=Path(__file__).resolve().parent
POSITIVE_EMBED_M=.000001


def area(vertices):
    v=np.asarray(vertices)
    if len(v)<3:return 0.
    return abs(float(np.sum(v[:,0]*np.roll(v[:,1],-1)-v[:,1]*np.roll(v[:,0],-1)))/2)


def clip(vertices, plane):
    """Convex polygon halfplane clip; no buffer or relaxed overlap criterion."""
    if not vertices:return []
    output=[]
    for p,q in zip(vertices,vertices[1:]+vertices[:1]):
        fp=float(plane@[p[0],p[1],1]);fq=float(plane@[q[0],q[1],1])
        if fp>=0:output.append(p)
        if (fp>=0)!=(fq>=0):
            t=fp/(fp-fq);output.append([p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])])
    return output


class LipAudit:
    def __init__(self,raw,structure,first):
        self.a=Audit(raw,structure)
        self.first=first
        f=json.loads(first.read_bytes())
        need(f.get('schema')=='zhenru-independent-actual-roles-contacts-v1'
             and f.get('finite_checks_passed') is False
             and f.get('raw',{}).get('sha256')==self.a.r['raw']['sha256'],
             'Must retain and bind actual first failing report')
        self.first_hash=filemeta(first);self.facets_cache={}

    def facets(self,label):
        if label in self.facets_cache:return self.facets_cache[label]
        need(len(self.a.labels[label])==1,'Repeated contact solid label')
        tris=self.a.triangles(label);up={};down={}
        for t in tris:
            cross=np.cross(t[1]-t[0],t[2]-t[0])
            if abs(cross[2])<1e-12:continue
            key=tuple(sorted(tuple(v) for v in t[:,:2]))
            dest=up if cross[2]>0 else down
            need(key not in dest,'Overlapping duplicate projected triangle')
            matrix=np.column_stack([t[:,:2],np.ones(3)])
            dest[key]=(Polygon(t[:,:2]),np.linalg.solve(matrix,t[:,2]))
        need(up and set(up)==set(down),'Actual shell is not matching-XY top/bottom heightfield')
        rows=[]
        for key,(poly,top) in up.items():
            bottom=down[key][1]
            need(all((top-bottom)@[x,y,1]>0 for x,y in key),'Nonpositive actual shell thickness')
            rows.append({'polygon':poly,'top':top,'bottom':bottom})
        # Projection must be tiled once, not disconnected slabs collapsed into an envelope.
        total=sum(r['polygon'].area for r in rows)
        from shapely.ops import unary_union
        union=unary_union([r['polygon'] for r in rows])
        need(abs(total-union.area)<1e-8,'Top projection overlaps itself')
        self.facets_cache[label]=rows
        return rows

    def pair(self,cover,pan):
        overlap_area=0.;contact_area=0.;maximum_gap=0.;maximum_embed=0.
        polygons=[];strict_witnesses=[];cells=0
        for a in self.facets(cover):
            for b in self.facets(pan):
                p=a['polygon'].intersection(b['polygon'])
                if p.is_empty or p.area<1e-12:continue
                need(p.geom_type=='Polygon','Unexpected projected intersection')
                cells+=1;overlap_area+=p.area
                verts=[list(x) for x in p.exterior.coords[:-1]]
                for xy in verts:
                    q=np.array([*xy,1]);d=min(a['top']@q,b['top']@q)-max(a['bottom']@q,b['bottom']@q)
                    maximum_gap=max(maximum_gap,-float(d));maximum_embed=max(maximum_embed,float(d))
                # Both inequalities must hold for vertical intervals to intersect.
                p1=a['top']-b['bottom'];p2=b['top']-a['bottom']
                p1=p1.copy();p2=p2.copy();p1[2]-=POSITIVE_EMBED_M;p2[2]-=POSITIVE_EMBED_M
                clipped=clip(clip(verts,p1),p2)
                ca=area(clipped)
                if ca>1e-10:
                    contact_area+=ca;poly=Polygon(clipped);polygons.append(poly)
                    qxy=poly.representative_point();xy=(qxy.x,qxy.y)
                    ia=self.a.interval(cover,xy);ib=self.a.interval(pan,xy)
                    need(ia is not None and ib is not None,'Clipped contact witness lacks single actual interval')
                    embed=min(ia[1],ib[1])-max(ia[0],ib[0])
                    need(embed>=POSITIVE_EMBED_M-1e-8,'Clipped intersection fails independent actual ray interval')
                    strict_witnesses.append({'xy_m':list(xy),'positive_embed_m':embed})
        from shapely.ops import unary_union
        union=unary_union(polygons)
        if polygons:need(abs(union.area-contact_area)<1e-8,'Contact regions double counted')
        return {'cover':cover,'pan':pan,'intersecting_triangle_cells':cells,
                'common_projected_footprint_m2':overlap_area,
                'strict_positive_contact_projected_area_m2':contact_area,
                'contact_area_fraction':contact_area/overlap_area if overlap_area else 0,
                'maximum_gap_in_common_footprint_m':maximum_gap,
                'maximum_vertex_embed_m':maximum_embed,
                'strict_contact_witness_count':len(strict_witnesses),
                'minimum_witness_embed_m':min((x['positive_embed_m'] for x in strict_witnesses),default=None),
                'witnesses':strict_witnesses,'contact_union':union}

    def cross_sections(self,cover,pan,contact):
        """Multiple actual row stations crossing the shared support band."""
        from shapely.geometry import LineString
        v=np.unique(self.a.triangles(cover).reshape(-1,3),axis=0)
        # Tile plan has two course-end lines. Their actual longest edge connects
        # the ends; PCA selects row direction (tiles are longer than cap width).
        xy=v[:,:2];center=xy.mean(axis=0);_,_,vh=np.linalg.svd(xy-center,full_matrices=False)
        along=vh[0];across=np.array([-along[1],along[0]])
        u=xy@along;w=xy@across;rows=[]
        common=self.a.hull(cover).intersection(self.a.hull(pan))
        for fraction in [.1,.3,.5,.7,.9]:
            station=float(u.min()+(u.max()-u.min())*fraction)
            line=LineString([along*station+across*(w.min()-.01),along*station+across*(w.max()+.01)])
            strip=contact.intersection(line);foot=common.intersection(line)
            segments=[]
            geoms=[strip] if strip.geom_type=='LineString' else list(getattr(strip,'geoms',[]))
            for seg in geoms:
                if seg.geom_type!='LineString' or seg.length<1e-8:continue
                mid=seg.interpolate(.5,normalized=True);p=(mid.x,mid.y)
                ia=self.a.interval(cover,p);ib=self.a.interval(pan,p)
                need(ia is not None and ib is not None,'Section lacks actual interval')
                segments.append({'width_m':seg.length,'endpoints_xy_m':[list(seg.coords[0]),list(seg.coords[-1])],
                                 'midpoint_embed_m':min(ia[1],ib[1])-max(ia[0],ib[0])})
            rows.append({'row_fraction_by_actual_pca':fraction,'common_footprint_section_width_m':foot.length,
                         'strict_contact_width_m':strip.length,'segments':segments})
        return rows

    def run(self):
        pattern=re.compile(r'^roof/field([0-3])/cover/c(\d+)/r(\d+)$')
        rows=[];failures=[];representative=[];perfield={};sections_failed=[]
        minimum_area=float('inf');minimum_fraction=1.;maximum_gap=0.;minimum_section=float('inf')
        for label in sorted(self.a.labels):
            m=pattern.fullmatch(label)
            if not m:continue
            field,col,row=map(int,m.groups())
            for side,pan_col in [('left',col),('right',col+1)]:
                pan=f'roof/field{field}/pan/c{pan_col}/r{row}'
                r=self.pair(label,pan);contact=r.pop('contact_union')
                sections=self.cross_sections(label,pan,contact)
                widths=[s['strict_contact_width_m'] for s in sections]
                r['field']=field;r['side']=side;r['column']=col;r['row']=row
                r['section_contact_widths_m']=widths
                good=r['strict_positive_contact_projected_area_m2']>1e-8 and all(x>1e-6 for x in widths)
                r['strict_contact_and_five_sections_passed']=good
                if not good:failures.append({**r,'sections':sections})
                if any(x<=1e-6 for x in widths):sections_failed.append({'cover':label,'pan':pan,'widths_m':widths})
                minimum_area=min(minimum_area,r['strict_positive_contact_projected_area_m2'])
                minimum_fraction=min(minimum_fraction,r['contact_area_fraction']);maximum_gap=max(maximum_gap,r['maximum_gap_in_common_footprint_m'])
                minimum_section=min(minimum_section,*widths)
                group=perfield.setdefault(str(field),{'pairs':0,'passed':0,'minimum_contact_area_m2':float('inf'),'minimum_section_width_m':float('inf')})
                group['pairs']+=1;group['passed']+=int(good);group['minimum_contact_area_m2']=min(group['minimum_contact_area_m2'],r['strict_positive_contact_projected_area_m2']);group['minimum_section_width_m']=min(group['minimum_section_width_m'],*widths)
                # Retain row0 left/right examples in each field, plus first failure.
                if col==0 and row==0:representative.append({**r,'sections':sections})
                r.pop('witnesses');rows.append(r)
        need(len(rows)==8500,'Unexpected actual cover/pan pair count')
        need(filemeta(self.first)==self.first_hash,'First failing report changed during audit')
        return {'schema':'zhenru-actual-cover-pan-piecewise-intersection-v1','strict_edge_band_contact_passed':not failures,
                'raw':self.a.r['raw'],'structure_report':self.a.structure_proof,'first_failing_roles_report':self.first_hash,
                'pair_count':len(rows),'positive_embed_threshold_m':POSITIVE_EMBED_M,
                'minimum_positive_contact_projected_area_m2':minimum_area,'minimum_contact_area_fraction':minimum_fraction,
                'minimum_five_station_contact_width_m':minimum_section,'maximum_real_gap_elsewhere_in_shared_footprint_m':maximum_gap,
                'per_field':perfield,'first_at_most_40_failures':failures[:40],'failed_pair_count':len(failures),
                'failed_five_station_count':len(sections_failed),'representative_cross_sections':representative,'all_pair_measurements':rows,
                'method':'Pair actual Float32 upward/downward facets with exact identical XY triangles. Intersect cover/pan projected facets and clip each convex cell by both actual top-minus-other-bottom >=1micron inequalities. Sum/union disjoint facet contact cells. Independently verify representative points with actual two-crossing ray intervals; intersect contact regions at five actual PCA course stations for both lips of every cover. No builder roof/profile formula or relaxed positive clearance is used.',
                'limits':['Contact regions are analysis output only; raw is unchanged.','Positive contact bands do not certify broad contact over the curved cover interior: actual air cavities and failed original stations remain recorded.','Five transverse sections are finite; not a global collision, drainage, structural-engineering, photographic or model acceptance proof.','Root must explicitly interpret the original interior-grid FAIL separately; this report never flips or overwrites it.'],
                'first_report_overwritten':False,'model_appearance_accepted':False,'native_or_browser_passed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--structure-proof',type=Path,required=True);p.add_argument('--first-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();need(out.is_relative_to(HERE) and not out.exists(),'Use new report within independent-review')
    try:r=LipAudit(a.raw.resolve(),a.structure_proof.resolve(),a.first_report.resolve()).run()
    except Exception as e:r={'schema':'zhenru-actual-cover-pan-piecewise-intersection-v1','strict_edge_band_contact_passed':False,'error':str(e),'model_appearance_accepted':False}
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:r.get(k) for k in ['strict_edge_band_contact_passed','pair_count','failed_pair_count','minimum_positive_contact_projected_area_m2','minimum_five_station_contact_width_m','error']}))
    raise SystemExit(0 if r['strict_edge_band_contact_passed'] else 1)


if __name__=='__main__':main()
