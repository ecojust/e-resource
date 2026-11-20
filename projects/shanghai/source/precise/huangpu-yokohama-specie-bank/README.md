# 横滨正金银行大楼

中山东一路24号位于23号中国银行以北、26号扬子大楼以南。上海市房管局第二批2A009登记“横滨正金银行”，公布时的使用单位为“工商银行；纺织控股集团公司”。《上海名建筑志》载这幢钢筋混凝土建筑由公和洋行设计，1923年开工，1924年8月竣工，共六层，建筑面积18,932平方米，占地约2,500平方米。1927年的外滩照片已经显示两根巨柱和上层退台。[市房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [《上海名建筑志》存档](https://web.archive.org/web/20200927092242/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108929.html) · [1927年街景](https://commons.wikimedia.org/wiki/File:Shanghai_of_Today,_Plate_12_-_Bank_of_China,_Bank_of_Yokohama,_Messrs_Jardine,_Matheson,_%26_Co,_Glen_Line.jpg)

东立面按当前外观制作。底层三道铜门可辨圆形门饰和上楣格栅。二至五层的十二扇窗分作三列，深色窗间墙前有一对从石座升起的爱奥尼克式巨柱。外侧窗下是独立的悬挑阳台与铁栏。六层向后退，中央三扇长窗，两端各一扇小窗，中央分级的女儿墙高于两侧。2006、2014、2021与2025年的街面照片可相互校对。地方志另提及武士与菩萨雕像，本版保留其所在的装饰区域，人物面容和身份细部仍待近照确认。现代工商银行字牌按2025年可见文字制作。[2014年正立面](https://commons.wikimedia.org/wiki/File:Yokohama_Specie_Bank_Building_Shanghai.JPG) · [2014年柱头](https://commons.wikimedia.org/wiki/File:Yokohama_Specie_Bank_Building_Shanghai_2.JPG) · [2025年正面](https://commons.wikimedia.org/wiki/File:上海横滨正金银行旧址2025.3.jpg) · [照片署名、日期与校验记录](reference-review.json)

旧时五层顶部铭板写过横滨正金银行名称，1945年后曾改作中央银行，后又移除。此模型的窗列与雕檐可与1927年照片比较，现用标识和门面参照当代照片。后翼沿具名L形底图铺设，屋顶按2018、2021、2024三个发布时间的航片估绘。层高、石雕深度、西后翼窗序和机电体量均为外部估计。单位为米，本地东向轴略偏向南。主入口朝向黄浦江。[杨浦图书馆《外滩24号横滨正金银行大楼》](https://web.archive.org/web/20140222030630/http://www.yplib.org.cn/structure/jdsh/bnsz/dg_76244_1.htm) · [底图、门牌与周边业主](footprint-review.json)

## 编辑和重建

在上海项目内运行下列命令。需要 Python、Shapely、NumPy、FontTools、Node、gltfpack、Blender 与 Open Image Denoise。两根柱子的截面、涡卷、窗洞、文字、门饰与屋顶均由几何源定义。原生场景按构件和材质分组，所有图片仅供研究。

```sh
python source/precise/huangpu-yokohama-specie-bank/source/build_model.py --out /tmp/bund24-model --audit /tmp/bund24-audit --decoded /tmp/bund24-decoded
```

[构件几何](source/yokohama_geometry.py) · [可编辑场景的相机](source/preview_camera.py) · [字牌字体来源和许可](source/fonts/provenance.json) · [独立模型页面](../../../yokohama-specie-bank.html)
