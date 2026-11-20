# 原上海市图书馆东门的门扇与石刻

长海路366号的杨浦区图书馆沿用1930年代原上海市图书馆。历史主入口朝东，门上方有石栏阳台及纵向高窗，两侧各有一扇八角窗。这些固定部位可在2018年整立面照片和2019年门面近照之间互认。近照显示成对格扇的上部有成列三角形花孔，下部各有云纹框饰，中间装有成对门把。花饰石券包住半圆门楣，两侧低墙有横向雕带。另一位作者刊出的黑白老照片可以辨认相同的位置和轮廓。[2018年整立面](https://www.meipian.cn/1r17jdu4) · [2019年外门近照](https://www.meipian.cn/2kgajyh3) · [另刊的历史照片](https://www.meipian.cn/1xn623c5)

本次修订在原整馆工程中替换了东门组件。实心下扇、深置玻璃、镂空的上扇、把手、拱圈卷草和横带均含实际三维几何。石花和卷草根据可见轮廓概括，浮雕深度、玻璃反射和金属色均按照片估计。馆内另有铸花铁门，此次拍摄位置位于室外；照片、作者、文件尺寸及校验值均收在参考目录。[照片目录](reference-review.json)

主楼、2018年扩建部分、两个露天内院继续使用V13的原位置和尺度。原地图入口、街区地块1196、相机起点分别保有各自的定位。新文件按版本存放，可回看原始整馆交付。现版本完整模型390,432个三角面，简化模型139,556个三角面。[进入原馆漫游](../../../../../index.html#landmark=yangpu-library&mode=walk) · [四件模型清单](manifest.json) · [V13原始模型说明](../../CURRENT_STATE.md) · [前后几何及图像核验](../../../../../data/audit/yangpu-library-east-entry-relief-v1/README.md)

## 本地重建

从 `projects/shanghai/` 运行。需要 Python 3、NumPy、Shapely、gltfpack、Node 和 Blender 4。源坐标采用东、北、上，单位为米；glTF坐标为东、上、南。新版入口直接调用原工程，继承其定标和可查证的外部几何。

```sh
revision=source/precise/yangpu-library/revisions/east-entry-relief
mkdir -p /tmp/library-east
python -B "$revision/authoring/build_model.py" --out /tmp/library-east/full-v6
python -B "$revision/authoring/build_model.py" --lod --out /tmp/library-east/lod-v6
python -B source/precise/yangpu-library/authoring/package_assets.py \
  --root /tmp/library-east --gltfpack "$(command -v gltfpack)"
blender -b --threads 2 --python-exit-code 1 --python "$revision/authoring/render_revision.py" -- \
  --glb /tmp/library-east/package-v6/yangpu-library-raw.glb \
  --native /tmp/library-east/yangpu-library.blend \
  --image /tmp/library-east/door.png --report /tmp/library-east/native.json --samples 12
```

原工程及新增的原创几何与代码沿用MIT许可。参考图像保留各作者权利，仅提供出处与校验值。建筑轮廓采用原工程的 OpenStreetMap 与 Overture Maps 数据及既有授权条件。[原工程许可及署名](../../authoring/ATTRIBUTION.md)
