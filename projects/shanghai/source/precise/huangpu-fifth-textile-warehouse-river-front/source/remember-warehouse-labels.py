import bpy,json,os
names=json.loads(os.environ['WAREHOUSE_FULL_GROUP_LABELS'])
@bpy.app.handlers.persistent
def retain_warehouse_group_names(scene,*args):
    for short,full in names.items():
        ob=bpy.data.objects[short]
        assert ob.type=='MESH'
        ob['full_source_group']=full
bpy.app.handlers.save_pre.append(retain_warehouse_group_names)
