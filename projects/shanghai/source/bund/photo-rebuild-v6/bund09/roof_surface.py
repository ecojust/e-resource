"""Finite-thickness roof tiles clipped to continuous modeled roof domains.

The source polygon and1.95m inset/1.40m rise remain estimates from the previous
candidate. Voronoi domains assign tile directions, not measured roof hips.
All height evaluation uses the same distance-to-source-boundary surface.
"""
import math
import numpy as np
from collections import Counter
from shapely import constrained_delaunay_triangles, voronoi_polygons, points as shape_points, distance as shape_distance
from shapely.geometry import Polygon, Point, MultiPoint, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from photo_architecture import pieces


def build_roof(builder, polygon, edges, eaves):
    inset=1.95;rise=1.40;pitch=rise/inset;normal_scale=math.sqrt(1+pitch*pitch)
    inner=polygon.buffer(-inset,join_style=2);ring=polygon.difference(inner)
    if inner.is_empty:raise ValueError('Roof inset failed')
    boundary=polygon.boundary
    def height(xy):return eaves+rise*min(1.,boundary.distance(Point(*xy))/inset)
    def heights(xy):return eaves+rise*np.minimum(1.,shape_distance(boundary,shape_points(xy))/inset)
    # Dense line-site Voronoi is only an orientation partition. The shared
    # global height function, not each edge's local plane, defines every vertex.
    sites=[];owners=[]
    for i,f in enumerate(edges):
        count=max(2,math.ceil(f.length/.18))
        for k in range(count):sites.append((f.a+f.t*(k+.5)*f.length/count)[:2]);owners.append(i)
    cells=voronoi_polygons(MultiPoint(sites),extend_to=polygon.envelope,ordered=True)
    by_owner=[[] for _ in edges]
    for cell,i in zip(cells.geoms,owners):
        clipped=cell.intersection(ring)
        if not clipped.is_empty:by_owner[i].append(clipped)
    domains=[unary_union(items).simplify(1e-9,preserve_topology=True) for items in by_owner]
    all_domains=unary_union(domains);domain_error=all_domains.symmetric_difference(ring).area
    assert domain_error<1e-8
    overlap=sum(domains[i].intersection(domains[j]).area for i in range(len(domains)) for j in range(i))
    assert overlap<1e-8

    def subdivide(tris):
        result=[]
        for a,b,c in tris:
            ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
            result.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
        return result

    def interpolation_errors(tris):
        array=np.asarray(tris);weights=np.array([(1/3,1/3,1/3),(.5,.5,0),(0,.5,.5),(.5,0,.5)])
        zs=heights(array.reshape(-1,2)).reshape(-1,3)
        samples=np.einsum('ij,kjl->kil',weights,array)
        linear=zs@weights.T;actual=heights(samples.reshape(-1,2)).reshape(-1,4)
        return np.max(np.abs(linear-actual),axis=1)

    def interpolation_error(tris):return float(interpolation_errors(tris).max())

    def refine_tile_surface(plan):
        """Refine curved triangles with propagated edge splits, not whole tiles.

        One marked edge is split on both adjacent triangles. This keeps a
        conforming closed tile while avoiding million-triangle uniform grids.
        """
        pts=[];lookup={};triangles=[]
        def idx(point):
            key=tuple(round(float(v),9) for v in point)
            if key not in lookup:lookup[key]=len(pts);pts.append(np.array(key))
            return lookup[key]
        for tri in plan:triangles.append(tuple(idx(p) for p in tri))
        for level in range(10):
            actual=np.array([[pts[i] for i in tri] for tri in triangles]);errors=interpolation_errors(actual)
            bad=errors>.002
            if not bad.any():return actual,float(errors.max())
            marked=set()
            for tri in np.array(triangles)[bad]:
                for a,b in zip(tri,np.roll(tri,-1)):marked.add(tuple(sorted((int(a),int(b)))))
            mids={edge:idx((pts[edge[0]]+pts[edge[1]])/2) for edge in marked};new=[]
            for tri in triangles:
                edges=[tuple(sorted((tri[k],tri[(k+1)%3]))) for k in range(3)]
                flags=[edge in mids for edge in edges];count=sum(flags)
                if count==0:new.append(tri)
                elif count==1:
                    k=flags.index(True);a,b,c=tri[k:]+tri[:k];m=mids[tuple(sorted((a,b)))];new.extend([(a,m,c),(m,b,c)])
                elif count==2:
                    k=(flags.index(False)+1)%3;a,b,c=tri[k:]+tri[:k]
                    ab=mids[tuple(sorted((a,b)))];bc=mids[tuple(sorted((b,c)))];new.extend([(b,bc,ab),(a,ab,bc),(a,bc,c)])
                else:
                    a,b,c=tri;ab=mids[edges[0]];bc=mids[edges[1]];ca=mids[edges[2]];new.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
            triangles=new
        raise ValueError('Tile curved-surface refinement did not converge')

    # Roof support follows exactly the same continuous surface as the tiles.
    # It sits25mm below it; the retained inset cap overlaps that small setback.
    support_triangles=0;support_error=0.
    for domain in domains:
        for component in pieces(domain):
            for t in constrained_delaunay_triangles(component).geoms:
                pending=[(np.array(list(orient(t,1.).exterior.coords)[:3]),0)]
                while pending:
                    tri,level=pending.pop();err=interpolation_error([tri])
                    if err>.002 and level<9:
                        pending.extend((np.array(x),level+1) for x in subdivide([tri]));continue
                    assert err<.003,('Support curvature tolerance',err)
                    support_error=max(support_error,err)
                    builder.add([(x,y,height((x,y))-.025) for x,y in tri],[(0,1,2)],'gray roof tile','roof-hip-surface-sheet')
                    support_triangles+=1
    builder.plan_prism(inner,eaves+rise-.09,eaves+rise,'roof zinc','concealed-roof-core-closure-estimate')

    # A complete corrugated tile has a rounded cover ridge and a shallow pan
    # valley, with a constant9mm vertical section thickness before slope scale.
    # Combining those two portions avoids intersecting cover/pan solids at laps.
    theta=np.linspace(math.pi,0,9)
    profile=[(-.11,.020),(-.075,.026)]
    profile += [(.06*math.cos(a),.034+.06*math.sin(a)) for a in theta]
    profile += [(.075,.026),(.11,.020)]
    profile.sort();knots=np.array([p[0] for p in profile]);tops=np.array([p[1] for p in profile])
    tile_thickness=.009;course=.26;tile_length=.32;lap_lift=.020
    # Same-column overlap is intentional and has strictly positive clearance.
    overlap_clearance=(lap_lift*course/tile_length-tile_thickness)*normal_scale
    assert overlap_clearance>.002
    total_tiles=0;tile_tris=0;max_curve_error=0.;tile_domains=[];domain_reports=[];sliver_area=0.

    def add_tile(f,cut,u,d0,d1,mat,label):
        nonlocal tile_tris,max_curve_error,sliver_area
        plan=[]
        # Split at every section knot. CDT therefore never approximates across
        # a raised ridge or a pan-valley corner with one flat face.
        for x0,x1 in zip(knots,knots[1:]):
            strip=Polygon([f.point(u+x0,0,-d0)[:2],f.point(u+x1,0,-d0)[:2],f.point(u+x1,0,-d1)[:2],f.point(u+x0,0,-d1)[:2]])
            clipped=cut.intersection(strip)
            for part in pieces(clipped):
                for t in constrained_delaunay_triangles(part.simplify(1e-9,preserve_topology=True)).geoms:
                    if t.area<1e-11:sliver_area+=t.area;continue
                    plan.append(np.array(list(orient(t,1.).exterior.coords)[:3]))
        if not plan:return 0
        area=sum(abs(np.cross(t[1]-t[0],t[2]-t[0]))/2 for t in plan)
        assert abs(area-cut.area)<1e-8,(area,cut.area)
        plan,err=refine_tile_surface(plan)
        assert err<=.002,('Tile curvature tolerance',label,u,d0,err)
        max_curve_error=max(max_curve_error,err)
        # Weld plan points first, then derive the exterior from the triangulated
        # skin itself. This preserves all boundary subdivisions without T edges.
        points=[];lookup={};tris=[]
        def index(p):
            key=tuple(round(float(x),9) for x in p)
            if key not in lookup:lookup[key]=len(points);points.append(np.array(key))
            return lookup[key]
        for tri in plan:
            ids=tuple(index(p) for p in tri)
            if len(set(ids))==3:tris.append(ids)
        counts=Counter();direct={}
        for tri in tris:
            for a,b in zip(tri,tri[1:]+tri[:1]):
                key=tuple(sorted((a,b)));counts[key]+=1;direct[key]=(a,b)
        assert max(counts.values())<=2
        vertices=[]
        for low in [True,False]:
            for xy in points:
                relative=xy-f.center[:2];x=float(relative@f.t[:2])-u;d=float(-relative@f.n[:2])
                top=float(np.interp(x,knots,tops));lift=lap_lift*(d1-d)/(d1-d0)
                z=height(xy)+normal_scale*(top+lift-(tile_thickness if low else 0))
                vertices.append((xy[0],xy[1],z))
        n=len(points);faces=[]
        for a,b,c in tris:faces.extend([(a,c,b),(a+n,b+n,c+n)])
        for edge,count in counts.items():
            if count==1:
                a,b=direct[edge];faces.append((a,b,b+n,a+n))
        builder.add(vertices,faces,mat,label);tile_tris+=sum(len(f)-2 for f in faces)
        return len(tris)

    # Every observed/front-facing edge is tiled, including the short facets
    # previously excluded12–14 and the slope joins10/16. Rear domains0–8 remain
    # explicitly inferred support, not newly claimed photographic tile detail.
    for index in range(9,19):
        f=edges[index];domain=domains[index];covered=[]
        coords=[p for part in pieces(domain) for p in part.exterior.coords]
        local=np.array([[(np.array(p)-f.center[:2])@f.t[:2],-(np.array(p)-f.center[:2])@f.n[:2]] for p in coords])
        umin,dmin=local.min(0);umax,dmax=local.max(0)
        for row in range(math.floor(dmin/course)-1,math.ceil(dmax/course)+1):
            d0=row*course;d1=d0+tile_length
            for col in range(math.floor((umin-.11)/.22),math.ceil((umax+.11)/.22)+1):
                u=col*.22
                tile=Polygon([f.point(u-.11,0,-d0)[:2],f.point(u+.11,0,-d0)[:2],f.point(u+.11,0,-d1)[:2],f.point(u-.11,0,-d1)[:2]])
                cut=domain.intersection(tile)
                if cut.is_empty:continue
                for part in pieces(cut):
                    if part.area<1e-10:sliver_area+=part.area;continue
                    mat='gray roof tile light' if (row+col+index)%7==0 else 'gray roof tile'
                    if add_tile(f,part,u,d0,d1,mat,f'roof-v3-edge-{index}-clipped-lapped-tile'):
                        covered.append(part);total_tiles+=1
        coverage=unary_union(covered);missing=domain.difference(coverage);outside=coverage.difference(domain)
        assert missing.area<1e-7 and outside.area<1e-8,(index,missing.area,outside.area)
        tile_domains.append(coverage);domain_reports.append({'source_edge':index,'domain_m2':domain.area,'coverage_m2':coverage.area,'uncovered_m2':missing.area,'outside_domain_m2':outside.area,'tile_solids':len(covered)})
    target=unary_union([domains[i] for i in range(9,19)]);covered=unary_union(tile_domains)
    # Reuse the one photographed hip-cap path with finite, nonintersecting laps.
    # The centerline is an estimated bisector of the frozen rounded-return chain.
    chain=[edges[i] for i in [12,13,14]];remaining=sum(f.length for f in chain)/2
    for f in chain:
        if remaining<=f.length:lowxy=(f.a+f.t*remaining)[:2];break
        remaining-=f.length
    inward=-sum((f.n[:2] for f in chain),np.zeros(2));inward/=np.linalg.norm(inward)
    lo=0.;hi=4.5
    for _ in range(36):
        mid=(lo+hi)/2
        if boundary.distance(Point(*(lowxy+inward*mid)))<inset:lo=mid
        else:hi=mid
    highxy=lowxy+inward*hi;low=np.r_[lowxy,height(lowxy)];high=np.r_[highxy,height(highxy)]
    down=low-high;span=np.linalg.norm(down);down/=span;side=np.cross([0.,0.,1.],down);side/=np.linalg.norm(side);normal=np.cross(down,side)
    # Cap top stays above the maximum field-ridge height; constant section
    # thickness and22mm lap lift give positive clearance between cap courses.
    cap_top=[(.105*math.cos(a),.165+.105*math.sin(a)) for a in np.linspace(math.pi,0,11)]
    cap=Polygon(cap_top+[(x,z-.010) for x,z in reversed(cap_top)])
    cap_count=0;cap_envelope_clearances=[]
    for start in np.arange(0,span-.05,.30):
        length=min(.37,span-start);base=high+down*start
        def mapper(x,y,d,base=base,length=length):return base+side*x+normal*(y+.022*d/length)+down*d
        builder.prism(cap,0,length,mapper,'gray roof tile light','roof-v3-observed-rounded-return-hip-cap');cap_count+=1
        for x,y in cap_top:
            for d in np.linspace(0,length,15):
                pt=mapper(x,y-.010,d)
                if polygon.covers(Point(*pt[:2])):
                    field_envelope=height(pt[:2])+normal_scale*(float(tops.max())+lap_lift)+max_curve_error
                    cap_envelope_clearances.append(float(pt[2]-field_envelope))
    assert min(cap_envelope_clearances)>.003
    report={'schema':'bund09-roof-v3-continuous-clipped-tiles-v1','passed':True,'source_perimeter_unchanged':True,'inset_m':inset,'rise_m':rise,'height_policy':'One shared eaves+rise*min(distance_to_original_boundary/inset,1) surface for every tile vertex; estimated geometry, not surveyed roof height','orientation_partition':'Dense boundary-site Voronoi only chooses tile direction; all19domains cover source skirt. Short edge domains retained.','domain_partition_symmetric_difference_m2':domain_error,'domain_pairwise_overlap_m2':overlap,'observed_direction_edges':list(range(9,19)),'tile_solids':total_tiles,'tile_triangles':tile_tris,'tiles_plan_uncovered_m2':target.difference(covered).area,'tile_domain_reports':domain_reports,'maximum_tile_surface_interpolation_error_m':max_curve_error,'support_triangles':support_triangles,'maximum_support_surface_error_m':support_error,'support_offset_below_surface_m':.025,'dropped_numerical_sliver_area_m2':sliver_area,'same_column_lap_minimum_clearance_m':overlap_clearance,'conservative_lap_clearance_after_surface_interpolation_m':overlap_clearance-2*max_curve_error,'tile_profile':'Rounded cover ridge and shallow pan valley are one closed corrugated tile section;9mm section thickness. Adjacent columns meet without plan-area overlap. Course overlap60mm horizontally,20mm lift.','cap_tile_count':cap_count,'cap_vs_tile_field_envelope_minimum_sampled_clearance_m':min(cap_envelope_clearances),'cap_clearance_sample_count':len(cap_envelope_clearances),'cap_policy':'One photographed rounded-return cap path; estimated bisector. Cap lifted above tile-field ridges;22mm lap lift and10mm thickness.','limits':['Exact tile sizes, lap, roof-domain directions and hip path remain estimates','Hidden rear domains0–8 and broad inset cap not newly asserted as photographed','Plan coverage and analytical course clearance do not constitute a whole-building Boolean union or visual acceptance']}
    builder.roof_surface_report=report
    return inner,rise
