# 业广地产公司大楼滇池路与四川中路转角

依据滇池路120号的具名足印和Fayhoo所摄街角，制作斜切角、两侧各一跨、阁窗、曲线窗头与二层连续阳台。街角向南偏西约21°。高度及构件尺度按斜视街照估算。

房管局现表将120号及四川中路444至464号双号列于2A016，将邻栋仁记洋行列于2A017。源登记保留了旧工作表与现表的差异。

[来源和楼号](reference-review.json) · [足印定位](source/frontage-registration.json) · [制作脚本](source/build_model.py)


街角和两条街墙的位置以现存足印校准。照片显示红砖山花内的券窗、转角平顶阁窗、成对街窗及贯通三侧的铁栏阳台。模型保留每边约5.45米的临街墙。窗洞深度和石饰厚度属于按照片估算的尺寸。

[砖材生成程序](source/brickwork.py)以固定随机种子生成1024×1024的顺砖纹理，两侧山花、窗头曲线及铁栏均由可编辑几何构成。房管局名录与实拍街角的出处、图像许可和日期见[来源登记](reference-review.json)。

在项目的 `projects/shanghai` 目录下，可用下列命令重建。工具参数接受已安装的 Blender、gltfpack 和 Open Image Denoise 命令路径。

```sh
python source/precise/huangpu-dianchi-land-investment-corner/source/build_model.py \
  --out assets/models/candidates/huangpu-dianchi-land-investment-corner \
  --audit data/audit/dianchi-land-investment-corner-v1 \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
```
