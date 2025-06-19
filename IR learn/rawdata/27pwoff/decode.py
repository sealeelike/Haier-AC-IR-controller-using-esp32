import os
import pandas as pd
import sys
from contextlib import redirect_stdout

def read_data_from_txt(directory='.'):
    """
    从指定目录读取所有.txt文件到字典中。
    键是无扩展名的文件名，值是数据。
    """
    print("--- 步骤 1: 读取 .txt 文件 ---")
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"警告: 在目录 '{os.path.abspath(directory)}' 中未找到 .txt 文件。")
        return {}

    data_dict = {}
    for file_name in txt_files:
        list_name = file_name.replace('.txt', '')
        file_path = os.path.join(directory, file_name)
        try:
            # 读取以逗号分隔的文件
            data = pd.read_csv(file_path, header=None, delimiter=',')
            
            # 将单行或单列数据转换为扁平列表
            if data.shape[0] == 1:
                data_dict[list_name] = data.iloc[0].tolist()
            else:
                data_dict[list_name] = data.values.flatten().tolist()
            print(f"成功读取文件: {file_name}")

        except Exception as e:
            print(f"读取文件 {file_name} 时出错: {e}")
            
    return data_dict

def unpack_and_filter_data(data_dict):
    """
    处理原始数据列表：移除前4个元素，并从剩余部分中选择偶数位置的元素。
    """
    print("\n--- 步骤 2: 解包和过滤数据 ---")
    unpack_dict = {}
    for name, data in data_dict.items():
        if not isinstance(data, list):
            data = data.tolist()
        
        # 裁剪前四个元素
        if len(data) > 4:
            trimmed_data = data[4:]
            
            # 提取偶数位置的元素 (索引 1, 3, 5, ...)
            even_position_elements = trimmed_data[1::2]
            
            unpack_name = "unpack_" + name
            unpack_dict[unpack_name] = even_position_elements
            print(f"已处理 '{name}', 创建了 '{unpack_name}'，包含 {len(even_position_elements)} 个元素。")
        else:
            print(f"警告: 列表 '{name}' 的元素少于或等于4个，已跳过。")
            
    return unpack_dict

def convert_to_binary_string(unpack_dict):
    """
    根据数值范围将数字列表转换为二进制字符串。
    400-700 -> 0, 1500-1900 -> 1, 其他 -> ?
    """
    print("\n--- 步骤 3: 将数据转换为二进制表示 ---")
    converted_dict = {}
    for name, data in unpack_dict.items():
        converted_list = []
        for value in data:
            try:
                num_value = float(value)
                if 400 <= num_value <= 700:
                    converted_list.append(0)
                elif 1500 <= num_value <= 1900:
                    converted_list.append(1)
                else:
                    converted_list.append("?")
            except (ValueError, TypeError):
                converted_list.append("?")
        
        converted_dict[name] = converted_list
        binary_string = ''.join(str(item) for item in converted_list)
        print(f"{name}: {binary_string}")
        
    return converted_dict

def get_consensus_string(converted_dict):
    """
    按位置比较所有二进制列表，以生成一个共识字符串。
    每个位置选择出现频率最高的值（0或1）。
    """
    print("\n--- 步骤 4: 生成共识字符串 ---")
    if not converted_dict:
        print("因为没有要处理的数据，无法生成共识字符串。")
        return ""
        
    all_data_lists = list(converted_dict.values())
    max_length = max(len(lst) for lst in all_data_lists) if all_data_lists else 0
    
    consensus = []
    for i in range(max_length):
        position_values = []
        for lst in all_data_lists:
            if i < len(lst) and str(lst[i]) in ['0', '1']:
                position_values.append(str(lst[i]))
        
        if not position_values:
            consensus.append("?")
            continue
            
        count_0 = position_values.count('0')
        count_1 = position_values.count('1')
        
        if count_0 > count_1:
            consensus.append('0')
        elif count_1 > count_0:
            consensus.append('1')
        else:
            consensus.append('?') # 如果数量相等，则使用 '?'
            print(f"警告: 在位置 {i}，'0' 和 '1' 的数量相等。使用 '?'。")
            
    return ''.join(consensus)

def format_number_with_separators(number_str, group_size, separator=' '):
    """为数字字符串添加分隔符以提高可读性。"""
    reversed_str = number_str[::-1]
    separated = separator.join(reversed_str[i:i+group_size] for i in range(0, len(reversed_str), group_size))
    return separated[::-1]

def perform_final_conversion(binary_string):
    """
    将最终的二进制字符串转换为十进制和十六进制格式。
    """
    print("\n--- 步骤 5: 最终转换和输出 ---")
    
    print(f"最终共识二进制字符串: {binary_string}")
    print(f"共识字符串中的总位数: {len(binary_string)}")
    
    clean_binary = ''.join(c for c in binary_string if c in '01')
    
    if not clean_binary:
        print("十进制结果: 没有有效的二进制数据可供转换。")
        print("十六进制结果: 没有有效的二进制数据可供转换。")
        return

    try:
        decimal_value = int(clean_binary, 2)
        hex_value = hex(decimal_value)[2:].upper()
        
        # 格式化以便于阅读
        decimal_formatted = format_number_with_separators(str(decimal_value), 3, ',')
        hex_formatted = format_number_with_separators(hex_value, 4, ' ')
        
        print(f"十进制结果: {decimal_formatted}")
        print(f"十六进制结果: {hex_formatted}")

    except ValueError:
        print("十进制结果: 转换期间出错。")
        print("十六进制结果: 转换期间出错。")

def main():
    """
    运行整个数据处理流程的主函数。
    """
    data_dict = read_data_from_txt('.')
    if not data_dict:
        print("\n流程已停止: 未读取到任何数据。")
        return

    unpack_dict = unpack_and_filter_data(data_dict)
    if not unpack_dict:
        print("\n流程已停止: 解包后无可用数据。")
        return

    converted_dict = convert_to_binary_string(unpack_dict)
    if not converted_dict:
        print("\n流程已停止: 转换后无可用数据。")
        return

    consensus_result = get_consensus_string(converted_dict)

    perform_final_conversion(consensus_result)


if __name__ == "__main__":
    # 将所有 print 输出重定向到 result.txt 文件
    with open('result.txt', 'w', encoding='utf-8') as f:
        with redirect_stdout(f):
            print("--- 开始处理 ---")
            main()
            print("\n--- 处理完成 ---")

