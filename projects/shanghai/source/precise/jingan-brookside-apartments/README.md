# 枕流公寓

市房管局第二批2B020登记为枕流公寓，华山路731号。《上海名建筑志》记地上七层、地下一层、总高28.9米，由哈沙德洋行设计、馥记营造厂施工。志书记述的主入口朝北，南花园另有门阶。[名录、志书及各期照片](reference-review.json)

2019年12月的无人机照片提供了楼体两翼和屋顶转折的方向。2023年11月的花园正照可见中央山花、分高低的透空券列、菱形透孔、成组的凸窗和南门台阶。两座独立花园门架位于楼前，与主楼之间有绿地和步道。华山路一面的窗墙另参考2020和2021年的街景，顶上设备、树后的侧窗和室内布置缺少同等精度的资料。[2019年拍摄参数和底图2669](footprint-review.json) · [三期航空底图](aerial-editions.json)

要修改外观，可直接打开资产目录中的 Blender 工程，也可编辑参数化几何并重新生成。在上海项目目录执行以下命令会在指定输出目录创建原始模型、两个网页模型和可编辑工程；核验目录接收母模复开结果和预览图。该脚本使用 Blender、gltfpack 和 Open Image Denoise。[几何脚本](source/brookside_geometry.py) · [单体页](../../../brookside-apartments.html)

```sh
python source/precise/jingan-brookside-apartments/source/build_model.py --out /tmp/brookside-model --audit /tmp/brookside-audit
```
