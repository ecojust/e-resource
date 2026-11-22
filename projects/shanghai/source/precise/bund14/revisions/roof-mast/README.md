# 交通银行旧址塔顶旗杆

上海市房屋管理局第三批优秀历史建筑名录将中山东一路14号登记为3A002，原名交通银行，现名上海市总工会大楼。本次细化沿用外滩14号的地图入口。近景保留原建筑的48个正面窗洞和照片玻璃，在中央石脊的后方增加独立旗杆、圆形杆头及收垂的红色旗幅。[市房管局第三批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [模型清单](manifest.json)

Ferox Seneca于2012年8月31日从侧面拍下展开的旗幅，能分辨旗杆与前端两枚条纹圆筒的位置。Livelikerw于2014年1月14日从另一侧取景，旗杆和收拢的旗幅出现在中央石脊侧后。2025年5月1日Suicasmo的正面原片仍可辨圆形杆顶，石脊右缘露出一条狭窄的红色旗幅。这三张照片共同确定旗杆的位置关系，模型的旗幅采用2025年的形状。[2012年](https://commons.wikimedia.org/wiki/File:China_Bank_of_Communications_Building_Shanghai.jpg) · [2014年](https://commons.wikimedia.org/wiki/File:China_Bank_of_Communications_Building,_Shanghai.JPG) · [2025年](https://commons.wikimedia.org/wiki/File:Bank_of_Communications_Building,_Shanghai_20250501.jpg)

原模型采用33.4米作为最高石砌构件的估计高度。此次用杆顶和可见红边在3456×5184像素原片中的位置，结合旧模型相机的透视矩阵，估算杆顶约35.68米。沿主轴退入1.75米是一个估计值，可解释的范围约1.3至2.4米。以2012年斜照中前景圆筒为尺度，另核了露出杆身的比例。杆径、旗幅折叠及背侧布面厚度也按照片比例估计。旗绳、隐蔽杆座和没有近照的后屋面仍待查。[图像与几何参数](geometry-input.json) · [来源、作者与许可](reference-review.json)

## 生成和复核

从项目的这一源码目录执行下列命令，使用Python、NumPy、Node.js和Blender。脚本引用同一项目中外滩17号修订的网格工具及网页使用的meshoptimizer解码器。下载脚本逐件核对已提交旧版的Git对象、SHA-256和字节数。

```sh
python fetch_baseline.py /tmp/bund14-prior
mkdir -p /tmp/bund14-revised /tmp/bund14-checks
python build_mast.py /tmp/bund14-prior /tmp/bund14-revised
blender -b -t 1 -P native_mast.py -- /tmp/bund14-prior/native.blend /tmp/bund14-revised/native.blend /tmp/bund14-checks/native.json
node check_buffers.mjs /tmp/bund14-prior /tmp/bund14-revised /tmp/bund14-checks/decoded.json
python check_roof.py /tmp/bund14-revised /tmp/bund14-checks/rays.json
blender -b -t 1 -P render_mast.py -- /tmp/bund14-revised/native.blend /tmp/bund14-checks
```

原始及网页近景共有78,204个三角面，远景68,948面。三个新增部件在Blender中各自可编辑。新增几何采用项目MIT许可。原地块采用OpenStreetMap的ODbL-1.0许可，原始照片玻璃采样保留Suicasmo的CC0原图。[旧版四件](baseline.json) · [复核记录](../../../../../data/audit/bund14-roof-mast-v1/README.md)
