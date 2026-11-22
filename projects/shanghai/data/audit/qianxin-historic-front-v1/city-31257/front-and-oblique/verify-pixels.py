from PIL import Image
import numpy as np,sys,json
a=np.asarray(Image.open(sys.argv[1]).convert('RGB'));b=np.asarray(Image.open(sys.argv[2]).convert('RGB'))
x,y,w,h=map(int,sys.argv[3:7]);p=a[y:y+h,x:x+w];q=b[y:y+h,x:x+w];m=np.any(p!=q,axis=2)
print(json.dumps(dict(changed=int(m.sum()),pixels=int(m.size),fraction=float(m.mean()),foreground=[int(np.any(im!=im[0,0],axis=2).sum())for im in [p,q]],dimensions=list(a.shape[:2][::-1]),rect=[x,y,w,h])))
