# 武进路225弄住宅卷草山墙

照片中的山墙上有两组红框窗。窗间封砌面的风化砖色偏粉褐，下面是一块叶脉从中部向两边展开的卷草饰板。模型按同一栋的檐线、窗、饰板和下部浅色砖墙建造。它位于第五批上海市优秀历史建筑5F010的武进路225弄3–11号范围内，照片中的具体门牌待考。同条目的9号与11号两处入口另有独立门牌照与展示页。[两处住宅入口](../../../wujin-225-paired-residential-entrances.html)

## 照片与比例

Fayhoo 于2016年2月9日从院内拍摄的照片保有墙身、两侧窗和上檐。几何随原摄影作品按 CC BY-SA 3.0 共享。饰板对照图裁取并标注了这幅照片，近、远网格内嵌三张程序砖纹。图像作者及授权如下。[原片和摄影署名](https://commons.wikimedia.org/wiki/File:Wujinlu_225_Long_9,_11_Hao_Zhuzhai.jpg) · [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

高参88于2009年9月所摄的另一角度和2016年照片共有49个可见特征，第二视点拟合残差中位1.24像素，第90百分位3.66像素。2015年另一张近照单独用于核对浮雕图案。饰板名义宽1.82、高1.10米来自砖皮模数换算，檐口进深依斜照估算。实际取点、两组投影矩阵、屋檐偏差和图文来源见测量资料。[双视点记录](measurements/gable-registered-cameras.json) · [屋顶控制点](measurements/gable-metric-extent.json) · [照片目录及授权](measurements/acanthus-photographs.json)

## 重建

从本目录运行，需 Python 3、NumPy、Pillow、Shapely、仓库附带的模型工具、Meshoptimizer 的 gltfpack 以及 Node.js。生成几何、网页压缩件、独立解码件和清单的命令如下。

```sh
python source/build_model.py --out build/models --decoded build/decoded --gltfpack gltfpack
python measurements/render_gable.py build/models/hongkou-wujin-225-acanthus-gable-raw.glb build/decoded/decoded-full.glb build/decoded/decoded-lod.glb build/views
python measurements/check_topology.py build/topology.json
```

按米制局部坐标组织模型，饰板中央为原点，沿墙为X，向里为Y，向上为Z。屋面下缘、封砌面上方与饰板两端的实测误差分别列在投影表中。可编辑工程使用同一组具名构件并逐角对应贴图坐标。每幅渲染按指定相机直接读取所列GLB的嵌入纹理，使用统一的展示灯光。程序、原创砖纹及其生成器按仓库 MIT 许可发布。
