"""Write photo-free LOD input from corrected Bund12 geometry; never save input."""
import bpy,sys,argparse
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(args.input))
models=[bpy.data.objects[n] for n in('HSBC Bund 12','Bund12 six observed main casement frames','Bund12 thirty independently mapped recessed glass panes')]
m=bpy.data.materials.new('Bund12_Distant_Geometric_Glazing');m.use_nodes=True;m.diffuse_color=(.075,.14,.16,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.075,.14,.16,1);bs.inputs['Roughness'].default_value=.3;bs.inputs['Metallic'].default_value=.1
count=0
for ob in models:
 for i,old in enumerate(ob.data.materials):
  if old.name.startswith('PhotoFacade_') and old.use_nodes and any(n.type=='TEX_IMAGE' and n.image for n in old.node_tree.nodes):ob.data.materials[i]=m;count+=1
assert count==1
bpy.ops.object.select_all(action='DESELECT')
for ob in models:ob.select_set(True)
bpy.context.view_layer.objects.active=models[0];bpy.ops.export_scene.gltf(filepath=str(args.output),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True)
print('PHOTO_FREE_LOD_SOURCE_READY',args.output)
