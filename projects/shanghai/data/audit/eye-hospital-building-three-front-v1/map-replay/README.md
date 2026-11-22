# 眼耳鼻喉科医院三号楼院内西南立面

从上海项目目录运行 `python data/audit/eye-hospital-building-three-front-v1/map-replay/replay.py result.json`。需要 Python 3 和 Node.js。复验程序核对相邻两期目录的原始字节，在第349栋的底图上重算加入本栋后的遮罩及矢量余面，再与第350栋的实际登记和两张现场结果逐项比较。

原始矢量来自 OpenFreeMap 的 2026-11-15 底图，数据来源为 © OpenStreetMap contributors，开放数据库许可 ODbL。瓦片地址、原件与解码件的 SHA-256 均列在 signed-inputs.json。prepare-vector.py 可从原瓦片再生成解码件，需安装 NumPy、Shapely 和 mapbox-vector-tile。
