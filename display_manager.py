# ScreenUI：把 OLED 当“指示灯”用
import machine, time

# ==== 修改为自己实际布线 ====
PIN_SCK  = 18
PIN_MOSI = 22
PIN_RES  = 16
PIN_DC   = 17
PIN_CS   = 5
WIDTH, HEIGHT = 128, 64
# ===========================

class ScreenUI:
    def __init__(self):
        # 自动判定驱动
        try:
            import sh1106 as oled_drv
            drv = oled_drv.SH1106_SPI
        except ImportError:
            import ssd1306 as oled_drv
            drv = oled_drv.SSD1306_SPI

        self._hard_reset()
        spi = machine.SPI(1, baudrate=10_000_000,
                          polarity=1, phase=0,
                          sck=machine.Pin(PIN_SCK),
                          mosi=machine.Pin(PIN_MOSI))
        self.disp = drv(WIDTH, HEIGHT, spi,
                        machine.Pin(PIN_DC),
                        machine.Pin(PIN_RES),
                        machine.Pin(PIN_CS))
        self.disp.init_display()
        self.disp.sleep(False)
        self.disp.contrast(255)

    # ---------------- 公共接口 ----------------
    def clear(self):
        self.disp.fill(0)
        self.disp.show()

    def msg(self, *lines):
        """最多显示 6 行文本"""
        self.disp.fill(0)
        for i, ln in enumerate(lines[:6]):
            self.disp.text(str(ln)[:21], 0, i * 10, 1)
        self.disp.show()

    def blink(self, n=1, gap=0.2):
        """反色闪屏 n 次"""
        for _ in range(n):
            self.disp.invert(True)
            time.sleep(gap)
            self.disp.invert(False)
            time.sleep(gap)

    def progress(self, percent):
        """在底部画进度条"""
        percent = max(0, min(100, percent))
        bar_w = int(WIDTH * percent / 100)
        y = HEIGHT - 6
        self.disp.fill_rect(0, y, WIDTH, 6, 0)
        self.disp.fill_rect(0, y, bar_w, 6, 1)
        self.disp.show()

    # ---------------- 内部工具 ----------------
    def _hard_reset(self):
        rst = machine.Pin(PIN_RES, machine.Pin.OUT)
        rst.value(1); time.sleep_ms(1)
        rst.value(0); time.sleep_ms(10)
        rst.value(1); time.sleep_ms(10)
