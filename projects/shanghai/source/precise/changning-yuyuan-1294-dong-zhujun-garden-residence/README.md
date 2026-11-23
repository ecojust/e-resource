# 董竹君旧居18号楼的南面券廊与题号山墙

愚园路1294号的这幢住宅原属新华村。长宁区规划和自然资源局记为1925年建造、建筑面积594平方米、占地1120平方米，现为区政府18号楼。2018年街道专稿的院内照片清楚显示山墙下的圆牌“18”，可以将该立面与单栋档案相联。保护铭牌另记1930年，街道报道另列185和740平方米。各数值和原文出处均见 [资料说明](reference-review.json)。

模型展示东开间题号山墙及其左侧庭院立面。底层三道较低的砖券、二层平台、二三层贯通红砖柱和室外楼梯见保护铭牌说明。两套摄影机分别配准2018年的山墙全景和高参88的室外梯近照。外梯的踏步、方柱和镂空栏板可以核对，楼梯在整座花园住宅中的绝对方位和距离仍有误差。东端树荫遮住一部分檐线。屋盖只到模型所见段落。

四种饰面用程序独立生成砖、卵石、灰水泥和红瓦的色图与法线。玻璃、木框和金属分别保留为可编辑材料。普通城市图块14-13717-6695保留原户168及邻宅。门户内的花园住宅和愚园路路边银行的测读出处列于 [地块记录](measurements/named-and-ordinary-owners.json)。

在项目文件树或随附源码包中执行下列命令。相机记录使用作者坐标，X向图右、Y入屋、Z向上，GLB 使用Y向上。

```sh
mkdir -p model
python source/build_model.py --output model/full-source.glb
python source/build_model.py --lod --output model/lod-source.glb
python measurements/check_solid.py model
python measurements/render_views.py model/full-source.glb views
```
