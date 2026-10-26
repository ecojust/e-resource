"""Small reusable mathematical opening profile; not a measured photo tracing."""
def cubic(a,b,c,d,t):
 return tuple((1-t)**3*a[i]+3*(1-t)**2*t*b[i]+3*(1-t)*t*t*c[i]+t**3*d[i] for i in range(2))
def cusped_opening_profile(width,height,segments_per_curve=8):
 if min(width,height)<=0 or segments_per_curve<4:raise ValueError('Invalid opening control')
 curves=[((-.5,.66),(-.5,.76),(-.37,.83),(-.28,.83)),
         ((-.28,.83),(-.25,.88),(-.23,.94),(-.14,.94)),
         ((-.14,.94),(-.08,1),(+.08,1),(+.14,.94)),
         ((+.14,.94),(+.23,.94),(+.25,.88),(+.28,.83)),
         ((+.28,.83),(+.37,.83),(+.5,.76),(+.5,.66))]
 points=[(-width/2,0),(width/2,0),(width/2,.66*height)];top=[]
 for controls in curves:
  for i in range(segments_per_curve):
   x,z=cubic(*controls,i/segments_per_curve);top.append((x*width,z*height))
 top.append((width/2,.66*height));points+=list(reversed(top[:-1]));return points
