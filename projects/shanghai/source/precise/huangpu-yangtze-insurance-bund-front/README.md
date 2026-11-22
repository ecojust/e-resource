# 扬子大楼外滩26号临江东立面

上海市房管局第三批优秀历史建筑名录3A001登记扬子大楼、扬子水火保险公司，地址中山东一路26号。南邻24号横滨正金银行，北邻27号怡和洋行。1927年出版的《Shanghai of Today》图版12把三栋摄在同一画面，26号以五轴窗墙和顶层两侧高窗区分。1908年的三层连拱照片显示同址前身。[市房管局第三批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [1927年图版](https://commons.wikimedia.org/wiki/File:Shanghai_of_Today,_Plate_12_-_Bank_of_China,_Bank_of_Yokohama,_Messrs_Jardine,_Matheson,_%26_Co,_Glen_Line.jpg) · [1908年旧楼](https://commons.wikimedia.org/wiki/File:Tcitp_d458_offices_of_the_yangtze_insurance_association.jpg)

《黄浦区续志》列1917年，市黄浦江两岸开发工作领导小组办公室《外滩故事》列1920年。《上海名建筑志》记公和洋行设计、七层钢筋混凝土，并写1928年动工。1927年的图版已能看见六层柱廊和七层侧窗，因此目前可落实这两项外观最晚已于1927年出现。[《黄浦区续志》](https://web.archive.org/web/20140117015505/http://www.shtong.gov.cn/newsite/node2/node4/node2249/node75735/node75740/node76396/node76402/userobject1ai90977.html) · [开发办《外滩故事》](https://web.archive.org/web/20150924031449/http://www.hpjbanks.com/history/wai5.asp) · [《上海名建筑志》](https://web.archive.org/web/20200927094900/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108930.html)

正面依2014年日照照片与2025年东面近景制作。底层两侧开门，中间是三扇长窗。二层五券窗带放射状石券、凸出的拱心石与通长铁栏。三至五层为竖向窗列和壁柱，五层柱顶另有浅浮雕花环，上端有大檐口。六层中央三间退廊由两对柱子分隔，后方有独立窗墙。七层两侧为较高的窗亭，中部屋顶退后。农行字牌按现在照片的六个汉字制作，字体、行徽、卷涡和雕花为近似。临街东面宽按具名底图为18.61米，窗宽、层高、檐口进深及旗杆高度根据照片估算。[2014年正面](https://commons.wikimedia.org/wiki/File:Yangtze_Building_The_Bund.JPG) · [2025年5月近景](https://commons.wikimedia.org/wiki/File:Yangtze_Insurance_Building_20250501.jpg) · [2025年11月三楼同框](https://commons.wikimedia.org/wiki/File:Yangtze_Insurance_Building_20251127.jpg)

底图源面2937标注中国农业银行，其英文别名是Yangtze Insurance Building。现行OSM建筑177931019直接登记门牌26、中山东一路、七层和扬子大楼旧名。与地图冻结轮廓的面积交并比为98.62%。仅替换东侧不足4米深的临街部分。西侧原体量、南北通道及两侧已有精模各保留在原位。三期卫星影像辅助核定楼界；西侧后部、设备和未见侧墙窗序另列。[具名源面及邻楼](footprint-review.json) · [三期卫星影像与现行轮廓](roof-reference.json) · [照片作者、授权和SHA-256](reference-review.json)

## 构件和重建

立面使用带真实进深的窗洞、两侧门洞、带柱身与涡卷的六层柱廊、独立平台和屋顶栏杆。网页使用三角面与可编辑Blender文件；照片仅作形态依据。现代行名字体子集采用SIL Open Font License 1.1。[字体许可](source/fonts/OFL.txt) · [独立模型与四项下载](../../../yangtze-insurance-bund-front.html)

在上海项目目录运行。打包器会导出原始GLB、近景和远景GLB、可编辑Blender文件，再解码网格并重新打开Blender核对面与材质。

```sh
python source/precise/huangpu-yangtze-insurance-bund-front/source/build_model.py \
  --out assets/models/candidates/huangpu-yangtze-insurance-bund-front \
  --audit data/audit/yangtze-insurance-bund-front-v1
```
