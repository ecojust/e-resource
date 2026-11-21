"""Original, periodic, fine-grained granite texture and the documented surface fracture."""
import json
from pathlib import Path

import numpy as np

STONE = 'Grey dressed granite'
FISSURE = 'Weathered granite fissure'
PERIOD = .32
SOURCE = Path(__file__).resolve().parent

def create():
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    rng = np.random.default_rng(6022021)
    n = 384
    def texture_field(sigma):
        field = gaussian_filter(rng.normal(0.,1.,(n,n)), sigma, mode='wrap')
        return (field-field.mean())/field.std()
    # Feldspar/cloudy quartz grains and fewer dark mineral grains, with a weak
    # broad weathering field. All convolution samples wrap periodically.
    ground = 3.9 * texture_field(4.1) + 2.4 * texture_field(13) + 1.9 * texture_field(.35)
    mica = np.clip((texture_field(.82)-.89)/.92,0,1)
    quartz = np.clip((texture_field(1.23)-.68)/1.23,0,1)
    base = np.array([159.,151.,137.])
    image = base + ground[:,:,None] - mica[:,:,None]*[36,33,30] + quartz[:,:,None]*[19,19,21]
    Image.fromarray(np.clip(image,0,255).astype('uint8')).save(SOURCE/'dressed-grey-granite.png',optimize=True)

def build_fissure(b, radius, height):
    survey=json.loads((SOURCE.parent/'measurements/granite-fissure.json').read_bytes())
    scale=radius/survey['inner_step_radius_m']
    points=np.asarray(survey['metric_points'])*scale
    half_width=np.asarray(survey['estimated_half_width_m'])*scale
    vertices=[];faces=[]
    for i,(point,width) in enumerate(zip(points,half_width)):
        tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
        for location in (point-width*normal,point+width*normal):
            vertices.append((*location,height+.00072))
        if i:
            k=2*i
            faces.append((k-2,k,k+1,k-1))
    b.add(vertices,faces,FISSURE,'Upper step / photographed mineral fracture')

if __name__=='__main__':
    create()
