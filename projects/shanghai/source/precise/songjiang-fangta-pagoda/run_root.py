#!/usr/bin/env python3
"""Root sequential entry: audited raw geometry, then one Blender session/three views.

Defaults to preparation checks. --execute explicitly authorizes this invocation
of local asset generation; this tool never registers, uploads or modifies MAIN.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--build-only','--raw-only',dest='build_only',action='store_true');p.add_argument('--blender',default='/usr/bin/blender');p.add_argument('--samples',type=int,default=24);a=p.parse_args()
 if a.output.exists():raise ValueError('Choose a fresh run directory; never overwrite a previous model run.')
 raw=a.output/'raw';native=a.output/'native'
 commands=[[sys.executable,str(HERE/'build_model.py'),'--output',str(raw)], [a.blender,'-b','-t','2','--python-exit-code','1','--python',str(HERE/'render_previews.py'),'--','--glb',str(raw/'songjiang-fangta-pagoda-raw.glb'),'--output',str(native),'--samples',str(a.samples),'--threads','2']]
 if a.build_only:commands=commands[:1]
 print(json.dumps({'execute':a.execute,'commands':commands,'output':str(a.output)},indent=2),flush=True)
 if not a.execute:return
 a.output.mkdir(parents=True)
 for index,command in enumerate(commands):
  log=a.output/('geometry-build.log' if index==0 else 'native-render.log')
  with log.open('xb') as stream:subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
 print(json.dumps({'completed':True,'raw':str(raw),'native':str(native) if not a.build_only else None}),flush=True)
if __name__=='__main__':main()
