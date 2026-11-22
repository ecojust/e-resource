"""Original repeating fired-brick finish, generated in metric space without photographic pixels."""
from pathlib import Path
BRICK='1914 block | kiln-fired red brick'
REPEAT=(1.92,1.056)
TEXTURE=Path(__file__).with_name('fired-brick.jpg')

def make(destination):
    import numpy as np
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    rng=np.random.default_rng(19145030)
    h,w=528,960
    y,x=np.indices((h,w))
    # Offset courses with occasional paired headers. The larger brick faces in the 2020
    # detail give a finish scale estimate. Individual photographed units are not reused.
    row=y//33
    xx=(x+(row%2)*60)%w
    unit=xx//120
    splits=rng.random((16,8))<.27
    half=(xx%120)>=60
    joint=np.minimum.reduce([xx%120,(120-xx%120)%120, (y%33)*1.,(33-y%33)%33])
    joint=np.where(splits[row,unit],np.minimum(joint,abs(xx%120-60)),joint)
    bed=gaussian_filter(rng.standard_normal((h,w)),.85,mode='wrap')
    joint=joint+.75*bed/bed.std()
    blend=np.clip((joint-.75)/2.0,0.,1.)
    field=rng.normal(0,7,(16,8,2))
    deviation=field[row,unit,np.where(splits[row,unit],half,False).astype(int)]
    grit=rng.normal(0,3.2,(h,w))
    broad=gaussian_filter(rng.standard_normal((h,w)),7.,mode='wrap')
    mottling=3.0*broad/broad.std()
    brick=np.array([169,92,67])[None,None,:]+(grit+deviation+mottling)[:,:,None]*[1,.88,.72]
    mortar=np.array([151,121,100])[None,None,:]+(grit*.72+bed)[:,:,None]
    rgb=mortar*(1-blend[:,:,None])+brick*blend[:,:,None]
    Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(destination,quality=91,subsampling=0)

if __name__=='__main__':
    make(TEXTURE)
