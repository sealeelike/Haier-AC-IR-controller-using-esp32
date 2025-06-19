from machine import Pin
import time

# 配置红外接收器连接到GPIO15
ir_pin = Pin(23, Pin.IN)

# 测试时长(秒)
test_duration = 50

print(f"红外接收测试程序 - 将在{test_duration}秒内统计信号变化")
print("请在此期间按下空调遥控器按钮")

# 初始化变量
signal_count = 0
last_state = ir_pin.value()
start_time = time.time()

try:
    while time.time() - start_time < test_duration:
        current_state = ir_pin.value()
        
        # 检测状态变化
        if current_state != last_state:
            signal_count += 1
            print(f"信号变化: {last_state} -> {current_state}, 总计: {signal_count}")
            last_state = current_state
        
        time.sleep(0.01)  # 短暂延时，但保持足够快的采样率
    
    print(f"\n测试结束! {test_duration}秒内检测到{signal_count}次信号变化")
    
except KeyboardInterrupt:
    elapsed = time.time() - start_time
    print(f"\n程序已手动停止! {elapsed:.1f}秒内检测到{signal_count}次信号变化")

