# 高邮路5弄32号住宅花园阳台与清水砖转角

上海市房屋管理局第五批名录把高邮路5弄32号列为徐汇区5D015，原登记名和现用途均为“住宅”。现场市牌载“花园里弄住宅。1931年竣工，砖木结构”，署2015年8月17日公布。祖强拍到的另一块区牌题“高邮路5弄34号花园住宅”，署2017年4月。祖强记录同楼一层用34号、二层用32号，乐哥的组照也将32、34并题并拍到32号门牌。模型取这栋楼的二层花园面和可从弄堂辨认的转角。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [祖强的两块牌及建筑外景](https://www.meipian.cn/3byew56n) · [乐哥的门牌与楼外组照](https://www.meipian.cn/30b44zsy)

花园面上，两樘宽钢窗各有六列五层玻璃，中心两道成对窗框比小格的细梃更宽。直立红砖压窗头，窗台边砖略向外挑。两窗之间是微退的阳台门和挑出的阳台板。砖墩顶有浅色压顶，细铁栏的上、下段可以看见成对的涡卷。中跨平檐比左右檐低，用浅色曲形撑架托住。右端转至侧面后，可见一段素砖墙与凸出的小间，两扇窄窗同在外伸墙带上。2022年发表的另一张侧照可作砖色、窗扇和退凸关系的旁证，画面所属墙段未用于摄影配准。[2022年建筑图录](https://www.meipian.cn/4bc41uqy)

模型截面下止于阳台板下可连续读出的砖段，上及红色封檐、檐下出木和左翼小烟囱。门内阴影处只表现能辨出的外缘和暗面。右侧窗下、院墙内的下层和主屋脊均被遮挡，完整底层和屋架仍待证。砖面与涂漆木檐使用程序生成纹理，钢窗分格、栏花、砖墩压顶和曲形支托可独立编辑。图版为模型实渲。[造型与照片来源](measurements/identity-and-photos.json) · [花园面与两扇侧窗](../../../data/audit/gaoyou-lane-5-no-32-garden-balcony-v1/garden-balcony-study.jpg)

用乐哥第6、59幅和祖强第100、101、102幅的窗洞、檐角和柱帽独立标点。各相机在原量测图的控制点中位偏差为1.5至3.75像素。两扇宽窗间距和钢窗纵横比例为摄影估计，一樘窗宽暂取1.44展示单位，绝对米制未经过现场测尺。侧墙远端进深和叶丛后的窗边尤易受透视影响。对原网及两份独立解码分别从这五个机位实射123束，每档103束首交与观察材质相符，107束在两像素内符合。细铁栏、窄封檐、叶隙和两道窗头的偏差均可回读。两篇文章发表于2020年，单张拍摄日未详。[五机位量测](measurements/garden-camera-survey.json) · [逐束首交及偏差](../../../data/audit/gaoyou-lane-5-no-32-garden-balcony-v1/five-camera-image-rays.json)

在本模型目录运行以下命令可重建几何和可编辑文件。摄影拟合使用 OpenCV 与 SciPy，几何与图版使用 NumPy、Shapely、Pillow、仓库内的共用建模工具、C编译器及 gltfpack。

```sh
mkdir -p work
python measurements/register_front.py
python source/build_model.py work/gaoyou32-raw.glb
python measurements/package_models.py work/exports work/assets work/audit --gltfpack gltfpack
python source/build_blender_source.py prepare work/exports/full-source.glb work/editable
python source/build_blender_source.py run work/exports/full-source.glb work/editable
```

[独立展页](../../../gaoyou-lane-5-no-32-garden-balcony.html)
