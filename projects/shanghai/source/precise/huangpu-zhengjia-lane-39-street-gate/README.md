# 永嘉路39弄郑家衖弄口与院内横屋

街上看得见弄口相对的两根水泥门柱、打开的铁门和靠东的弧形花池。站进弄内，横屋三层窗下的绿底“家政”牌、四台空调和五座短雨篷仍能与2015年街景一一对应。独立页可分别近看弄口、院内窗扇、瓦面和“家政”牌。[不同拍摄位置的实物比对](measurements/courtyard-house-photo-identification.json)

院内主墙有八处开窗。上层左侧叶片翻开，露出内层玻璃格，中层三套百叶合拢。模型保留底层窗格、铁护栏、短篷、表面抹灰、檐下排水管，以及隔壁低翼屋顶在原片可见的那一段。黄漆字和箭头沿原照轮廓重建。[窗洞摄影坐标](measurements/courtyard-window-picks.json) · [屋面与外墙坐标](measurements/courtyard-fabric-observations.json) · [招牌轮廓](measurements/housekeeping-paint.json)

弄口以2015年的铁门开启位置为准。门柱牌面及门扇用后来较清楚的视角复核。花池正面可见两道横缝和25条竖缝，街道一侧的地砖和路缘石仅保留入口前的一小段。[门柱与门扇](measurements/zhengjia-gate-fabric.json) · [弧形花池](measurements/entrance-planter-joints.json)

三处实景机位给出的院内墙面位置相互接近。按8.80米的估计面宽，墙面距入口基线约45.66米，横向偏移5.05米。面宽若在7.6至10.2米之间，相机至屋面的距离约为51至69米。两部分之间的弄深采用这项估算。市区原建筑模型中的院内户号尚无唯一对应，模型在独立页展示。[三站尺度核验](measurements/courtyard-range-check.json) · [院内与街口坐标转换](measurements/courtyard-to-entrance.json) · [原地块与定位](measurements/footprint-review.json)

从上海项目根目录运行以下命令，可以重建两档几何与程序纹理，或查看可编辑Blender工程的标准打包入口。依赖项目中的公共建模工具、NumPy、SciPy、Shapely及Pillow。实图署名与来源列于文末链接。[资料与许可](SOURCES-LICENSE.md)

```sh
python source/precise/huangpu-zhengjia-lane-39-street-gate/source/paint.py
python source/precise/huangpu-zhengjia-lane-39-street-gate/source/build_model.py --output zhengjia-lane-39.glb
python source/precise/huangpu-zhengjia-lane-39-street-gate/source/build_model.py --lod --output zhengjia-lane-39-lod.glb
python source/precise/huangpu-zhengjia-lane-39-street-gate/source/build_model.py --help
```
