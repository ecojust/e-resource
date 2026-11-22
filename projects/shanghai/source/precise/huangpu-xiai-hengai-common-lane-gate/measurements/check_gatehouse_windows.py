"""Read an actual GLB and verify the first contacts on the photographed window and sash features."""
import argparse
from pathlib import Path
import sys
import json

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"source"))
sys.path.insert(0,str(HERE.parents[1]/"xuhui-pathe-records-office"/"measurements"/"city-contact"))
from glb_triangles import SerialScene
from gatehouse_upper_windows import openings,leaf_axes,TIMBER,BAR,GLASS,LOWER,CASING,LEDGE,CANOPY,SHADOW,BEAD


def expected_front_at_jamb(row,x,z):
    """Analytic 2-D slab intersections, independent of the exported triangles."""
    o=np.array([x,-1.,z]); front=-.042; material=CASING
    for i in (0,1):
        h,d,n=leaf_axes(row,i)
        z0,z1=row["bottom"]+.028,row["top"]-.030
        ww=(row["right"]-row["left"])/2-.026
        blocks=[(0,.032,-.018,.022,TIMBER),(ww-.032,ww,-.018,.022,TIMBER)]
        level=(z-z0)/(z1-z0)
        if z<z0+.045 or z>z1-.040:
            blocks.append((.032,ww-.032,-.015,.019,TIMBER))
        elif min(abs(level-r)*(z1-z0) for r in (.248,.5,.755))<.012:
            blocks.append((.032,ww-.032,-.015,.019,BAR))
        else:
            blocks.append((.032,ww-.032,.003,.010,GLASS if level>.50 else LOWER))
        for lo,hi,lower,upper,mat in blocks:
            intervals=[]
            for axis,low,high in [(d,lo,hi),(n,lower,upper)]:
                origin=(o-h)@axis
                if abs(axis[1])<1e-9:
                    intervals.append((-np.inf,np.inf) if low<=origin<=high else (np.inf,-np.inf))
                else:
                    intervals.append(tuple(sorted(((low-origin)/axis[1],(high-origin)/axis[1]))))
            near=max(v[0] for v in intervals);far=min(v[1] for v in intervals)
            if 0 <= near <= far and -1+near < front:
                front=-1+near;material=mat
    return front,material


def probes():
    for row in openings():
        l,r,z0,z1=[row[k] for k in ("left","right","bottom","top")]
        norm=np.array([0.,1.,0.]);mid=(z0+z1)/2
        for x in (l-.065,r+.061):
            for z in (z0+.13,mid,z1-.13):
                yield row["key"]+" mineral jamb close contact",np.array([x,-.042,z]),norm,CASING,.012
                if row["key"]=="right":
                    y,first=expected_front_at_jamb(row,x,z)
                    yield "right opening street ray in front of jamb",np.array([x,y,z]),norm,first,y+1.
        for ratio in (.25,.75):
            x=l+(r-l)*ratio
            yield row["key"]+" cap front edge",np.array([x,-.071,z1+.038]),norm,CASING,.17
            yield row["key"]+" broad sill front",np.array([x,-.114,z0-.035]),norm,LEDGE,.36
        if row["key"]=="left":
            yield "left canopy outer drip",np.array([(l+r)/2,-.345,z1+.098]),norm,CANOPY,.32
        else:
            for z in (mid,z0+.31,z1-.33):
                yield "right clear open centre",np.array([(l+r)/2,.405,z]),norm,SHADOW,.84
        for i in (0,1):
            h,d,n=leaf_axes(row,i);zb=z0+.028;zt=z1-.030;ww=(r-l)/2-.026
            def sample(t,down,x,z,mat,name):
                return (f"{row['key']} leaf {i+1} {name}",h+d*x+np.array([0.,0.,z])+n*t,down,mat,.032)
            # Check the actual outermost face of each leaf. On a turned leaf
            # the reverse, facing the street, is the visible face of the timber.
            for x in (.015,ww-.015):
                outside=(.022,-n) if n[1]<0 else (-.018,n)
                for ratio in (.2,.63):
                    yield sample(*outside,x,zb+(zt-zb)*ratio,TIMBER,"stile")
            for ratio in (.248,.500,.755):
                z=zb+(zt-zb)*ratio
                for x in (ww*.26,ww*.75):
                    outside=(.019,-n) if n[1]<0 else (-.015,n)
                    yield sample(*outside,x,z,BAR,"subdivision")
            for m,frac in enumerate((.133,.377,.625,.872)):
                for x in (ww*.31,ww*.65):
                    outside=(.010,-n) if n[1]<0 else (.003,n)
                    yield sample(*outside,x,zb+(zt-zb)*frac,GLASS if m>=2 else LOWER,"glass")


def rebate_samples(level):
    """Probe all four rebate strips on each of four lights, including the swung leaves."""
    for row in openings():
        width=(row["right"]-row["left"])/2-.026
        bottom,top=row["bottom"]+.028,row["top"]-.030
        bands=[(bottom,bottom+.045),(top-.040,top)]
        for fraction in (.248,.500,.755):
            z=bottom+(top-bottom)*fraction
            bands.append((z-.012,z+.012))
        bands.sort()
        for index in (0,1):
            hinge,d,n=leaf_axes(row,index)
            for light in range(4):
                low,high=bands[light][1],bands[light+1][0]
                edges=(("hinge",.0345,(low+high)/2),("meeting",width-.0345,(low+high)/2),
                       ("bottom",width*.44,low+.0025),("top",width*.44,high-.0025))
                for edge,s,z in edges:
                    mat=BEAD if level=="full" else (GLASS if light>=2 else LOWER)
                    depth=-.005 if level=="full" else .003
                    label=f"{row['key']} leaf {index+1} light {light+1} {edge}"
                    yield label,hinge+d*s+n*depth+np.array([0.,0.,z]),n,mat


def check_rebates(scene,level):
    result=[]
    for feature,point,normal,material in rebate_samples(level):
        hit=scene.ray(point-normal*.008,normal,.020)
        error=None if hit is None else float(np.linalg.norm(np.asarray(hit["point_enu_m"])-point))
        result.append({"feature":feature,"expected_xyz_m":point.round(6).tolist(),
                       "expected_material":material,"actual_material":None if hit is None else hit["material"],
                       "error_m":error,"passed":error is not None and error<.0015 and hit["material"]==material})
    return {"level":level,"count":len(result),"passed":bool(result) and all(row["passed"] for row in result),
            "checks":result}


def check(model,dest,level=None):
    scene=SerialScene(model);rows=[]
    for name,p,d,material,gap in probes():
        hit=scene.ray(p-d*gap,d,gap+.010)
        delta=None if hit is None else float(np.linalg.norm(hit["point_enu_m"]-p))
        rows.append({"feature":name,"expected_material":material,"expected_local_xyz_m":p.round(6).tolist(),"actual_material":None if hit is None else hit["material"],"error_m":delta,"passed":hit is not None and hit["material"]==material and delta<.006})
    report={**scene.asset,"triangles":len(scene.tri),"rays":len(rows),"passed":all(r["passed"] for r in rows),"checks":rows}
    if level is not None:
        report["lod_rebates"]=check_rebates(scene,level)
        report["passed"]=report["passed"] and report["lod_rebates"]["passed"]
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print(model.name,len(scene.tri),sum(r["passed"] for r in rows),len(rows));return report["passed"]


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("model",type=Path);p.add_argument("report",type=Path);p.add_argument("--level",choices=("full","lod"));args=p.parse_args();raise SystemExit(0 if check(args.model,args.report,args.level) else 1)
