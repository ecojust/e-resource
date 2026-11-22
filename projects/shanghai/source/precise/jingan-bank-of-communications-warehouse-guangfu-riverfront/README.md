# 原交通银行仓库光复路临河立面

光复路195号登记为上海市第五批优秀历史建筑5H003，历史名称为交通银行仓库，后称四行仓库光二分库、创意仓库。1934年《交行通信》报道总行沿苏州河新建的四层钢骨水泥仓库开业。1947年上海电话簿英文第6页把交通银行的仓库明确列在“195 Kwangfoo”。光复路115–129号的光三分库另有5H004登记。[市房屋管理局登记表](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html?from=historical-building-list) · [1947年电话簿原页](https://archive.org/details/shanghai-telephone-directory-1947/page/n250/mode/1up) · [历史资料释读](measurements/1947-address-and-1934-opening.json)

模型按修缮后的外观制作。沿苏州河北岸可见十个宽开间，中央门楼上有三列窄窗。临河楼上39处钢窗和底层两翼30处商铺开口各自贯穿石墙。沿西山墙返回的11.10米内，可见两扇窄窗和一扇横窗。门额四字「光二倉庫」、台阶形双柱和山形柱冠采用立体构件，车道从门槛延伸到首个侧向分流，约14.9米深，可见前三对柱、横梁和两侧灯带。南侧屋面铺地延伸到设备房南缘，沿弧形女儿墙留有栏杆和嵌地灯。其余楼层内部、北院及上层设备用房仍待制作。[修缮团队图文](https://www.sohu.com/a/971431850_121124642) · [静安区完工报道](https://sh.people.com.cn/n2/2026/0604/c134768-41601453.html)

屋面南檐两端直距约59.37米，沿弧约59.64米。模型原点在中部门槛，X轴沿正门向东，Y轴向仓库内部，Z轴向上。设计方屋面平面与航片在两角对齐后，另取15个南檐点的图面纵向差中位数约0.21米。四个2019年街景站独立给出的中央檐冠高度约为门槛上21.84米，扰动估算的5%至95%区间为21.16至22.50米。窗框退深、局部洗石子饰面厚度、栏脚和屋面标高含估测。[屋面平面配准](measurements/roof-terrace-survey.json) · [街景标高计算](measurements/four-station-front-height.json) · [三维开口表](measurements/riverfront-layout.json)

## 构建与核验

在仓库的上海建模环境中可运行下列命令。近景与远景共用墙面、洞口和檐冠的测量基准。远景减少玻璃分片、管卡、灯槽等细部。

    python source/build_model.py --output ./guangfu-195.glb
    python source/build_model.py --lod --output ./guangfu-195-lod.glb
    python measurements/check_riverfront.py ./guangfu-195.glb ./guangfu-195-check.json
    python measurements/render_riverfront_survey.py ./guangfu-195.glb ./guangfu-195.jpg

编辑源按石墙、屋面、牌字、钢窗和通道分别命名，并附七个相机。常规发布命令调用仓库的网格压缩、Blender导出与独立回读检查。[来源与使用条件](SOURCES-LICENSE.md)

    python source/build_model.py --out ./guangfu-delivery --audit ./guangfu-audit
