# 慈惠村太原路4弄1—2号临街转角
1922年建成的慈惠村位于太原路与汾阳路交角。市房管局第五批表列“住宅，太原路4弄”，HTML编号印作 D5035。区级登记码为 XH-J-035-V。徐汇2023年街区资料将慈惠村定位到4弄1—2号，并记占地约350平方米。2016年3月11日独立步行图录的绿色门牌可读作“太原路四弄1”。[市房管局](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [徐汇区图文](https://sh.people.com.cn/n2/2023/0428/c350122-40397986.html) · [中国の風景，2016](https://4travel.jp/travelogue/11115838)

太原路街面以三楼出挑的宽窗、下方三片铁饰和双层券窗辨认。2016年的地层两扇开口落到地面，2023年照片中的对应处有圆券、砌实窗裙与灰色窗台。模型采用后一时期。转入汾阳路，墙面分级升高，靠街的成排钢窗、折角窄券、排水管与灰色压顶可在相邻角度比对。这是两条街的外墙构件模型。院内、背墙和屋顶深处没有独立摄影控制。

五幅照片共用窗缘控制点。照相机、原观察栅格尺寸、未参与拟合的点及逐点残差见 measurements/registered-street-cameras.json。照片中树枝和街线遮蔽若干细构件。研究照片仅列原始出版地址与摘要，展示图从原创网格生成。模型的数值为相片估计。

在已安装项目依赖的工作目录运行以下命令，分别生成未压缩近景以及低细节原网。Blender入口可从同一份原网逐构件重建并二次重开。
```sh
python source/build_model.py near.glb --textures
python source/build_model.py far.glb --lod
python measurements/package_models.py work assets audit
python source/build_blender_source.py prepare near.glb native
python source/build_blender_source.py run near.glb native
```
几何及两张程序纹理采用MIT许可。

2020年街道机位分别量得太原路中层两券窗轴距约2.87米、底层约4.28–4.34米。将两组独立读数联合换算，现场取景支持的太原路街面长约12.4米。 汾阳路两扇白框券窗分别位于凸窗湾的两侧。其西侧另有黑框券窗，街站量得该窗玻璃约0.92×1.63米。从这里延伸到低檐翼还可辨两列钢窗、窗下铁栅和一层入口。朝街矮墙与铁栏遮住凸窗湾低段，模型按2016年转角照和2020年街照保留其外侧；屋顶后坡和院内没有展开。
