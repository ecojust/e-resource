# 原亚洲文会博物院虎丘路立面

虎丘路20号曾是英国皇家亚洲文会北中国支会的会址。1874年建成的第一座馆舍为两层。现存大楼由George L. Wilson设计，馆方记为1932年竣工。2007年戴维·奇普菲尔德建筑师事务所受邀改造，上海外滩美术馆于2010年成立。市房管局第三批名录3A009所列使用单位是青岛工行和上海图书馆书库。独立模型展示虎丘路上的历史西门，今日美术馆主入口位于虎丘路以东的博物院广场。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [馆史](https://www.rockbundartmuseum.org/about-us) · [参观入口](https://www.rockbundartmuseum.org/visit)

馆方2010年5月的全景可见西门底层三道圆券、两扇八卦窗及上方石栏阳台。中间竖窗的顶端收成圆券，两侧各有一列窄窗。中央顶屏可辨R.A.S.三枚字母，两端的浅浮雕卷草分置在翼部檐顶。2011年的仰拍可分辨黑色金属窗下板及由右向左排列的「亞洲文會」石额。八卦窗的近拍可辨八组阴阳爻和中央弯曲的金属隔条。另以2007年的改造前街照核对窗带，以2013年街巷斜照、2015年窗饰近照核对修缮后的外观。[馆方2010年照片](https://commons.wikimedia.org/wiki/File:RAM_building.jpg) · [2011年窗饰](https://commons.wikimedia.org/wiki/File:Bagua_Window_of_the_NCBRAS.jpg) · [照片作者、日期、许可和字节校验](reference-review.json)

冻结城市源2274的OSM记录为w446934758第7版。与另取的第8版具名环交并比约93.91%。两者的西侧短边均邻虎丘路，模型采用冻结边线的12.282米宽。用馆方原片的24毫米焦距记录和街边两端做透视估算，两个翼部檐顶约21.8至22.0米。中央顶部约23.3米。地块、临街方向与照片中的结构可以交叉核验，高度、窗的内退、石栏挑距和阳台柱头的细部仍是估计值。切片向内约2.34米，其余三面、后期增建、馆内楼层、博物院广场及临时展览装置另待考察。[地块与相邻建筑](footprint-review.json) · [原片取点与估算](source/parameters.json)

## 工程与验收

生成器需要Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick及Open Image Denoise。从项目的 `projects/shanghai` 目录运行以下命令。四份成果使用独立几何和材质，未在其表面嵌入照片。项目原创代码与网格采用MIT许可，地块数据来自OpenStreetMap贡献者，采用ODbL 1.0。[单体预览](../../../royal-asiatic-society.html)

```sh
python source/precise/huangpu-royal-asiatic-society-huqiu-front/source/build_model.py \
  --out ./build/royal-asiatic-society-assets --audit ./build/royal-asiatic-society-audit \
  --decoded ./build/royal-asiatic-society-decoded --gltfpack /path/to/gltfpack --oidn /path/to/oidnDenoise
```
