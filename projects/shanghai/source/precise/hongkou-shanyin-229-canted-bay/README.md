# 山阴路229弄1号花砖凸窗与曲线铁栏

山阴路229弄1号住宅楼上，一面斜窗与中央窗沿青砖墙角相接。两面均可看见红砖券、红漆窗框、浅色挑窗台和曲边裙板。2015年照片中斜面右侧的一扇向外开启，栏杆在墙角处随凸窗折转。[Fayhoo，2015年4月12日，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Shanyinlu_229_Long_Zhuzhai.jpg)

老房子爱好者的独立拍摄以“山阴路229弄1号”标注同一面。窗台、裙板和上亮作第二视角的对应检查，逐点投影残差为0.84至7.55像素，原图宽640像素。取景右缘的树叶遮住其余转面。市名录5F006另列209弄，该处住宅在另一页展示。[第二组实照](https://www.toutiao.com/article/6984724111138243084/) · [上海市第五批优秀历史建筑](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [山阴路209弄3号](../../../shanyin-209-brick-arched-front.html)

## 尺度

两道横带之间取一个单位高度。斜面宽约0.467单位，中面宽约0.469单位。以照片中心为主点、方形像素、砖墙竖棱垂直于横砖皮为条件，估算转角约46°。转角对檐边取点较敏感，1.35像素的标点扰动下，中央80%的结果约42°至55°。两幅照片均无独立建筑米标。模型将基准高度设为3.2展示单位。铁栏的背面、窗铰、开启角与券石进深按可见轮廓近似。[原图标点](measurements/229-projected-bay-proportions.json) · [双视角与灵敏度计算](measurements/229-two-view-check.json)

## 复建

在项目根目录执行以下命令。需 Python 3、NumPy、Shapely、SciPy、Pillow、Node.js、C++ 编译器及 gltfpack。打包器会用仓库内的 meshopt 解码程序逐角色复查有向三角面、顶点和材质。

```sh
cd projects/shanghai
python source/precise/hongkou-shanyin-229-canted-bay/source/build_model.py \
  --out assets/models/candidates/hongkou-shanyin-229-canted-bay \
  --decoded build/shanyin-229/decoded --gltfpack gltfpack
python data/audit/shanyin-229-canted-bay-v1/inspect-model.py \
  assets/models/candidates/hongkou-shanyin-229-canted-bay/hongkou-shanyin-229-canted-bay-raw.glb \
  build/shanyin-229/decoded/decoded-full.glb build/shanyin-229/decoded/decoded-lod.glb \
  build/shanyin-229/inspection
```

从仓库根目录启动静态HTTP服务即可打开独立展页。首次交付包含原始、近景和远景GLB，分别为23,936、23,936和9,824个三角面；72次表面射线检查覆盖砖皮、窗框、玻璃、托板、铁栏与上方开口。6个机位分别复核近、远网格。[独立展页](../../../shanyin-229-canted-bay.html) · [实际射线与渲染结果](../../../data/audit/shanyin-229-canted-bay-v1/views/three-role-inspection.json)

## 署名

展示网格及据其绘制的视图采用 CC BY-SA 3.0。模型参照Fayhoo的同许可照片，用自行构造的曲线、砖皮和面材重建；GLB无嵌入照片。老房子爱好者的第二张实照仅以链接引用。[Fayhoo的原作与许可](https://commons.wikimedia.org/wiki/File:Shanyinlu_229_Long_Zhuzhai.jpg) · [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
