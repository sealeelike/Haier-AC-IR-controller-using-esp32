from machine import Pin, Timer
import time
import array
import utime

class IRReceiver:
    def __init__(self, pin_num):
        self.ir_pin = Pin(pin_num, Pin.IN)
        self.timer = Timer(0)
        self.pulse_buffer = array.array('i', [0] * 1000)  # 缓冲区支持999个脉冲
        self.buffer_index = 0
        self.recording = False
        self.start_time = 0
        
    def start_recording(self, timeout_ms=6000):  # 缩短为6秒
        self.buffer_index = 0
        self.recording = True
        self.start_time = utime.ticks_us()
        
        self.ir_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._pulse_handler)
        self.timer.init(period=timeout_ms, mode=Timer.ONE_SHOT, callback=self._timeout_handler)
        
    def _pulse_handler(self, pin):
        if not self.recording:
            return
            
        current_time = utime.ticks_us()
        if self.buffer_index > 0:
            duration = utime.ticks_diff(current_time, self.start_time)
            if duration > 0:
                self.pulse_buffer[self.buffer_index - 1] = duration
            else:
                self.pulse_buffer[self.buffer_index - 1] = 1  # 避免负值
        self.buffer_index += 1
        self.start_time = current_time
            
    def _timeout_handler(self, timer):
        if self.recording:
            self._stop_recording()
            
    def _stop_recording(self):
        self.recording = False
        self.ir_pin.irq(handler=None)
        self.timer.deinit()
        
    def is_recording(self):
        return self.recording
        
    def get_raw_data(self):
        if self.buffer_index <= 1:
            return []  # 未记录有效数据时返回空列表
        return self.pulse_buffer[:self.buffer_index - 1]  # 返回有效脉冲数据

def display_progress_bar(current, total, bar_length=20):
    """显示记录进度条"""
    percent = float(current) / total
    arrow = '=' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(arrow))
    print(f"\r[{arrow}{spaces}] {int(percent * 100)}%", end='')

def learn_single_ir_code(receiver):
    """记录单次红外信号"""
    print("\n开始记录，请按下遥控器按键...")
    receiver.start_recording(timeout_ms=6000)  # 6秒超时
    
    start_time = time.time()
    while receiver.is_recording():
        elapsed = time.time() - start_time
        if elapsed > 6:
            break
        display_progress_bar(elapsed, 6)  # 进度条为6秒
        time.sleep(0.1)
    
    print()  # 换行
    raw_data = receiver.get_raw_data()
    if raw_data:
        return raw_data
    return None

def learn_ir_command(pin_num=23, command_name="未命名"):
    """学习一个红外指令，记录3次"""
    print(f"\n开始学习指令: {command_name}")
    print("=" * 40)
    
    receiver = IRReceiver(pin_num)
    recorded_data = []
    
    for attempt in range(3):
        print(f"\n第 {attempt + 1} 次记录:")
        
        raw_data = learn_single_ir_code(receiver)
        
        if raw_data:
            recorded_data.append(raw_data)
            print(f"✓ 捕获信号: {len(raw_data)}个脉冲")
            print(f"  时序数据（前10个）：{raw_data[:10]}")
        else:
            print("✗ 未检测到有效信号")
            recorded_data.append(None)
        
        if attempt < 2:
            print("准备下一次记录...")
            time.sleep(1)
    
    print(f"\n{command_name} - 学习结果分析:")
    print("-" * 30)
    
    valid_data = [data for data in recorded_data if data is not None]
    print(f"有效记录: {len(valid_data)}/3")
    
    if len(valid_data) == 0:
        print("❌ 所有记录都失败")
        return None
    
    for i, data in enumerate(recorded_data):
        if data:
            print(f"记录 {i+1}: {len(data)}个脉冲")
        else:
            print(f"记录 {i+1}: 失败")
    
    print("\n完整的原始数据:")
    for i, data in enumerate(recorded_data):
        if data:
            formatted_data = '[' + ','.join(map(str, data)) + ']'  # 逗号后无空格
            print(f"第{i+1}次记录: {formatted_data}")
        else:
            print(f"第{i+1}次记录: 无数据")
    
    return recorded_data

def learn_multiple_commands(pin_num=23):
    """学习多个红外指令"""
    print("IR遥控器学习模式")
    print("=" * 50)
    
    commands = {}
    
    while True:
        print(f"\n已学习指令数量: {len(commands)}")
        if commands:
            print("已学习的指令:")
            for name in commands.keys():
                print(f"  - {name}")
        
        command_name = input("\n请输入要学习的指令名称 (输入'quit'退出): ").strip()
        
        if command_name.lower() == 'quit':
            break
        
        if not command_name:
            print("指令名称不能为空")
            continue
        
        if command_name in commands:
            overwrite = input(f"指令'{command_name}'已存在，是否覆盖? (y/n): ").strip().lower()
            if overwrite != 'y':
                continue
        
        recorded_data = learn_ir_command(pin_num, command_name)
        if recorded_data:
            commands[command_name] = recorded_data
            print(f"✓ 指令'{command_name}'学习完成")
        else:
            print(f"✗ 指令'{command_name}'学习失败")
    
    print(f"\n学习完成! 共学习了 {len(commands)} 个指令:")
    print("=" * 50)
    for name, data_list in commands.items():
        print(f"\n指令: {name}")
        for i, data in enumerate(data_list):
            if data:
                print(f"  记录 {i+1}: {len(data)}个脉冲")
                formatted_data = '[' + ','.join(map(str, data)) + ']'  # 逗号后无空格
                print(f"  原始数据: {formatted_data}")
            else:
                print(f"  记录 {i+1}: 无数据")
    
    return commands

if __name__ == "__main__":
    learned_commands = learn_multiple_commands()
    
    if learned_commands:
        print(f"\n可以将以下数据保存用于后续使用:")
        print(learned_commands)

