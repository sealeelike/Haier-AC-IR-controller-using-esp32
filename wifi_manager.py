import network, time, ujson, uio, os

CONFIG_FILE = "/wifi_config.json"

class WiFiManager:
    def __init__(self, ui=None):
        self.ui  = ui
        self.sta = network.WLAN(network.STA_IF); self.sta.active(True)
        self.ap  = network.WLAN(network.AP_IF);  self.ap.active(False)
        self._connecting_since = None

    # ---------- 文件操作 ----------
    def _load(self):
        if CONFIG_FILE[1:] not in os.listdir('/'):
            print("wifi_config.json 不存在，返回空字典")
            return {"networks": []}
        try:
            with uio.open(CONFIG_FILE) as f:
                cfg = ujson.load(f)
                print("读取 WiFi 配置:", cfg)
                return cfg
        except Exception as e:
            print("JSON 读取失败，重置为空，错误:", e)
            return {"networks": []}

    def _save(self, cfg_dict):
        try:
            with uio.open(CONFIG_FILE, "w") as f:
                ujson.dump(cfg_dict, f)
            print("写入完成，再次读取确认 →", self._load())
        except Exception as e:
            print("保存文件失败:", e)

    # ---------- API ----------
    def save(self, ssid, pwd):
        cfg = self._load()
        for n in cfg["networks"]:
            if n["ssid"] == ssid:
                n["password"] = pwd; break
        else:
            cfg["networks"].append({"ssid": ssid, "password": pwd})
        self._save(cfg)
        self.ui and self.ui.msg("Saved", ssid)

    def connect(self, ssid, pwd, timeout=15):
        print("尝试连接:", ssid)
        self.ui and self.ui.msg("Connecting", ssid)
        self.sta.disconnect()
        self.sta.connect(ssid, pwd)
        self._connecting_since = time.ticks_ms()
        while not self.sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), self._connecting_since) > timeout*1000:
                print("连接超时/密码错")
                self.ui and self.ui.msg("Connect FAIL", ssid)
                self.sta.disconnect()
                return False
            time.sleep(0.2)
        ip = self.sta.ifconfig()[0]
        print("连接成功, IP:", ip)
        self.ui and self.ui.msg("Connected", ip)
        return True

    def connect_saved(self):
        cfg = self._load()
        for n in cfg["networks"]:
            if self.connect(n["ssid"], n["password"]):
                return True
        return False

    # ---------- AP ----------
    def start_ap(self, ssid="ESP32-Config", pwd="12345678"):
        if self.ap.active(): return
        self.ap.active(True)
        self.ap.config(essid=ssid, password=pwd,
                       authmode=network.AUTH_WPA_WPA2_PSK)
        print("AP 已启动:", self.ap.ifconfig())
        self.ui and self.ui.msg("AP Mode", ssid, self.ap.ifconfig()[0])

    def stop_ap(self):
        if self.ap.active():
            self.ap.active(False)
            print("AP 已关闭")

    # ---------- 看门狗 ----------
    def watchdog(self):
        if self.sta.isconnected():
            return
        if self.sta.status() in (network.STAT_WRONG_PASSWORD,
                                 network.STAT_NO_AP_FOUND,
                                 network.STAT_CONNECT_FAIL):
            # 已明确失败
            self.start_ap()
        elif self.sta.status() == network.STAT_CONNECTING:
            if time.ticks_diff(time.ticks_ms(), self._connecting_since or 0) > 15000:
                # 卡太久
                self.sta.disconnect()
                self.start_ap()
                
    def scan(self):
        """
        返回 [(ssid(str), rssi(int), authmode(int)), ...]
        authmode 参考：0=open, 1=WEP, 2=WPA-PSK, 3=WPA2-PSK, 4=WPA/WPA2-PSK,
                       5=WPA2-Enterprise
        """
        nets = self.sta.scan()               # (ssid,bssid,chan,rssi,auth,hidden)
        nets = sorted(nets, key=lambda x: x[3], reverse=True)
        return [(n[0].decode(), n[3], n[4]) for n in nets]
