# ESP32 Wi-Fi Config Portal (MicroPython Edition)

让一块刷了 **MicroPython** 的 ESP32 “开机自动联网、连不上就开热点、网页填密码再连上”，并把过程信息输出到串口 / OLED。  
本仓库包含 4 个核心脚本：

| 文件               | 作用                                                         |
| ------------------ | ------------------------------------------------------------ |
| `wifi_manager.py`  | STA / AP 管理、网络保存与重连、看门狗                         |
| `config_server.py` | 常驻 HTTP 服务器；网页列网、收表单、保存并尝试连接            |
| `display_manager.py` | OLED/LED 等指示层（示例实现，可根据实际硬件替换）           |
| `main.py`          | 引导流程 & 无限循环：网页轮询 + 网络看门狗 + 业务逻辑         |

`wifi_config.json` 存在于文件系统根目录，记录已保存 Wi-Fi 列表。

---

## 运行时逻辑

# 流程图

- 上电 / 软重启
  - 加载 `wifi_config.json`
    - **有连接记录**
      - 依次尝试已保存网络
        - **任一成功**
          - Connected（显示局域网 IP）
        - **全部失败**
          - 启动 AP（ESP32-Config）
    - **无记录**
      - 启动 AP（ESP32-Config）
  - 启动 AP 后
    - HTTP 服务器（0.0.0.0:80 常驻）
      - 浏览器访问 `192.168.4.1` 填表单
        - 提交表单（POST `/save`）
          - 写入 `wifi_config.json`
          - 立刻用提交的 SSID/PWD 连接
            - **成功**
              - 关闭 AP
              - Connected（显示局域网 IP）
            - **失败**
              - 保持 AP 等用户重新修改
  - Connected 后
    - 看门狗常循环（掉线/密码错误 >15s）
      - 启动 AP

---

## 关键实现

### 1. `wifi_manager.py`

* `save(ssid, pwd)`  
  把新网络写入或覆盖到 `wifi_config.json`；写后再读一次校验。
* `connect(ssid, pwd, timeout=15)`  
  STA 先 `disconnect()` 再 `connect()`；轮询 `isconnected()`；超时 || `STAT_WRONG_PASSWORD` 返回 `False`。
* `connect_saved()`  
  读取文件，按保存顺序循环 `connect()`，任一成功即返回 `True`。
* `start_ap()/stop_ap()`  
  WPA2 AP：`ESP32-Config / 12345678`，IP 为 `192.168.4.1`。
* `watchdog()`  
  每 0.1 s 调一次：  
  ‑ 已连上 → 无事；  
  ‑ `STAT_WRONG_PASSWORD / STAT_NO_AP_FOUND` → 立刻开热点；  
  ‑ `STAT_CONNECTING` 且持续 >15 s → `disconnect()` + 开热点。

### 2. `config_server.py`

* 内置 `url_decode()` 兼容 MicroPython 无 `urllib` / `ure.unquote_plus`。  
* `start()` 创建 `socket`, `listen(2)`, `settimeout(0.5)`，永不阻塞主循环。  
* `poll()`  
  1. `accept()`\* → `recv()` 1 kB → 根据首行路由  
  2. `GET /` 生成下拉 `<option>`；`scan()` 缺失时降级调用 `network.WLAN.scan()`  
  3. `POST /save`：先回 200 OK 防前端等待 → `wifi_manager.save()` → `wifi_manager.connect()` → 成功则 `stop_ap()`，失败则 `start_ap()`  
  4. 异常全部捕获，保证单次请求崩溃不会拖垮系统。

\* `accept()` 超时抛 `OSError`，由 `while True` 外层循环 0.1 s 处理。

### 3. `main.py`

```python
ui = ScreenUI()          # OLED 封装
wm = WiFiManager(ui)
srv = ConfigServer(wm, ui)

if not wm.connect_saved():
    wm.start_ap()

srv.start()              # HTTP server always ON

while True:
    srv.poll()           # 网页请求
    wm.watchdog()        # 网络保活
    # 你的项目逻辑 ...
    time.sleep(0.1)
```



---


## 终端输出日志示例

```
[WiFiManager] wifi_config.json 不存在，返回空字典
[WiFiManager] AP 已启动: ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
[ConfigServer] HTTP 服务已启动 (0.0.0.0:80)
[ConfigServer] 可访问地址: ['192.168.4.1']

===== 收到 HTTP 请求 =====
POST /save ...
[ConfigServer] 表单数据: {'ssid': 'MyHome', 'pwd': '12345678'}
[WiFiManager] 写入完成，再次读取确认 → {'networks':[...]}
[WiFiManager] 尝试连接: MyHome
[WiFiManager] 连接成功, IP: 192.168.31.123
[ConfigServer] 可访问地址: ['192.168.31.123']
