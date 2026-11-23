"""Render the published meshes in the measured oblique camera and review actual first surfaces."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from check_actual_meshes import mesh,digest
def render(path,projected,w,h):
    tri,idx,mats,_,uv,tile=mesh(path,with_texture=True);xyz,depth=projected(tri)
    colors=np.array([m['pbrMetallicRoughness']['baseColorFactor'][:3]for m in mats])
    textured=[i for i,m in enumerate(mats) if 'baseColorTexture' in m['pbrMetallicRoughness']]
    th,tw,_=tile.shape
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
    shading=.68+.32*np.maximum(0,normal@np.array([-.35,-.48,.803]))
    canvas=np.full((h,w,3),[232,231,222],np.uint8);distance=np.full((h,w),-1e9)
    for n,(points,z) in enumerate(zip(xyz,depth)):
        lo=np.maximum(np.floor(points.min(0)).astype(int),0);hi=np.minimum(np.ceil(points.max(0)).astype(int),[w-1,h-1])
        if np.any(hi<lo):continue
        x,y=points[:,0],points[:,1];det=(y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if abs(det)<1e-10:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
        a=((y[1]-y[2])*(xx-x[2])+(x[2]-x[1])*(yy-y[2]))/det
        b=((y[2]-y[0])*(xx-x[2])+(x[0]-x[2])*(yy-y[2]))/det
        c=1-a-b;values=a*z[0]+b*z[1]+c*z[2];window=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1))
        active=(np.minimum(np.minimum(a,b),c)>=-1e-9)&(values>distance[window])
        distance[window][active]=values[active]
        color=255*colors[idx[n]]
        if idx[n] in textured:
            weights=np.column_stack([a[active],b[active],c[active]])
            u,v=(weights@uv[n]).T
            pixels=tile[np.floor(v*th).astype(int)%th,np.floor(u*tw).astype(int)%tw]
            color=pixels*colors[idx[n]]
        canvas[window][active]=np.clip(color*shading[n],0,255).astype(np.uint8)
    return Image.fromarray(canvas)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('geometry',type=Path);args=ap.parse_args();folder=args.geometry
    q=json.loads((folder/'mesh-and-photo-check.json').read_text())
    az,el,scale,cx,cy=q['photo']['camera_azimuth_elevation_scale_origin']
    along=np.array([math.cos(az),math.sin(az),0]);up=np.array([-math.sin(az)*math.sin(el),math.cos(az)*math.sin(el),math.cos(el)]);toward=np.cross(along,up)
    def photo(tri):
        return np.stack(((cx+scale*(tri@along)-185)*2.25,(cy-scale*(tri@up)-75)*2.25),axis=-1),tri@toward
    def roof(tri):
        return np.stack(((tri[:,:,0]+12)*21,(8-tri[:,:,1])*21),axis=-1),tri[:,:,2]
    board=Image.new('RGB',(1050,720),'#faf8ee');draw=ImageDraw.Draw(board)
    for i,role in enumerate(['full','lod']):
        p=folder/(role+'-source.glb');im=render(p,photo,525,465);board.paste(im,(i*525,30))
        top=render(p,roof,510,330);top.thumbnail((340,213));board.paste(top,(i*525+92,500));draw.text((i*525+12,8),role+' / 2023 oblique camera',fill='black')
    board.save(folder/'model-comparison.jpg',quality=94)
    print(digest(folder/'model-comparison.jpg'))
if __name__=='__main__':main()
