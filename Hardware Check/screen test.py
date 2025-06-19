import machine
import time
import gc

# 尝试导入不同的驱动
try:
    import sh1106
    print("使用SH1106驱动")
    USING_SH1106 = True
except:
    try:
        import ssd1306
        print("使用SSD1306驱动")
        USING_SH1106 = False
    except:
        print("错误: 找不到OLED驱动库!")
        raise

# 引脚定义
PIN_SCK  = 18
PIN_MOSI = 22
PIN_RES  = 16
PIN_DC   = 17
PIN_CS   = 5

# 屏幕尺寸
WIDTH = 128
HEIGHT = 64

# 手动硬件复位
reset_pin = machine.Pin(PIN_RES, machine.Pin.OUT)
reset_pin.value(1)
time.sleep(0.001)
reset_pin.value(0)
time.sleep(0.01)
reset_pin.value(1)
time.sleep(0.01)

# 初始化SPI - 尝试不同配置
spi = machine.SPI(1, 
                  baudrate=10000000, 
                  polarity=1, 
                  phase=0, 
                  sck=machine.Pin(PIN_SCK), 
                  mosi=machine.Pin(PIN_MOSI))

# 初始化显示屏
if USING_SH1106:
    display = sh1106.SH1106_SPI(WIDTH, HEIGHT, spi, 
                              machine.Pin(PIN_DC), 
                              machine.Pin(PIN_RES), 
                              machine.Pin(PIN_CS))
else:
    display = ssd1306.SSD1306_SPI(WIDTH, HEIGHT, spi, 
                                machine.Pin(PIN_DC), 
                                machine.Pin(PIN_RES), 
                                machine.Pin(PIN_CS))

# 强制初始化序列
display.init_display()
display.sleep(False)
display.contrast(255)  # 最大对比度

# 清屏并显示测试图案
display.fill(0)
display.show()
time.sleep(0.5)

# 显示像素测试
for y in range(0, HEIGHT, 2):
    for x in range(0, WIDTH, 2):
        display.pixel(x, y, 1)
display.show()
time.sleep(1)

# 显示文字
display.fill(0)
display.text("OLED TEST", 30, 0, 1)
display.text("Line 1", 0, 15, 1)
display.text("Line 2", 0, 25, 1)
display.text("Line 3", 0, 35, 1)
display.text("Line 4", 0, 45, 1)
display.hline(0, 55, 128, 1)
display.show()

print("测试完成 - 屏幕应该显示测试图案")

