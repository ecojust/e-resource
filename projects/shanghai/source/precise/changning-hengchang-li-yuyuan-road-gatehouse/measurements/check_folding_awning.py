"""Check the refurbishment awning, five bows, two pivots and clearance to the cornice."""
import argparse
import hashlib
import json
from math import pi
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from awning import BOW, bow_point
from gatehouse_finishes import LINING, FITTING, CREAM, WINE

LAYOUT=json.loads((HERE.parent/'source/gatehouse-layout.json').read_bytes())
RECORD=HERE/'refurbished-folding-awning.json'


def sections(scene):
    rows=[]
    def cast(label,p,d,expected,n):
        hit=scene.ray(p,d,n)
        rows.append(dict(feature=label,origin=list(p),direction=list(d),material=expected,
                         hit=hit,matched=bool(hit and hit['material']==expected)))
    # Local rays start in the gap between consecutive hoops.
    for hoop,turn in enumerate([0,.28,.57,.79,1.]):
        for q in (.12,.22,.34,.45,.55,.66,.78,.88):
            head=np.array(bow_point(q*pi,turn,LAYOUT))
            normal=np.array([0.,-np.sin(turn*1.16),np.cos(turn*1.16)])
            cast(f'Folding bow {hoop}',head-.085*normal,normal,LINING if hoop==0 else BOW,.16)
    for i,a in enumerate([0,pi]):
        q=np.array(bow_point(a,0,LAYOUT));dx=1 if i==0 else -1
        cast('Axial pin',q-np.array([dx*.16,0,0]),(dx,0,0),FITTING,.24)
    for turn in (.16,.43,.685,.915):
        for q in (.21,.35,.47,.62,.77):
            h=np.array(bow_point(q*pi,turn,LAYOUT))
            cast('Outer burgundy canvas',h+[0,0,.18],(0,0,-1),WINE,.34)
    # Find the two crossings of the fixed hoop and each sloping ledge.
    for h,depth,thick in ((0,.145,.09),(.09,.235,.14),(.23,.27,.066)):
        def diff(t):
            x,y,z=bow_point(t,0,LAYOUT)
            return z-(11.65+h+thick/2+(x+.055)*.25/6.45)
        for lo,hi in ((0.,pi*.5),(pi*.5,pi)):
            for _ in range(32):
                mid=(lo+hi)*.5
                if diff(mid)*diff(lo)>0:lo=mid
                else:hi=mid
            x,_,z=bow_point((lo+hi)/2,0,LAYOUT)
            eye=(x,(-.314-depth)/2,z)
            cast('Free gap to the stone ledge',eye,(0,1,0),CREAM,.33)
            cast('Free gap to the back hoop',eye,(0,-1,0),LINING,.33)
    return rows


def board(mesh, output, doc):
    out=Image.new('RGB',(1370,620),'#f8f5ef');draw=ImageDraw.Draw(out)
    def font(n,bold=False):
        return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',n,index=2)
    draw.text((37,22),'亨昌里南口　更新后的折篷和共轴弓架',font=font(32,True),fill='#332e2d')
    draw.text((38,78),'实网投影与原照片读点。红点为篷顶外轮廓，金点为垂布前缘；右端被枝叶遮住的位置保留空缺。',font=font(18),fill='#423a36')
    tris=mesh.tri
    material={i:name for i,name in enumerate(mesh.materials)}
    allowed=[i for i,m in material.items() if m==BOW or m in (LINING,WINE) or 'awning seam' in m]
    idx=np.flatnonzero(np.isin(mesh.mi,allowed))
    colors={BOW:'#e6d9bc',LINING:'#877a76',WINE:'#94586d'}
    for col,(n,title) in enumerate((('west21','2021年1月11日　西侧'),('east21','2021年1月11日　东侧'),('east20','2020年2月22日　东侧'))):
        view=doc['source_views'][n];p=np.array(view['P']);t=tris[idx]
        q=t@p[:,:3].T+p[:,3];uv=q[:,:,:2]/q[:,:,2,None]
        samples=np.vstack([view['upper_envelope_original_uv'],view['scalloped_front_original_uv']])
        corners=np.vstack([uv.reshape(-1,2),samples]);lo=corners.min(axis=0);hi=corners.max(axis=0);sz=hi-lo
        scale=min(397/sz[0],308/sz[1]);offset=np.array([38+450*col+(397-scale*sz[0])/2,164+(308-scale*sz[1])/2])-lo*scale
        pixels=np.array(out)
        depth=np.zeros(pixels.shape[:2],dtype=np.float32)
        face_normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
        lengths=np.linalg.norm(face_normals,axis=1)
        face_normals/=np.maximum(lengths[:,None],1e-12)
        lighting=.78+.22*np.abs(face_normals@np.array([.3,-.7,.65]))
        face_colors=[]
        for mat_index in mesh.mi[idx]:
            hex_color=colors.get(material[int(mat_index)],'#c8888d')
            face_colors.append([int(hex_color[i:i+2],16) for i in (1,3,5)])
        face_colors=(np.asarray(face_colors)*lighting[:,None]).astype(np.uint8)
        # A z-buffer resolves the many places where metal, hems and cloth
        # overlap in the oblique photographs. Depth is reciprocal camera Z.
        screen=uv*scale+offset
        for face,(triangle,zs) in enumerate(zip(screen,q[:,:,2])):
            low=np.maximum(np.floor(triangle.min(axis=0)).astype(int),[0,0])
            high=np.minimum(np.ceil(triangle.max(axis=0)).astype(int),[pixels.shape[1]-1,pixels.shape[0]-1])
            if np.any(high<low) or zs.min()<=0:continue
            a,b,c=triangle
            det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(det)<1.e-8:continue
            x0,y0=low;x1,y1=high
            ys,xs=np.ogrid[y0:y1+1,x0:x1+1]
            xrel=xs+.5-c[0];yrel=ys+.5-c[1]
            w0=((b[1]-c[1])*xrel+(c[0]-b[0])*yrel)/det
            w1=((c[1]-a[1])*xrel+(a[0]-c[0])*yrel)/det
            w2=1-w0-w1
            local=depth[y0:y1+1,x0:x1+1]
            inv_z=w0/zs[0]+w1/zs[1]+w2/zs[2]
            visible=(w0>=0)&(w1>=0)&(w2>=0)&(inv_z>local)
            local[visible]=inv_z[visible]
            pixels[y0:y1+1,x0:x1+1][visible]=face_colors[face]
        out.paste(Image.fromarray(pixels))
        for field,c in [('upper_envelope_original_uv','#8e202b'),('scalloped_front_original_uv','#fac65e')]:
            for src in view[field]:
                u,v=np.array(src)*scale+offset
                draw.ellipse((u-3,v-3,u+3,v+3),fill=c)
        draw.text((38+450*col,515),title,font=font(23,True),fill='#403b3a')
        draw.text((38+450*col,550),'前缘均方根误差 %.1f 原像素'%view['scalloped_leading_edge_errors']['rms_px'],font=font(16),fill='#625954')
    out.save(output,quality=90,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--board',type=Path)
    args=parser.parse_args();scene=SerialScene(args.mesh)
    doc=json.loads(RECORD.read_bytes());rows=sections(scene)
    report={'mesh':scene.asset,'evidence_sha256':hashlib.sha256(RECORD.read_bytes()).hexdigest(),
            'match':sum(r['matched'] for r in rows),'total':len(rows),'rays':rows}
    if args.board:
        board(scene,args.board,doc);report['board_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest()
    args.report.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    print(report['match'],report['total'],scene.asset)
