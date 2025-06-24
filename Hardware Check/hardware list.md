| 元件 | 型号/规格 | 数量 | 备注 |
| :--- | :--- | :--- | :--- |
| 主控板 | ESP32-DevKitC (3V3,EN,UP,UN,GND,D0-D3,CMD,5V,CLK,0,2,15,4,16,17,18,5,19,21,RX,TX,22,23,34,35,32,25,26,27,14,12,13)| 1 | 无 |
| 显示屏 | 1.3英寸 OLED 模块 （(GND,VCC,SCK,SDA,RES,DC,CS)）| 1 | 关键: 驱动芯片为SH1106(涉及库的使用) |
| 红外接收器 | 开箱即用模块 | 1 | 无 |
| 红外发射管 | 开箱即用模块 | 1 | |
| NPN三极管 | S8050 | 1 | 用于放大发射信号。（尚未使用） |
| 电阻 | 各阻值 | 若干 | 未使用 |
| 连接附件 | 面包板、杜邦线 | 若干 | |


esp32具体型号
```
>python -m esptool --chip auto -p COM5 chip_id
esptool.py v4.9.0
Serial port COM5
Connecting....
Detecting chip type... Unsupported detection protocol, switching and trying again...
Connecting.....
Detecting chip type... ESP32
Chip is ESP32-D0WD-V3 (revision v3.1)
Features: WiFi, BT, Dual Core, 240MHz, VRef calibration in efuse, Coding Scheme None
Crystal is 40MHz
MAC: f0:24:f9:0a:7b:f8
Uploading stub...
Running stub...
Stub running...
Warning: ESP32 has no Chip ID. Reading MAC instead.
MAC: f0:24:f9:0a:7b:f8
Hard resetting via RTS pin...
```
