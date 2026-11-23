"""Test the same recorded-view rays in two emitted models at the upper return's roof joint."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from probe_registered_facade import mesh,HERE

# The two strips were located on the first model-only contact prints. Coordinates
# below refer to those 615-pixel-wide prints, allowing later renders at any width.
strips={'2017':(430,537,138,129),'2015-12-front':(342,437,163,157)}

def intersections(tris,camera,uv):
    start=np.asarray(camera['eye'])
    K,R=np.asarray(camera['K']),np.asarray(camera['R'])
    directions=np.linalg.solve(K,np.c_[uv,np.ones(len(uv))].T).T@R
    result=[(None,float('inf')) for _ in uv]
    for off in range(0,len(tris),4096):
        chunk=tris[off:off+4096]
        a,b,c=[np.asarray([r[k] for r in chunk]) for k in range(3)]
        ac=start-a;q=np.cross(ac,b);v0=np.einsum('ij,ij->i',c,q)
        for i,d in enumerate(directions):
            p=np.cross(d,c);det=np.einsum('ij,ij->i',b,p);det[np.abs(det)<1e-12]=np.nan
            u=np.einsum('ij,ij->i',ac,p)/det;v=(q@d)/det;t=v0/det
            good=(u>=0)&(v>=0)&(u+v<=1)&(t>0)&(t<result[i][1])
            if np.any(good):
                k=np.nanargmin(np.where(good,t,np.inf));result[i]=(chunk[k][3],float(t[k]))
    return result

def main(before,after,images,dst):
    cams=json.loads((HERE/'street-cameras.json').read_bytes())['cameras']
    pts={};native={}
    for key,(a,b,ya,yb) in strips.items():
        pic=Image.open(images/(key+'-model.jpg')).convert('RGB')
        unit=pic.width/615; chosen=[]
        for x in range(a,b,5):
            centre=ya+(x-a)*(yb-ya)/(b-a)
            samples=[(round(unit*x),round(unit*(centre+j)))for j in (-2,-1,0,1,2)]
            best=max(samples,key=lambda p:sum(pic.getpixel(p)))
            brightness=min(pic.getpixel(best))
            if brightness>=177:chosen.append(best)
        pts[key]=chosen;native[key]=[[(x+.5)*cams[key]['size'][0]/pic.width-.5,(y+.5)*cams[key]['size'][1]/pic.height-.5]for x,y in chosen]
    reports={}
    for key,model in [('before',before),('after',after)]:
        tris,digest=mesh(model)
        readings={k:intersections(tris,cams[k],values)for k,values in native.items()}
        reports[key]={'mesh':digest,'hits':readings}
        del tris
    public={}
    for k in pts:
        rows=[]
        for uv,local,old,new in zip(native[k],pts[k],reports['before']['hits'][k],reports['after']['hits'][k]):
            if old[0] is not None:continue
            rows.append({'render_px':local,'native_photo_px':uv,'old_first_surface':old[0],'new_first_surface':new[0]})
        public[k]={'original_open_sky_count':len(rows),'now_obstructed':sum(p['new_first_surface'] is not None for p in rows),'points':rows}
    doc={'before_sha256':reports['before']['mesh'],'after_sha256':reports['after']['mesh'],'method':'The bright band was localized in the old model-only image. Each pixel centre was lifted to the native photographic camera. Full GLB intersections were calculated independently; rays hitting an old surface were discarded.','views':public}
    dst.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
    print({k:(v['original_open_sky_count'],v['now_obstructed'])for k,v in public.items()})
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for x in ('before','after','previous_renders','output'):p.add_argument(x,type=Path)
    a=p.parse_args();main(a.before,a.after,a.previous_renders,a.output)
