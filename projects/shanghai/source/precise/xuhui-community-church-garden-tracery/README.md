# 国际礼拜堂临衡山路七扇尖窗山墙

1925年建成的国际礼拜堂有高窄的红砖山墙、双扶壁和一组七扇竖向花窗。上海市房屋管理局第一批名录在1D002行登记衡山路58号，中国基督教网的本堂介绍使用衡山路53号。模型依据三个不同拍摄者所摄的同一尖券、七个窗冠、两个圆饰及双侧扶壁定栋。[中国基督教网](https://www.ccctspm.org/churchinfo/199) · [原照片目录](https://commons.wikimedia.org/wiki/Category:Shanghai_Community_Church)

三份原照分别为Livelikerw于2013年12月18日的右斜照、Fayhoo于2017年1月21日的正照、Szalai.laci于2018年3月4日的近院照。原始照片、文件签名、各自许可及独立读数见measurements/public-photo-measurement.json。在景观设计方刊出的历史对照照片中，窗裙下端和入口旧石饰能看得更清楚。门饰按该资料的历史外形表现，原照片摄年未标。[景观改造原刊](https://worldlandscapearchitect.com/historic-landscape-renovation-of-community-church-in-shanghai/)

五个带测站位置的冬季外业视点给出双侧扶壁中距约8.25米、顶部标高约13.78米、正脊尖约17.59米。模型的X轴沿山墙往照片右侧，与真北顺时针约215.80度。航片显示大堂与侧翼连成L形，现有原城户1917还含另一条长翼。这里交付临街山墙、尖窗及首段檐返。相机求解分别保留地理多站误差和三个独立作者机位误差。

运行 python measurements/fit_street_anchor.py、python measurements/fit_church.py、python measurements/make_church_cameras.py 可复算测站和九个机位。python measurements/check_mesh.py 输出目录 可重建两份GLB并检验每件的边界。几何与程序采用MIT许可。源照片只作建筑观察。

细部修订以Fayhoo的3956×2967原片测量了玻璃上的两族斜线。高通、汉宁窗和二维傅里叶谱得到相反斜率的两个主峰，投到窗面后横、竖周期约0.139和0.225米。Szalai.laci从堂内拍到相同的七扇窗和两处花饰，玻璃呈明暗菱格。外侧抱券在两张相片上分六个标高重新量读，模型采用约0.54米的石圈宽度。近院斜照也拍到了砖山墙斜边向前伸出的压顶。[从堂内看同一高窗](https://commons.wikimedia.org/wiki/File:Christian_Church_International_Chapel_Shanghai_back_window.jpeg)

旧稿有三个窗边或斜边测点未命中预期材料。修订后的三站共有34个独立像点，其中31处直接命中，其余3处在14个原像素内可找到对应表面。按原始照片拟合的残差中位数分别约为2.7、11.1及11.4像素，树枝、雨水管和斜拍下的檐缘使部分控制点不易精读。五个街站为尺度提供独立约束，个别扶壁顶的回投误差达到约26个原像素。更多原照数值见measurements。
