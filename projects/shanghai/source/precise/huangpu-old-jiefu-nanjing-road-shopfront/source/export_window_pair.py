"""Export the standalone measured component or import nanjing_steel_windows into the full model."""
from argparse import ArgumentParser
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from nanjing_steel_windows import add_window_pair,PALETTE

if __name__=='__main__':
    p=ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--lod',action='store_true');arg=p.parse_args()
    b=Builder(PALETTE);add_window_pair(b,arg.lod)
    b.save(arg.output,{'copyright':'Measured component and mesh CC BY 4.0. Source views by Chainwit., CC BY 4.0. No photo texture embedded.','name':'老介福绸缎局北立面一组双扇钢窗与交叉菱格窗裙','units':'metres','photo_author':'Chainwit.','geometry_license':'CC BY 4.0','source':'Two 2024-04-23 views of 257 Nanjing East Road by Chainwit., Wikimedia Commons. Mesh modeled from photographs. No photo texture embedded.'})
    print(arg.output,len(b.parts),sum(len(q['triangles']) for q in b.parts))
