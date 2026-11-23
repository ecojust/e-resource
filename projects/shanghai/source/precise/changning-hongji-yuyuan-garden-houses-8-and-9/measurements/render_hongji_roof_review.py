"""Draw original survey plates by projecting the exported triangles of each house."""
from pathlib import Path
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from check_hongji_roofs import map_frame, read, M, COVER, STACK, TILES, SerialScene
from hongji_roof_geometry import BRICK,PEBBLE,TILE8,TILE9,STONE,CAP,FLASH,EAVE,SOFFIT,VERGE

PAPER=(247,245,239);INK=(43,47,45);GREY=(98,102,96)
def font(n):
    try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
    except OSError:return ImageFont.load_default()
def fill(mat):
    cols={TILE8:(184,104,76),TILE9:(155,86,69),BRICK:(159,93,70),PEBBLE:(191,183,158),
          STONE:(202,193,171),CAP:(141,83,59),FLASH:(117,126,120),EAVE:(75,80,77),
          SOFFIT:(207,193,156),VERGE:(98,106,107)}
    if mat in cols:return cols[mat]
    k=mat.lower()
    if 'glass'in k:return (86,122,119)
    if 'frame'in k or 'metal'in k or 'wood'in k:return (67,68,61)
    if 'hedge'in k or 'planted'in k or 'shrub'in k:return (103,114,78)
    if 'brick'in k:return(163,106,83)
    return(188,181,160) if 'render'in k or 'pebble'in k else (199,194,175)

def select(scene,n,roof,local):
    offset,basis=map_frame(n)
    xyz=scene.tri if local else (scene.tri-offset)@np.linalg.inv(basis).T
    center=xyz.mean(axis=1)
    bounds=(center[:,0]>-7.5)&(center[:,0]<15.)&(center[:,1]>-1.35)&(center[:,1]<25.)
    if roof:
        allowed=(COVER|STACK[n])-{TILES[17-n]}
        bounds &= np.isin(scene.mi,[k for k,mat in enumerate(scene.materials)if mat in allowed])
    return xyz[bounds],scene.mi[bounds]
def paint(image,xyz,colors,project,face=None):
    d=ImageDraw.Draw(image)
    coord,dep=project(xyz)
    normal=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1.e-12)
    shade=.78+.22*np.maximum(0,normal@np.array([.42,-.35,.83]))
    valid=dep.min(axis=1)>.08
    if face is not None:valid &=face
    for i in np.argsort(-dep.mean(axis=1)):
        if not valid[i]:continue
        q=coord[i]
        if q[:,0].max()<0 or q[:,1].max()<0 or q[:,0].min()>image.width or q[:,1].min()>image.height:continue
        d.polygon([tuple(v)for v in q],fill=tuple((colors[i]*shade[i]).astype(int)))
def orthographic(w,h,vec):
    eye=np.array(vec,dtype=float);eye/=np.linalg.norm(eye)
    u=np.cross([0.,0.,1.],eye);u/=np.linalg.norm(u);v=np.cross(eye,u)
    def camera(tri):
        ox=tri@u;oy=-tri@v
        s=min((w-44)/(ox.max()-ox.min()),(h-34)/(oy.max()-oy.min()))
        return np.stack([(ox-(ox.min()+ox.max())/2)*s+w/2,(oy-(oy.min()+oy.max())/2)*s+h/2],axis=-1),300-tri@eye
    return camera

def main(mesh,out,component_dir=None):
    scene=SerialScene(mesh) if mesh else None
    im=Image.new('RGB',(1350,1015),PAPER);d=ImageDraw.Draw(im)
    d.text((32,20),'Garden houses 8 and 9  ·  roof survey',font=font(32),fill=INK)
    d.text((34,69),'1107 Yuyuan Road, Shanghai   /   Local geometry from the two separately identified garden elevations',
           font=font(16),fill=GREY)
    for j,n in enumerate((8,9)):
        s=scene or SerialScene(component_dir/f'{n}-near.glb')
        tri,mi=select(s,n,True,scene is None)
        colors=np.asarray([fill(s.materials[int(k)])for k in mi],dtype=float)
        clip=Image.new('RGB',(647,305),PAPER)
        paint(clip,tri,colors,orthographic(647,305,(-.75,-1.,.85) if n==8 else (1.,.6,.91)))
        x=24+j*659;im.paste(clip,(x,109))
        d.text((x+8,421), 'No. 8   /   transverse clipped hip' if n==8 else 'No. 9   /   stepped pair of north gables',font=font(22),fill=INK)
        d.text((x+8,457), 'Outer eave 4.34 m; cropped summit 6.63 m.' if n==8 else 'Foreground summit 7.77 m; higher gable 8.93 m.',font=font(15),fill=GREY)
    d.line((34,499,1314,499),fill=(185,183,173))
    records=read(M/'nine-north-windows-and-stepped-gables.json')['views']
    for j,n in enumerate(('20','22')):
        s=scene or SerialScene(component_dir/'north-windows-near.glb')
        tri,mi=select(s,9,False,scene is None)
        colors=np.asarray([fill(s.materials[int(k)])for k in mi],dtype=float)
        cam=records[n];P=np.array(cam['P']);W,H=cam['native_dimensions'];scale=min(640/W,355/H)
        clip=Image.new('RGB',(640,355),PAPER)
        def projection(tr):
            p=tr@P[:,:3].T+P[:,3]
            half=np.array([(640-W*scale)/2,(355-H*scale)/2])
            return p[:,:,:2]/np.maximum(p[:,:,2:3],1.e-7)*scale+half,p[:,:,2]
        paint(clip,tri,colors,projection)
        x=30+j*659;im.paste(clip,(x,515))
        d.text((x+4,887),'North view '+n+'  /  original camera projection',font=font(19),fill=INK)
    d.text((34,936),'The two northern views overlap on the same plaster. The low window heads are visible above the planting; sill heights are estimates.',font=font(15),fill=GREY)
    tag=scene.asset['sha256'][:20] if scene else 'local component study'
    d.text((34,970),'Original model projection   ·   Mesh '+tag+'   ·   2023 photographs credited to wwj1955 are documented in the measurements.',font=font(14),fill=GREY)
    im.save(out,quality=88,optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mesh',type=Path);p.add_argument('--component-dir',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();main(a.mesh,a.out,a.component_dir)
