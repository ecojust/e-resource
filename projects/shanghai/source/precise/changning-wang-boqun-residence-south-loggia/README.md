# 王伯群住宅南花园双层弧廊

上海市长宁区愚园路1136弄31号，现长宁区少年宫。市房管局第一批优秀历史建筑名录编号1M007。区房管局记载主楼于1934年落成。模型依据南侧花园的高位正照、草坪正照、近地斜照及旧照制作，表现现状。

模型以花园侧的两层弧廊为范围。下层三道敞拱连着入口平台及两侧下行梯段。上层五扇玻璃窗的中央一扇较宽，窗台下为四叶透花石栏板，顶部是可步入的弧形露台。侧翼、主屋屋顶、室内和花园均位于本次范围外。与主屋相接的楼板在后缘截断。实际可见的楼梯分向与窗、拱及栏杆的层次用实体几何表达。

两张摄影站各用13个可辨点作透视拟合，其中2点独立检验。模型坐标为米，曲率、绝对尺度、截断面位置、檐部深度、栏杆间距及梯级数属于估算。站位是影像拟合结果。铭牌及历史文字不作几何推定。模型色彩和程序生成的材质均为原创。

## 文件与重建

三档 GLB 可直接在标准 glTF 2.0 查看器中打开。可编辑工程保留石柱、拱券、窗棂、花饰、梯段和栏杆的分组、程序材质与九个相机。可在此目录执行以下命令重建并独立检查。相机重新拟合使用 NumPy 与 SciPy，射线检查使用 NumPy。此次原生检查使用 Blender 4.3.2。

```sh
python source/build.py ./output
python measurements/register_views.py
blender -b -t 1 --python-exit-code 1 -P source/editable.py -- build ./output/raw.glb ./output/editable.blend source/cameras.json
blender -b -t 1 --python-exit-code 1 -P source/editable.py -- check ./output/editable.blend ./output/editable-check.json
OPENBLAS_NUM_THREADS=1 python measurements/check_assets.py ./output ./output/three-level-ray-tests.json
```

[名录、照片与许可](SOURCES-LICENSE.md) · [摄影站标点及残差](measurements/photographic-registration.json) · [在线展示](../../../wang-boqun-south-garden-loggia.html)
