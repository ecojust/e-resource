# 光复路195号原交通银行仓库南露台的旗杆

从临河一面看，旗杆立在中央山墙背后，向楼内退约1米。按整楼所用的街面高程，南露台铺地为18.20米，山墙顶约21.84米，杆顶约27.0米。模型展示修缮后的屋顶。杆身与杆脚是两个可分别选择、编辑的实体。[原创模型图板](flagstaff-study.jpg) · [原始GLB](flagstaff-raw.glb) · [网格压缩近档](flagstaff-full.glb) · [网格压缩远档](flagstaff-lod.glb)

图34的临河斜照中，用十组上层窗的顶部与底部及三个檐角定相机，留出杆顶像点，算得27.08米。图39中的屋面边线、墙角和杆轴底点给出另一个相机，留出的杆顶对应26.83米。结合两处相机对控制点与焦距的敏感程度，读为26.5至27.5米。图16可核对与山墙居中的关系。图38原相机将杆顶预测在实见点右方3.2像素、下方21.1像素，此处读高的不确定性较大。[原图出处与原尺寸坐标](photo-observations.json) · [相机复算](camera-checks.json)

图38、39中仅能辨出杆脚浅色小块的部分顶面和明暗边界。图中绘作约0.40 × 0.32米、厚0.20米，宽深、厚度、金属杆的渐缩直径与表面颜色均为外观近似。杆身在模型中的下段直径约9厘米、上段约5厘米。每个网格档次都用整楼露台的五个真实铺地点、杆顶、二十个侧向交点和三个杆座顶面点复核，共87次。另查两个实体的边缘闭合和有向体积。[三档检查记录](mesh-checks.json) · [可编辑构件源码](roof_flagstaff.py)

现场图片和屋面平面图出自华建集团历史建筑保护设计院发表的光复路195号修缮项目介绍。图板采用本增补模型和首版建筑网格绘制。[设计院项目图文](https://www.sohu.com/a/971431850_121124642) · [整楼首版](https://github.com/ecojust/e-resource/tree/31d877578e31d1e3392e2fd8a358324e5af93ecb/projects/shanghai/source/precise/jingan-bank-of-communications-warehouse-guangfu-riverfront)

## 复算

在仓库检出首版或含有整楼源码的后续版本后，将项目目录、输出位置、gltfpack可执行文件以及整楼原始、解压近档、解压远档GLB依次传给下面的程序。Python环境需有NumPy、SciPy和Pillow，另需Node.js及Noto Sans CJK字体。整楼三件的校验值见检查记录。

```sh
python package_flagstaff.py PROJECT OUTPUT GLTFPACK HOUSE_RAW HOUSE_NEAR_DECODED HOUSE_FAR_DECODED
```
