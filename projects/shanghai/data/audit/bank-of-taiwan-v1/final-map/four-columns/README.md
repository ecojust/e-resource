# 台银四柱首次取景

21115原153处目录从普通卡片进入时，390像素手机和870像素桌面的台银长灯牌压在东门廊上。手机继续按放大也会移向屋面。[原手机默认、放大及早期取证说明](../original-phone-zoom/) · [原桌面、手机及近远档整套](../original153/) · [原152处城市同址](../original152/)

对照原始两幅PNG的真实深绿色牌底，390屏至少遮住两根柱身593个像素，870屏四根均有遮挡，至少525个像素。数字未包含牌中文字及边框，所用实际近景轴身与修订版相同。[原图颜色与三维投影比对](original-projection/original-coverage.json)

隔离试站C（26116）只为台银这一个长L形模型指定相机焦点和灯牌应避让的构件，两个参数均在可下载GLB的实际边界内。朝向与俯角保持为−62°、37°。在街区目录展开的870像素桌面上仍可选择邻近的外滩15号。390像素手机可触控本楼灯牌及放大按钮。所有取样均在启动遮罩消失、近景54,008面及228号源裁切生效后进行。[试站桌面](c-actual/desktop-default.png) · [手机首次进入](c-actual/mobile-default.png) · [手机一次放大](c-actual/mobile-plus.png) · [真实点击和原始响应](c-actual/browser.json)

从解码的近景中提取4根银灰色花岗石轴身，每根984个三角面，高度1.52至13.42米。按实际浏览器画面的投影绘制轴身轮廓，并与地图真实绘出的灯牌矩形逐像素相交。390默认、390一次放大、870展开目录三个状态的全部12个轴身样本均为0像素重叠；三个画面中的90个牌内取点均与实际建筑一致。[逐柱覆盖数据](c-actual/shaft-coverage.json) · [实际四柱三角面](columns.json) · [复核算法](measure.py)

新配准实跑只多出两条显示范围，真实体量、定位、四件下载、原源保留、地面碰撞与邻栋参数逐项相同。23115正式目录153处，共697份输入、611,815,947字节，逐一按HTTP正文校验SHA-256。[配准差异与原新签名](revised-placement/binding-difference.json) · [23115全部HTTP输入](accepted-http.json)

23115正式版的390手机及870桌面默认均完整呈现四根轴身，四柱与灯牌、地点卡及视口边界的交叠均为0。手机再按一次放大，最右柱的右边界到393.032像素，越出390像素视口3.032像素，39个轴身像素出屏、4,749个仍在屏内。左柱有1,532个屏内轴身像素在下方地点卡矩形下。该放大视图的四柱仍分别有4,832、4,795、4,794、4,749个屏内像素，任何柱身与姓名牌交叠都是0。最初将放大也要求全部入屏的断言失败，原检验和错误保留下来。此前曾把放大态的四柱误说成完整入屏，以上述逐柱投影实测为准。[正式手机默认](formal-23115/mobile-default.png) · [正式手机一次放大](formal-23115/mobile-plus.png) · [正式桌面默认](formal-23115/desktop-default.png) · [正式逐柱像素、边界与地点卡](formal-23115/shaft-coverage.json) · [90项牌内命中和实际点击签收](formal-23115/accepted.json) · [首次断言记录](preflight-all-three-views/first-verification.log)

复验时先用项目通用Meshoptimizer解码网页近景，再从项目根路径和解码文件生成同样的柱体采样。浏览器检查程序接受站点根URL和新的输出目录，启动依赖Playwright和Chromium。最后根据同一运行的投影、真实PNG和各牌边界复算像素。

```bash
python extract-column-shafts.py /path/to/projects/shanghai /path/to/decoded/full.glb /tmp/taiwan-column-check
node check.cjs http://127.0.0.1:23115/ /tmp/taiwan-final-browser
python measure.py /tmp/taiwan-final-browser
python verify-final.py /tmp/taiwan-final-browser /path/to/115-production.json http://127.0.0.1:23115/
```

原始21115画面的色块下限也可重放，首个参数使用21115原站上海项目目录，包含未变动的MapLibre版本和原153处目录。

```bash
node replay-original-cameras.mjs /path/to/original153/projects/shanghai /tmp/taiwan-original-replay
python measure-original-colours.py /tmp/taiwan-original-replay
```
