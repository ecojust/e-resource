from hashlib import sha256
from pathlib import Path
import argparse,json
import numpy as np
from scipy.ndimage import map_coordinates,gaussian_filter
from PIL import Image,ImageOps

# Four points of the south parapet are assigned to a measurement rectangle. The
# lines at each end provide extra space around the actual front of the balustrade.
REFERENCE=[[3570.,790.],[4952.,302.],[4964.,558.],[3576.,970.]]
CENTRES=[44,66,92,119,146,174,200,226,252,279,305,330,355,381,406,433,458,481,508,534,558,582,605,629,653,676,699,721,744,768,790,811,832,855,877,898,920,942,964]

def homography(source,destination):
    rows=[]
    for (x,y),(u,v) in zip(source,destination):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y,-u],[0,0,0,x,y,1,-v*x,-v*y,-v]])
    return np.linalg.svd(rows)[2][-1].reshape(3,3)

def project(h,x,y):
    q=h@np.array([x,y,1.])
    return q[:2]/q[2]

def run(source,output):
    original=source.read_bytes()
    assert sha256(original).hexdigest()=='6d2e2db453c82e94f11b0bc594e784bcf47689595c1de425afc5f71e1aac94ff'
    picture=np.asarray(ImageOps.exif_transpose(Image.open(source)).convert('L'),float)
    # Coordinates of the four visual registration corners after rectification.
    template=[[28.3,27.1],[970.7,27.1],[970.7,162.5],[28.3,162.5]]
    h=homography(template,REFERENCE)
    u,v=np.meshgrid(np.arange(1000),np.arange(187));q=h@np.stack([u.ravel(),v.ravel(),np.ones(u.size)])
    values=map_coordinates(picture,[q[1]/q[2],q[0]/q[2]],order=1).reshape(v.shape)
    grad=np.gradient(gaussian_filter(values,[.9,1.15]),axis=1)
    heights=np.arange(50.,150.,2.)
    def fit(centre,direction,width):
        best=None
        for slope in np.arange(-.024,.079,.008):
            for x in np.arange(centre+direction*width,centre+direction*width+6.5,.25):
                xx=x+slope*(heights-100)
                g=map_coordinates(grad,[heights,xx],order=1)
                # A painted upright usually has a bright face against its darker
                # reveal. Retain absolute contrast for the back-lit sections.
                merit=float(np.median(.7*np.abs(g)-.3*direction*g))
                if best is None or merit>best[0]:best=(merit,x,slope)
        return best
    rows=[]
    for i,centre in enumerate(CENTRES):
        if i==0: width=4.9
        else:width=6.8-.045*i
        l=fit(centre,-1,width+3);r=fit(centre,1,width-3.3)
        top=lambda x:41.3+.0102*(x-40.)
        bottom=lambda x:156.8+.0077*(x-40.)
        def corner(f,v):
            _,x,m=f;return [round(float(t),3) for t in project(h,x+m*(v-100.),v)]
        rows.append(dict(index=i+1,upper_left=corner(l,top(centre)),upper_right=corner(r,top(centre)),lower_right=corner(r,bottom(centre)),lower_left=corner(l,bottom(centre)),rectified_mid_x=[round(l[1],3),round(r[1],3)],edge_contrast=[round(l[0],2),round(r[0],2)]))
    j=dict(photo_source='Antigng 2015-09-09. EXIF orientation 3, rotated before measurement.',photo_sha256=sha256(original).hexdigest(),upright_dimensions_px=[5312,2988],registration_corners_px=REFERENCE,rectified_corners=template,method='The 39 light-painted upright positions were read from the rectified photograph. Signed and absolute horizontal luminance gradients across 50 heights locate each side of the upright. The pale end cap and drainpipe to its left are separate features. Cables, leaves and glare obscure some edge segments. The fitting carries visible edge directions to each bedding face.',uprights=rows)
    output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('original',type=Path);parser.add_argument('output',type=Path);opt=parser.parse_args();run(opt.original,opt.output)
