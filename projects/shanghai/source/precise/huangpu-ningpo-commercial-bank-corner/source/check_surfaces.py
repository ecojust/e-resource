"""Measure front-facing surfaces of the three street faces in exported bank geometry."""
from math import asin, cos, pi, sin, tau
import json
from pathlib import Path

import numpy as np


def check_triangles(triangles, materials, distant):
    """Accept actual detached triangles in author X/Y/Z metres, with one material per triangle."""
    source=Path(__file__).resolve().parent
    edges=np.asarray(json.loads((source/'frontage-registration.json').read_bytes())['visible_edges_local_m'])
    vertices=np.asarray(triangles,dtype=float)
    if len(materials)!=len(vertices) or vertices.shape[1:]!=(3,3):
        raise ValueError('A material and three XYZ vertices are required for each triangle')
    stone='dressed warm grey stone'
    granite='bush-hammered granite'
    metal='dark bronze'
    glass='recessed blue-grey glazing'
    rows=[]
    for edge,(a,b) in enumerate(zip(edges,edges[1:])):
        tangent=(b-a)/np.linalg.norm(b-a)
        normal=np.array([tangent[1],-tangent[0]])
        centered=vertices[:,:,:2]-(a+b)/2
        x=centered@tangent
        z=vertices[:,:,2]
        depth=centered@normal
        dx1=x[:,1]-x[:,0];dx2=x[:,2]-x[:,0]
        dz1=z[:,1]-z[:,0];dz2=z[:,2]-z[:,0]
        denominator=dx1*dz2-dx2*dz1
        front=denominator>1e-10
        def ray(name,u,h,expected,lo,hi):
            v=(u-x[:,0])*dz2-(h-z[:,0])*dx2
            t=(h-z[:,0])*dx1-(u-x[:,0])*dz1
            good=front&(v>=-1e-10)&(t>=-1e-10)&(v+t<=denominator+1e-10)
            idx=np.flatnonzero(good)
            if len(idx):
                d=depth[idx,0]+(v[idx]*(depth[idx,1]-depth[idx,0])+t[idx]*(depth[idx,2]-depth[idx,0]))/denominator[idx]
                visible=d<2.
                idx=idx[visible];d=d[visible]
            if len(idx):
                i=d.argmax();hit=materials[idx[i]];projection=float(d[i])
            else:
                hit=projection=None
            ok=hit==expected and (projection is None or lo-.002<=projection<=hi+.002)
            rows.append({'face':edge,'detail':name,'local_xz_m':[u,h],'hit':hit,'expected':expected,
                         'projection_m':projection,'distance_m':None if projection is None else 2-projection,
                         'expected_projection_m':None if expected is None else [lo,hi],'passed':bool(ok)})

        ray('central arch keystone' if edge==1 else 'street arch keystone',0,5.40 if edge==1 else 5.54,stone,.105,.109)
        ray('street arch jamb',1.455 if edge==1 else 1.245,3.1,stone,.102,.107)
        ray('rusticated wall above spring',1.68,4.42,granite,.027,.031)
        if edge!=1:
            for x0 in [-.52,.18,.59]:
                for h0 in [1.7,2.11,3.41,4.36]:
                    ray('recessed ground arched window',x0,h0,glass,-.321,-.319)
            for x0 in [-.74,-.38,.38,.74]:
                ray('upright iron grille',x0,1.83,metal,-.161,-.157)
            ray('horizontal iron grille',.29,2.76,metal,-.139,-.135)
            ray('granite sill to the street',.12,.86,stone,.237,.243)
            for h0 in [8.12,9.67,12.81,14.13]:
                ray('upper recessed street window',.31,h0,glass,-.321,-.319)
                ray('upper central sash',0,h0,metal,-.162,-.158)
            ray('upper shallow architrave',.999,9.17,stone,.119,.121)
            continue

        for sign in [-1,1]:
            ray('closed entrance glazing',.71*sign,2.57,glass,-.321,-.319)
            ray('closed leaf pull',.54*sign,1.42,metal,-.117,-.113)
            ray('round door column shaft',1.98*sign,2.8,stone,.627,.652)
            ray('square abacus of door column',1.98*sign,6.16,stone,.752,.758)
            ray('giant shaft',1.97*sign,9.02,stone,.624,.631)
            ray('tapered head of giant shaft',1.97*sign,15.39,stone,.564,.577)
            ray('capital neck ring',1.97*sign,15.52,granite,.65,.69)
            ray('capital abacus',1.97*sign,16.064,stone,.775,.784)
            for side in [-1,1]:
                ray('volute on the capital face',1.97*sign+side*.3293,15.80,granite,.65,.662)
        ray('entrance transom',.29,3.80,metal,-.17,-.165)
        ray('meeting rail between entrance leaves',0,2.77,metal,-.162,-.158)
        for x0 in [-.325,.046,.308]:
            for h0 in [13.67,14.095,14.42]:ray('inset oval glazing',x0,h0,glass,-.225,-.223)
        for x0 in [-.19,.19]:
            ray('fine oval sash vertical',x0,14.09,metal,-.146,-.144)
        ray('fine oval sash horizontal',.041,14.04+.85*.23,metal,-.146,-.144)
        ray('oval crown keystone',0,15.08,stone,.154,.156)
        for k in [0,2,9,11,15,18]:
            angle=tau*k/22
            # The relief has a real outward-facing ridge in addition to its continuous backing.
            nx,nz=cos(angle)/.5,sin(angle)/.85;length=(nx*nx+nz*nz)**.5
            x0=.586*cos(angle)+.009*nx/length
            z0=14.04+.936*sin(angle)+.009*nz/length
            ray('front-facing carved oval wreath',x0,z0,stone,.120,.135)
        for name,w,sag,y0,z0,height,count in [('roof',1.23,.32,0,17.66,.82,6),('balcony',1.70,.43,-.52,7.18,.78,9)]:
            radius=(w*w+sag*sag)/(2*sag);halfangle=asin(w/radius)
            for j in range(count+2):
                a0=-halfangle+2*halfangle*j/(count+1);x0=radius*sin(a0)
                proj=-y0+sag-radius*(1-cos(a0))
                if j in (0,count+1):
                    ray(name+' rail end pier',x0,z0+height*.43,granite,proj+.082,proj+.16)
                else:
                    ray(name+' turned baluster',x0,z0+height*.43,stone,proj+.064,proj+.115)
                if j>count:continue
                fraction=.66 if j==0 else (.34 if j==count else .5)
                angle=-halfangle+2*halfangle*(j+fraction)/(count+1)
                x0=radius*sin(angle);proj=-y0+sag-radius*(1-cos(angle))
                # The balcony gaps reveal the recessed rectangular window or the masonry on its sides.
                if name=='roof':
                    ray('sky through roof railing',x0,z0+height*.43,None,0,0)
                elif abs(x0)<1.14:
                    ray('window through lower railing',x0,z0+height*.43,glass,-.322,-.318)
                elif abs(x0)>1.4:
                    ray('wall through edge of lower railing',x0,z0+height*.43,granite,.027,.031)
                ray(name+' continuous coping above gap',x0,z0+height-.03,stone,proj+.143,proj+.182)
    misses=[row for row in rows if not row['passed']]
    if misses:
        raise ValueError(misses)
    return {'distant':bool(distant),'triangles':len(vertices),'rays':rows}
