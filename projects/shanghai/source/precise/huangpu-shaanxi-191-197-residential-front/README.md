# 陕西南路195号住宅与南端叠廊

2018年6月10日，WQL从街对面拍摄了这幢住宅。正面可辨两层格窗、穿插在砂浆墙里的红砖齿口、弧瓦、挑檐和三盏院墙灯。南端的底层圆券和楼上矩形廊口均连通侧廊。上海市第五批优秀历史建筑名录以黄浦区5A052合列陕西南路191至197号；这张署名照片的题名具体到195号。[原作者照片](https://commons.wikimedia.org/wiki/File:%E9%99%95%E8%A5%BF%E5%8D%97%E8%B7%AF195%E5%8F%B7.jpg) · [地址和原城轮廓核对](measurements/footprint-review.json)

本模型包括可编辑的街面主墙、四樘窗、檐下木构、前瓦坡、南端上下两层叠廊，以及照片中位于窗前的院界墙。三个方柱上的灯具、栏杆上的叉尖和弧形铁饰均按2018年照片放样。院墙脚部分受人行护栏和树木遮挡，取院墙向街退距约1.55米，估计范围约0.7至2.5米。前瓦坡的截取深度为2.83米，后屋面形状未获证实。模型在独立查看页展示。[院墙及铁栏观测](measurements/court-wall-2018.json) · [街面与瓦坡测量](measurements/house-fabric-and-roof.json)

上层两樘窗各有三组粗窗格，每组再分成两个小格。2018年整面照和不同年份街景共同约束窗宽、窗台高度与相对位置。南廊圆券边与侧券、楼上栏杆及吊灯以另组控制点检验。视线接近吊灯和券肩轮廓时，单个像素的材质判断会受原片清晰度影响。[格窗尺度及相机](measurements/west-upper-window-calibration.json) · [南廊跨视角测量](measurements/south-loggia-cross-registration.json)

## 重建与复核

在本项目根运行下列命令，可从Python建模源导出近景、远景以及可编辑Blender文件。几何坐标以米为单位，X沿街向南，Y向院内，Z向上。纹理由固定随机种子生成，原照片仅用于测量。[几何源](source/build_model.py) · [材质生成](source/paint.py) · [来源与授权](SOURCES-LICENSE.md)

```sh
src=source/precise/huangpu-shaanxi-191-197-residential-front/source
python "$src/paint.py"
python "$src/build_model.py" --output shaanxi-street.glb
python "$src/build_model.py" --output shaanxi-street-low.glb --lod
python "$src/build_model.py" --out shaanxi-assets --audit shaanxi-checks --blender blender --gltfpack gltfpack --oidn oidnDenoise
```

独立审计目录内有三档真实网格的街面射线、贴图坐标和七机位渲染。窗格、屋瓦及围墙各有具体材质和实测位置，可逐项复算。[街面核验](../../../data/audit/shaanxi-191-197-residential-front-v1/verify-export.py) · [上部格窗核验](measurements/check_west_windows.py)
