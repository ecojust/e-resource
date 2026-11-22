"""Trace first intersections on the delivered meshes. Compare raised-letter shadows to the registered original."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy.ndimage import binary_erosion,binary_dilation,distance_transform_edt,map_coordinates,shift
from scipy.signal import correlate,find_peaks
H=Path(__file__).resolve().parent
project=next((p for p in H.parents if (p/'source/precise/hongkou-general-post-office').is_dir()),None)
if project is None:
    import os
    project=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path[:0]=[str(project/'source/precise/xuhui-pathe-records-office/measurements/city-contact'),str(project/'source/precise/jingan-jiaozhou-450-garden-residence/measurements')]
from glb_triangles import SerialScene
from photo_glb_raster import read_glb
from pediment_dimensions import P,plane,pixels,data
# Independently picked interior/bed positions on the native photograph. The tip and shadow of a fine stroke can lie outside its physical top.
POSITIVES={
 '退':[(482,339),(497,337),(508,334),(507,341),(498,344),(503,349),(510,351),(516,345),(490,353),(475,350),(484,357),(496,359),(507,363),(518,362)],
 '耕':[(413,331),(413,337),(402,345),(410,349),(416,348),(408,362),(399,362),(421,360),(432,350),(439,346),(441,340),(439,362),(437,369)],
 '小':[(327,354),(325,357),(344,344),(347,349),(346,354),(342,357),(339,357),(361,352),(364,353),(366,352)],
 '筑':[(263,345),(270,343),(273,350),(268,355),(277,354),(281,349),(290,341),(296,336),(289,346),(287,354),(265,364),(274,363),(286,361),(298,360),(269,371),(277,375),(292,373)]}
NEGATIVES=[(257,340),(264,351),(278,348),(286,352),(283,370),(327,345),(336,347),(341,350),(356,352),(371,347),(399,355),(411,342),(421,354),(429,361),(439,356),(477,345),(487,349),(502,339),(511,349),(518,357),(529,350)]
# Lower edge of the rounded coping above the tablet. Columns differ from the interpolation stations used to author the profile.
EDGE=[(217,245),(256,227),(298,216),(337,208),(380,203),(418,202),(457,204),(499,211),(540,220),(583,237),(619,255),(660,281),(700,309)]
FACES={'glyph':'Limestone | positive running script','field':'Limestone | inscribed field','arc':'Cast stone | rounded arc moulding'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def test(mesh,photo):
    assert sha(photo)==data['source_sha256']
    sc=SerialScene(mesh);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
    def hit(u,v):
        h=sc.ray(eye,inv@[u,v,1],40.);return h['material'] if h else None
    rays=[]
    for group,pts in POSITIVES.items():
        for u,v in pts:
            material=hit(u,v);rays.append(dict(pixel=[u,v],group=group,expected='glyph',actual=material,direct=material==FACES['glyph']))
    for u,v in NEGATIVES:
        mat=hit(u,v);rays.append(dict(pixel=[u,v],group='字间露出的素底',expected='field',actual=mat,direct=mat==FACES['field']))
    edges=[]
    for u,v in EDGE:
        ys=np.arange(v-8,v+8.01,.5);which=[hit(u,y)==FACES['arc']for y in ys];bands=[(ys[i]+ys[i+1])/2 for i in range(len(ys)-1) if which[i] and not which[i+1]]
        found=min(bands,key=lambda k:abs(k-v))if bands else None
        edges.append(dict(photo=[u,v],model_y=found,error_px=None if found is None else float(found-v)))
    mat,bases,tex=read_glb(mesh);mul=3;mask=Image.new('1',(890*mul,500*mul));draw=ImageDraw.Draw(mask);n=0;zero_uv=0
    for xyz,norm,uv,ind,mi,ti in mat:
        ind=ind.reshape(-1,3);n+=len(ind)
        if ti is not None:
            ab=uv[ind[:,1]]-uv[ind[:,0]];ac=uv[ind[:,2]]-uv[ind[:,0]]
            zero_uv+=int((abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])<1e-12).sum())
        if bases[mi]['name']!=FACES['glyph']:continue
        uv=pixels(xyz)*mul
        for tri in ind:draw.polygon([tuple(v)for v in uv[tri]],fill=1)
    glyphmask=np.asarray(mask);rim=glyphmask&~binary_erosion(glyphmask)
    original=Image.open(photo).convert('L');gray=np.asarray(original,float);band=gray-np.asarray(original.filter(ImageFilter.GaussianBlur(4)),float)
    residual=[]
    for g in data['letters']:
        pts=np.concatenate([np.array(s)[:,:2]for s in g['strokes']])+g['offset'];x,y=np.floor(pts.min(0)-4).astype(int);xx,yy=np.ceil(pts.max(0)+4).astype(int)
        sub=glyphmask[y*mul:yy*mul,x*mul:xx*mul];m=rim[y*mul:yy*mul,x*mul:xx*mul]
        # The published image has high-contrast displaced shadow and low-contrast (sometimes unresolved) top faces.
        # Compare its shadow only in the measurement band around the letters; exclude the false line from the tree.
        d=distance_transform_edt(~sub)/mul;uvy,uvx=np.indices(sub.shape);intensity=map_coordinates(band,[y+uvy/mul,x+uvx/mul],order=1)
        lines=(intensity<-18)&(d<5)
        dist=distance_transform_edt(~lines)/mul;errs=dist[m];casts=d[lines]
        residual.append(dict(letter=g['reading'],directed_rim_to_dark_photo_px_median=round(float(np.median(errs)),3),directed_rim_to_dark_photo_px_p90=round(float(np.percentile(errs,90)),3),dark_photo_to_mesh_px_p90=round(float(np.percentile(casts,90)),3),scale_pixels=mul,measured_rim_samples=int(len(errs))))
    # Repeat interval of the top fret from a rectified, locally averaged band of the original photograph.
    xx=np.linspace(-1.225,1.225,640);zz=np.linspace(.68,-.13,213);gx,gz=np.meshgrid(xx,zz);xy=pixels(np.stack((gx,np.zeros_like(gx),gz),-1))
    rect=map_coordinates(band,[xy[...,1],xy[...,0]],order=1);rows=rect[27:60,142:535].copy();rows-=rows.mean(1)[:,None]
    corr=sum(correlate(s,s,mode='full')[len(s)-1:]for s in rows);lag=next(j for j in range(48,62) if corr[j]==max(corr[48:62]));meters=lag*(2.45/639)
    return dict(mesh=mesh.name,sha256=sha(mesh),triangles=n,zero_uv_triangles=zero_uv,photograph_sha256=sha(photo),actual_mesh_rays=rays,ray_hits=sum(r['direct']for r in rays),ray_count=len(rays),coping_lower_edge=edges,glyph_contour_residuals=residual,fret=dict(original_rectified_lag_px=lag,rectified_sampling_m=2.45/639,nominal_interval_from_image_m=meters,model_interval_m=.2107,relative_error_percent=round(abs(meters-.2107)/meters*100,3)),scope='独立像素点及局部暗缘用于评估；低对比字面、投影和铸边不等同。比例按题面宽1.80米推估，实物原尺未取得。')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photo',type=Path);p.add_argument('meshes',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rs=[test(m,a.photo)for m in a.meshes];a.output.write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
    for r in rs:print(r['mesh'],r['ray_hits'],r['ray_count'],r['zero_uv_triangles'],[(z['letter'],z['directed_rim_to_dark_photo_px_p90'])for z in r['glyph_contour_residuals']],r['fret'],[y['error_px']for y in r['coping_lower_edge']])
