"""
config_server.py
常驻 HTTP 服务 (端口 80)
功能：
  • GET  /         -> 返回 WiFi 配置网页
  • POST /save     -> 保存 SSID/PWD 并尝试连接
界面同时可在 STA IP / AP IP 访问
"""

import socket, time, network

# ---------- URL 解码 ----------
def url_decode(s: str) -> str:
    """把 x-www-form-urlencoded 编码文本解码为普通字符串"""
    res = ""
    i = 0
    while i < len(s):
        c = s[i]
        if c == '+':
            res += ' '
            i += 1
        elif c == '%' and i + 2 < len(s):
            try:
                res += chr(int(s[i+1:i+3], 16))
                i += 3
            except ValueError:
                res += '%'      # 保留原字符
                i += 1
        else:
            res += c
            i += 1
    return res


class ConfigServer:
    def __init__(self, wifi_mgr, ui=None, port: int = 80):
        """
        wifi_mgr : 需提供 save(ssid,pwd)、connect(ssid,pwd)、scan() 可选、
                   sta(WLAN)、ap(WLAN)、stop_ap()、start_ap()
        ui       : 可选屏幕接口；若无可传 None
        port     : 默认为 80
        """
        self.wm   = wifi_mgr
        self.ui   = ui
        self.port = port
        self.sock = None

    # ---------- 启动 ----------
    def start(self):
        try:
            addr = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
            self.sock = socket.socket()
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(addr)
            self.sock.listen(2)
            self.sock.settimeout(0.5)          # 非阻塞轮询
            print("[ConfigServer] HTTP 服务已启动 (0.0.0.0:{})".format(self.port))
            self._show_ips()
        except Exception as e:
            print("[ConfigServer] 启动失败:", e)

    # ---------- 轮询：主循环里反复调用 ----------
    def poll(self):
        if not self.sock:
            return
        try:
            cl, addr = self.sock.accept()
        except OSError:                 # 无连接
            return
        except Exception as e:
            print("[ConfigServer] accept 异常:", e)
            return

        try:
            req = cl.recv(1024).decode()
            print("\n===== 收到 HTTP 请求 =====\n", req)

            # 首页
            if req.startswith("GET / "):
                cl.send(self._page_index())
                cl.close()
                return

            # 保存
            if req.startswith("POST /save"):
                form = self._parse_post(req)
                print("[ConfigServer] 表单数据:", form)
                ssid, pwd = form.get("ssid", ""), form.get("pwd", "")
                # 立即回一条响应给浏览器，防止前端等待
                cl.send(self._page_msg("Saving ..."))
                cl.close()

                # ---- 业务流程 ----
                self.wm.save(ssid, pwd)
                ok = self.wm.connect(ssid, pwd)

                if ok:
                    self.wm.stop_ap()
                else:
                    # 让用户继续配置
                    self.wm.start_ap()
                    self.ui and self.ui.msg("Connect FAIL", "Keep AP")

                self._show_ips()
                return

            # 其它
            cl.send("HTTP/1.1 404 Not Found\r\n\r\n")
            cl.close()

        except Exception as e:
            print("[ConfigServer] 处理请求异常:", e)
            try:
                cl.close()
            except:
                pass

    # ---------- HTML ----------
    def _page_index(self) -> str:
        try:
            nets = self.wm.scan()          # 优先调用 WiFiManager 的 scan
        except AttributeError:
            nets = network.WLAN(network.STA_IF).scan()

        # nets: [(ssid,bssid,chan,rssi,auth,hidden), ...] 或我们自定义的三元组
        options_html = ""
        for item in nets:
            ssid = item[0].decode() if isinstance(item[0], bytes) else item[0]
            rssi = item[3] if len(item) > 3 else item[1]
            options_html += f'<option value="{ssid}">{ssid} ({rssi}dBm)</option>'

        html = ("HTTP/1.1 200 OK\r\n\r\n"
                "<meta charset=utf-8>"
                "<h3>WiFi 设置</h3>"
                "<form method='post' action='/save'>"
                f"<select name='ssid'>{options_html}</select><br>"
                "密码: <input type='password' name='pwd'><br>"
                "<button type='submit'>保存并连接</button></form>")
        return html

    def _page_msg(self, msg: str) -> str:
        return "HTTP/1.1 200 OK\r\n\r\n<h3>{}</h3>".format(msg)

    # ---------- 工具 ----------
    def _parse_post(self, req: str) -> dict:
        body = req.split("\r\n\r\n", 1)[1]
        kv = {}
        for seg in body.split('&'):
            if '=' in seg:
                k, v = seg.split('=', 1)
                kv[k] = url_decode(v)
        return kv

    def _show_ips(self):
        ips = []
        try:
            if self.wm.sta.isconnected():
                ips.append(self.wm.sta.ifconfig()[0])
            if self.wm.ap.active():
                ips.append(self.wm.ap.ifconfig()[0])
        except Exception:
            pass
        if self.ui:
            self.ui.msg("Web @", *ips)
        print("[ConfigServer] 可访问地址:", ips)
