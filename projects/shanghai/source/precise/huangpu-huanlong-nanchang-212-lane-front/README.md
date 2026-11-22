# 南昌路212弄环龙别业门楼与244弄入口

212弄的两根球顶门柱托住两道铁拱。2015年9月，摄影师Antigng在入口斜侧拍到红灯、铁花、木格窗、伸缩晾衣架和露台的细栏杆。市房管局的第五批名录将“环龙别业、环龙里”与南昌路212、244弄列在同一条目。212弄另有环龙别业修缮资料支持。244弄入口按其本身的绿牌、侧墙、窄窗和可见铁门识别。[2015年212弄原照](https://commons.wikimedia.org/wiki/File:%E5%8D%97%E6%98%8C%E8%B7%AF212%E5%BC%84.jpg) · [第五批优秀历史建筑名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html)

在模型页选择“看244弄绿牌与窄窗”可直接移至另一个入口。用冬季街景参照点换算，244弄绿牌下方与212弄上层中窗墩相距约85.55米；另一组站点得到约84.99米，两次估计相差约2米的位置。两地各按其路面定零，之间的绝对高程差未经水准测量。[两个入口的放置依据](measurements/212-and-244-placement.json) · [独立站点交叉复核](measurements/lane-244/placement-from-212.json)

两处实际通行空间分别建模。212弄上方有两个窗洞、六张可见外开窗扇，每扇为两列四行玻璃。窗下晾衣架的三根金属杆由七处独立亮线截面确认；露台栏杆的39个立柱逐根测边。244弄局部包括四片玻璃、窗台及窗头、墙上六道分缝、绿色门牌，以及可见门栏。照片对后院、邻户和两处之间的建筑覆盖有限，实物范围止于有证的外墙和出入口。[露台栏杆测量](measurements/terrace-rail-edges.json) · [晾杆图像剖面](measurements/retractable-airer.json) · [244弄墙与门牌](measurements/lane-244/photogrammetry.json)

从上海项目根目录运行下列命令可重建两个精度等级和原创抹灰纹理。依赖Python、NumPy、SciPy、Shapely、Pillow及项目公共建模工具。标准Blender打包入口保留具名部件与七个相机。[素材与许可](SOURCES-LICENSE.md)

```sh
python source/precise/huangpu-huanlong-nanchang-212-lane-front/source/paint.py
python source/precise/huangpu-huanlong-nanchang-212-lane-front/source/build_model.py --output nanchang-212-244.glb
python source/precise/huangpu-huanlong-nanchang-212-lane-front/source/build_model.py --lod --output nanchang-212-244-lod.glb
python source/precise/huangpu-huanlong-nanchang-212-lane-front/source/build_model.py --help
```
