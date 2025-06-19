from machine import Pin, Timer
import time
import array
import utime

class IRReceiver:
    def __init__(self, pin_num):
        self.ir_pin = Pin(pin_num, Pin.IN)
        self.timer = Timer(0)
        self.pulse_buffer = array.array('i', [0] * 1000)
        self.buffer_index = 0
        self.recording = False
        self.start_time = 0
      
    def start_recording(self, timeout_ms=6000):
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
                self.pulse_buffer[self.buffer_index - 1] = 1
        self.buffer_index += 1
        self.start_time = current_time
          
    def _timeout_handler(self, timer):
        if self.recording:
            self._stop_recording()
          
    def _stop_recording(self):
        self.recording = False
        self.ir_pin.irq(handler=None)
        self.timer.deinit()
      
    def stop_recording_immediately(self):
        """立即停止记录"""
        if self.recording:
            self._stop_recording()
      
    def is_recording(self):
        return self.recording
      
    def get_raw_data(self):
        if self.buffer_index <= 1:
            return []
        return list(self.pulse_buffer[:self.buffer_index - 1])

def display_progress_bar(current, total, bar_length=20):
    """显示记录进度条"""
    percent = float(current) / total
    arrow = '=' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(arrow))
    print(f"\r[{arrow}{spaces}] {int(percent * 100)}%", end='')

def get_number_choice(prompt, options, descriptions=None):
    """获取数字选择输入"""
    while True:
        if descriptions:
            print(f"\n{prompt}")
            for i, desc in enumerate(descriptions, 1):
                print(f"  {i}. {desc}")
        choice = input(f"请选择 (1-{len(options)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            else:
                print(f"请输入 1-{len(options)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")

def get_ac_parameters():
    """获取空调参数"""
    print("\n请设置空调参数:")
    print("-" * 30)
    
    # 首先询问操作类型
    type_options = ['switch', 'modify']
    type_descriptions = ['开关切换 (开机/关机)', '模式调节 (在开机状态下调节)']
    operation_type = get_number_choice("操作类型:", type_options, type_descriptions)
    
    # 根据操作类型设置开关状态
    if operation_type == 'modify':
        # 如果是模式调节，power 自动设为 on
        power = 'on'
        print("\n(模式调节时，空调默认为开启状态)")
    else:
        # 如果是开关切换，询问开关状态
        power_options = ['on', 'off']
        power_descriptions = ['开', '关']
        power = get_number_choice("开关状态:", power_options, power_descriptions)
  
    # 模式
    mode_options = ['auto', 'cool', 'dry', 'fan', 'heat']
    mode_descriptions = ['循环', '制冷', '除湿', '吹风', '制热']
    mode = get_number_choice("运行模式:", mode_options, mode_descriptions)
  
    # 辅热（只有制热模式才询问）
    aux_heat = 'off'
    if mode == 'heat':
        aux_heat_options = ['on', 'off']
        aux_heat_descriptions = ['开', '关']
        aux_heat = get_number_choice("辅热:", aux_heat_options, aux_heat_descriptions)
  
    # 风速
    fan_speed_options = ['1', '2', '3', 'auto']
    fan_speed_descriptions = ['低速', '中速', '高速', '自动']
    fan_speed = get_number_choice("风速:", fan_speed_options, fan_speed_descriptions)
  
    # 温度
    while True:
        try:
            temp = input("\n温度 (16-30°C): ").strip()
            temp_int = int(temp)
            if 16 <= temp_int <= 30:
                break
            else:
                print("温度范围应在 16-30°C 之间")
        except ValueError:
            print("请输入有效的温度数字")
  
    # 风向
    swing_options = ['fixed', 'swing']
    swing_descriptions = ['定向', '摆动']
    swing = get_number_choice("风向:", swing_options, swing_descriptions)
    
    # 备注说明
    print("\n备注 (选填，直接回车跳过):")
    specification = input("请输入备注信息: ").strip()
    if not specification:
        specification = " "
  
    # 生成描述性名称
    mode_cn = {'auto':'循环', 'cool':'制冷', 'dry':'除湿', 'fan':'吹风', 'heat':'制热'}
    power_cn = {'on':'开', 'off':'关'}
    swing_cn = {'fixed':'定向', 'swing':'摆动'}
    type_cn = {'switch':'开关切换', 'modify':'模式调节'}
  
    description = f"{type_cn[operation_type]}_{power_cn[power]}_{mode_cn[mode]}_{temp}度_风速{fan_speed}_{swing_cn[swing]}"
    if mode == 'heat' and aux_heat == 'on':
        description += "_辅热开"
  
    return {
        'type': operation_type,
        'power': power,
        'mode': mode,
        'aux_heat': aux_heat,
        'fan_speed': fan_speed,
        'temperature': temp,
        'swing': swing,
        'specification': specification,
        'description': description
    }

def save_to_csv(params, hex_code):
    """将结果保存到CSV文件，使用数字选项表示参数"""
    try:
        # 定义映射字典
        type_map = {'switch': '1', 'modify': '2'}
        power_map = {'on': '1', 'off': '2'}
        mode_map = {'auto': '1', 'cool': '2', 'dry': '3', 'fan': '4', 'heat': '5'}
        aux_heat_map = {'on': '1', 'off': '2'}
        fan_speed_map = {'1': '1', '2': '2', '3': '3', 'auto': '4'}
        swing_map = {'fixed': '1', 'swing': '2'}
      
        # 将参数转换为数字选项
        type_num = type_map.get(params['type'], '0')
        power_num = power_map.get(params['power'], '0')
        mode_num = mode_map.get(params['mode'], '0')
        aux_heat_num = aux_heat_map.get(params['aux_heat'], '0')
        fan_speed_num = fan_speed_map.get(params['fan_speed'], '0')
        swing_num = swing_map.get(params['swing'], '0')
        
        # 处理备注中的特殊字符（避免CSV格式问题）
        specification = params['specification'].replace(',', '，').replace('\n', ' ').replace('\r', ' ')
      
        # 检查文件是否存在，如果不存在则创建并写入标题
        try:
            with open('result.txt', 'r') as f:
                pass
        except:
            with open('result.txt', 'w') as f:
                f.write("type(switch=1/modify=2),power(on=1/off=2),mode,aux_heat,fan_speed,temperature,swing,specification,hex_code,timestamp\n")
      
        # 追加数据
        with open('result.txt', 'a') as f:
            # 获取当前时间
            timestamp = time.localtime()
            time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                timestamp[0], timestamp[1], timestamp[2],
                timestamp[3], timestamp[4], timestamp[5]
            )
            f.write(f"{type_num},{power_num},{mode_num},{aux_heat_num},{fan_speed_num},{params['temperature']},{swing_num},{specification},{hex_code},{time_str}\n")
        print(f"✓ 已保存到result.txt")
    except Exception as e:
        print(f"⚠️  保存失败: {e}")

def check_pulse_consistency(recorded_data):
    """检查脉冲数一致性"""
    valid_data = [data for data in recorded_data if data is not None]
    if len(valid_data) < 2:
        return True, ""
  
    pulse_counts = [len(data) for data in valid_data]
    avg_count = sum(pulse_counts) / len(pulse_counts)
  
    # 检查脉冲数差异
    deviations = [abs(count - avg_count) for count in pulse_counts]
    max_deviation = max(deviations)
  
    if max_deviation > avg_count * 0.2:  # 差异超过20%
        return False, f"脉冲数不一致: {pulse_counts}。请确保每次按同一个按键！"
  
    # 检查脉冲数是否在合理范围
    if avg_count < 10:
        return False, f"脉冲数过少({int(avg_count)}个)，可能未正确接收信号"
    if avg_count > 500:
        return False, f"脉冲数过多({int(avg_count)}个)，可能存在干扰"
  
    return True, ""

def analyze_pulse_widths(data):
    """分析脉冲宽度分布"""
    if not data:
        return 0, 0, 0
  
    short_count = sum(1 for v in data if 400 <= v <= 700)
    long_count = sum(1 for v in data if 1500 <= v <= 1900)
    unknown_count = len(data) - short_count - long_count
  
    return short_count, long_count, unknown_count

def decode_ir_data(recorded_data_list):
    """解码红外数据 - 带详细错误检查"""
    # 步骤1：检查数据一致性
    consistency_ok, error_msg = check_pulse_consistency(recorded_data_list)
    if not consistency_ok:
        return None, error_msg
  
    # 步骤2：处理每组数据
    processed_data_list = []
    pulse_quality_info = []
  
    for i, data in enumerate(recorded_data_list):
        if data and len(data) > 4:
            # 移除前4个元素
            trimmed_data = data[4:]
            # 提取偶数位置的元素
            even_position_elements = trimmed_data[1::2]
            processed_data_list.append(even_position_elements)
          
            # 分析脉冲质量
            short, long, unknown = analyze_pulse_widths(even_position_elements)
            total = len(even_position_elements)
            quality = (short + long) / total if total > 0 else 0
            pulse_quality_info.append((i+1, quality))
  
    if not processed_data_list:
        return None, "没有有效数据可供解码"
  
    # 检查脉冲质量
    avg_quality = sum(q[1] for q in pulse_quality_info) / len(pulse_quality_info)
    if avg_quality < 0.7:  # 70%的脉冲应该在预期范围内
        return None, f"信号质量差(仅{int(avg_quality*100)}%的脉冲在预期范围内)，可能是不支持的协议"
  
    # 步骤3：转换为二进制
    binary_lists = []
    for data in processed_data_list:
        binary_list = []
        for value in data:
            if 400 <= value <= 700:
                binary_list.append('0')
            elif 1500 <= value <= 1900:
                binary_list.append('1')
            else:
                binary_list.append('?')
        binary_lists.append(binary_list)
  
    # 步骤4：生成共识字符串并检查一致性
    max_length = max(len(lst) for lst in binary_lists)
    consensus = []
    disagreement_count = 0
  
    for i in range(max_length):
        count_0 = 0
        count_1 = 0
      
        for lst in binary_lists:
            if i < len(lst):
                if lst[i] == '0':
                    count_0 += 1
                elif lst[i] == '1':
                    count_1 += 1
      
        total_valid = count_0 + count_1
        if total_valid == 0:
            consensus.append('?')
            disagreement_count += 1
        elif count_0 > count_1:
            consensus.append('0')
            # 检查共识度
            if count_1 > 0 and count_1 / total_valid > 0.3:
                disagreement_count += 1
        elif count_1 > count_0:
            consensus.append('1')
            # 检查共识度
            if count_0 > 0 and count_0 / total_valid > 0.3:
                disagreement_count += 1
        else:
            consensus.append('?')
            disagreement_count += 1
  
    # 检查共识度
    consensus_rate = 1 - (disagreement_count / max_length) if max_length > 0 else 0
    if consensus_rate < 0.8:  # 80%的位应该有明确共识
        return None, f"数据一致性差(共识度仅{int(consensus_rate*100)}%)，可能按了不同的按键"
  
    # 步骤5：转换为十六进制
    binary_string = ''.join(consensus)
    clean_binary = ''.join(c for c in binary_string if c in '01')
  
    if not clean_binary:
        return None, "无法生成有效的二进制数据"
  
    if len(clean_binary) < 8:
        return None, f"解码后的数据过短(仅{len(clean_binary)}位)，可能信号不完整"
  
    try:
        decimal_value = int(clean_binary, 2)
        hex_value = hex(decimal_value)[2:].upper()
      
        # 检查是否全0或全1
        if decimal_value == 0:
            return None, "解码结果全为0，可能存在问题"
        if clean_binary.count('1') == len(clean_binary):
            return None, "解码结果全为1，可能存在问题"
      
        return hex_value, None
    except:
        return None, "转换为十六进制时出错"

def record_single_signal(receiver, attempt_num, first_pulse_count=None, max_retries=3):
    """记录单次信号，支持重试"""
    retry_count = 0
  
    while retry_count < max_retries:
        if retry_count > 0:
            print(f"\n重试第 {retry_count}/{max_retries-1} 次...")
          
        print(f"\n第 {attempt_num}/6 次记录:")
        print("请设置空调到相应状态，然后按下遥控器...")
      
        receiver.start_recording(timeout_ms=6000)
      
        start_time = time.time()
        while receiver.is_recording():
            elapsed = time.time() - start_time
            if elapsed > 6:
                break
            display_progress_bar(elapsed, 6)
            time.sleep(0.1)
      
        print()  # 换行
        raw_data = receiver.get_raw_data()
      
        # 检查是否接收到信号
        if not raw_data:
            print("✗ 未检测到有效信号")
            retry_count += 1
            if retry_count < max_retries:
                print("请检查遥控器是否对准接收器，并确保按键正确")
                time.sleep(1)
                continue
            else:
                print("❌ 多次尝试后仍未接收到信号")
                return None, "未接收到信号"
      
        current_pulse_count = len(raw_data)
        print(f"✓ 捕获信号: {current_pulse_count}个脉冲")
      
        # 检查脉冲数是否在合理范围
        if current_pulse_count < 10:
            print(f"⚠️  脉冲数过少({current_pulse_count}个)")
            retry_count += 1
            if retry_count < max_retries:
                print("信号可能未完整接收，请重新尝试")
                time.sleep(1)
                continue
            else:
                return None, "脉冲数过少"
        elif current_pulse_count > 500:
            print(f"⚠️  脉冲数过多({current_pulse_count}个)")
            retry_count += 1
            if retry_count < max_retries:
                print("可能存在干扰，请重新尝试")
                time.sleep(1)
                continue
            else:
                return None, "脉冲数过多"
      
        # 检查与首次记录的一致性
        if first_pulse_count is not None:
            deviation = abs(current_pulse_count - first_pulse_count) / first_pulse_count
            if deviation > 0.2:  # 偏差超过20%
                print(f"⚠️  脉冲数({current_pulse_count})与第一次记录({first_pulse_count})差异过大!")
                retry_count += 1
                if retry_count < max_retries:
                    print("请确保设置相同的空调参数")
                    time.sleep(1)
                    continue
                else:
                    return None, "脉冲数不一致"
      
        # 记录成功
        return raw_data, None
  
    return None, "达到最大重试次数"

def learn_ir_command(pin_num=23, params=None, num_recordings=6):
    """学习一个红外指令，记录6次"""
    print(f"\n开始学习指令: {params['description']}")
    if params['specification'] != "无":
        print(f"备注: {params['specification']}")
    print("=" * 40)
  
    receiver = IRReceiver(pin_num)
    recorded_data = []
    first_pulse_count = None
  
    for attempt in range(1, num_recordings + 1):
        # 记录单次信号，支持重试
        raw_data, error = record_single_signal(receiver, attempt, first_pulse_count)
      
        if raw_data:
            recorded_data.append(raw_data)
            if first_pulse_count is None:
                first_pulse_count = len(raw_data)
        else:
            print(f"\n❌ 第{attempt}次记录失败: {error}")
            abandon = input("是否放弃整个学习过程? (y/n) [默认n]: ").strip().lower()
            if abandon == 'y':
                return None
            else:
                # 跳过这次记录
                recorded_data.append(None)
      
        if attempt < num_recordings:
            print("\n准备下一次记录...")
            time.sleep(1)
  
    # 检查有效记录数
    valid_data = [data for data in recorded_data if data is not None]
  
    print(f"\n{params['description']} - 学习结果:")
    print("-" * 30)
    print(f"有效记录: {len(valid_data)}/{num_recordings}")
  
    if len(valid_data) < 3:
        print("❌ 有效记录太少(至少需要3次)，无法进行可靠解码")
        return None
  
    # 开始解码
    print("\n开始解码...")
    hex_result, error = decode_ir_data(valid_data)
  
    if hex_result:
        print(f"✓ 解码成功!")
        print(f"十六进制结果: {hex_result}")
        # 保存到文件
        save_to_csv(params, hex_result)
        return hex_result
    else:
        print(f"\n❌ 解码失败: {error}")
        return None

def main():
    """主程序"""
    print("空调IR遥控器学习和解码系统")
    print("=" * 50)
    print("提示: 请确保遥控器对准接收器")
    print("学习结果将保存在 result.txt 文件中")
  
    learned_count = 0
  
    while True:
        print(f"\n已成功学习指令: {learned_count}个")
      
        choice_options = ['y', 'n']
        choice_descriptions = ['是', '否']
        continue_learning = get_number_choice("是否学习新的空调指令?", choice_options, choice_descriptions)
      
        if continue_learning == 'n':
            break
      
        # 获取空调参数
        params = get_ac_parameters()
      
        print(f"\n准备学习: {params['description']}")
        if params['specification'] != "无":
            print(f"备注: {params['specification']}")
        
        confirm_options = ['y', 'n']
        confirm_descriptions = ['确认', '取消']
        confirm = get_number_choice("确认参数正确?", confirm_options, confirm_descriptions)
      
        if confirm == 'n':
            continue
      
        hex_result = learn_ir_command(23, params, 6)
      
        if hex_result:
            learned_count += 1
            print(f"\n✓ 指令学习并解码完成")
        else:
            print(f"\n指令学习失败")
            retry_options = ['y', 'n']
            retry_descriptions = ['重试', '跳过']
            retry = get_number_choice("是否重试?", retry_options, retry_descriptions)
          
            if retry == 'y':
                # 重新尝试相同参数
                hex_result = learn_ir_command(23, params, 6)
                if hex_result:
                    learned_count += 1
                    print(f"\n✓ 重试成功，指令学习完成")
  
    if learned_count > 0:
        print(f"\n学习完成! 共成功学习 {learned_count} 个指令")
        print("所有结果已保存在 result.txt 文件中")
    else:
        print("\n未学习任何指令")

if __name__ == "__main__":
    main()