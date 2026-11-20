# 字林西报大楼临江两翼首层门扇

上海市第二批优秀历史建筑2A007登记为中山东一路17号字林西报大楼。2014年的斜视照片中，两翼各有深色门洞、横向金线和石门楣上的“17”。2025年5月1日的照片可看清黑色双扇、门缝两旁的竖金条和圆饰、门叶花环状装饰与下垂细杆、卷线门楣和镀金横带。南门的右侧给石窗套遮住一部分，门叶细节以北门较完整的原照为主要依据。两张照片均无法确定现门的安装年代。[市府名录、两张原照与范围](reference-review.json) · [2025年门扇局部](../../../../../data/audit/daily-news-wing-doors-v1/wing-doors-source.jpg) · [2014年两翼局部](../../../../../data/audit/daily-news-wing-doors-v1/2014-both-door-crop.jpg)

在V4.4原网格中，各翼门48条射线均落在同一深度的蓝灰色玻璃上，通用浅色窗梃还从玻璃前方经过。新双扇在原有券石门套内向前落座，完整盖住这些旧窗梃。下垂装饰、卷线和门牌数字均为实体几何，金色与暗色金属参数按可见外观估计。原石材、中央柱廊、上层24扇取样窗及顶层两座塔楼均保留。主图继续使用同一锚点及地面碰撞。[原始96条射线](../../../../../data/audit/daily-news-wing-doors-v1/original-96-rays.json) · [新旧整楼网格核验](../../../../../data/audit/daily-news-wing-doors-v1/geometry-comparison.json) · [四件资产路径与散列](manifest.json)

## 重新构建

下列命令在本目录运行。几何步骤使用Python 3、NumPy，原生文件使用Blender 4.3.2。基础输入取自固定提交，逐个校验Git对象、SHA-256和文件长度。

```sh
python fetch_baseline.py /tmp/bund17-base
python build_wing_doors.py /tmp/bund17-base /tmp/bund17-new
blender -b -t 1 --python-exit-code 5 -P native_doors.py -- /tmp/bund17-base/native.blend /tmp/bund17-new/native.blend /tmp/bund17-new/native-reopen.json
```

三档GLB均保留原始二进制块与原图元，新增门扇和门楣各有独立命名网格。原始及近景完整保留原JPEG，简化远景延用V4.4无图材质。V4.4的原有逐窗源和屋顶取证见旧版本工程。[基础资产交接记录](baseline.json) · [V4.4工程](https://github.com/ecojust/e-resource/tree/2de028ea0d545643b95fd5ee1d12db26bb5d7b60/projects/shanghai/source/bund/bund_classics/photo-v4.4)

原创代码与构件几何采用MIT，地图足迹由OpenStreetMap贡献者按ODbL 1.0提供。原模型取样照片由Suicasmo按CC0 1.0发布。[照片署名与许可](../../../../../data/audit/daily-news-wing-doors-v1/image-credits.md)
