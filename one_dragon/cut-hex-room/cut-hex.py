import pandas as pd
import os

# 获取当前文件夹中的所有 CSV 文件
csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

if not csv_files:
    print("当前文件夹中没有找到 CSV 文件！")
else:
    # 假设只处理第一个找到的 CSV 文件，如果有多个可以调整逻辑
    input_file = csv_files[0]
    print(f"找到 CSV 文件：{input_file}，开始处理...")

    # 读取 CSV 文件
    df = pd.read_csv(input_file)

    # 创建一个函数来拆分 hex_code 为单独的字节
    def split_hex_code(hex_str):
        # 去掉可能的空格并确保是字符串
        hex_str = str(hex_str).strip()
        # 每两个字符分割为一个字节
        return [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]

    # 获取 hex_code 列的所有字节数（取最长的 hex_code 长度）
    max_bytes = max(df['hex_code'].apply(lambda x: len(str(x).strip()) // 2))

    # 创建新的列名，如 Byte0, Byte1, Byte2...
    byte_columns = [f'Byte{i}' for i in range(max_bytes)]

    # 将 hex_code 拆分成多个列
    split_hex = df['hex_code'].apply(split_hex_code)
    hex_df = pd.DataFrame(split_hex.tolist(), columns=byte_columns, index=df.index)

    # 将拆分后的字节列与原数据合并
    result_df = pd.concat([df, hex_df], axis=1)

    # 保存到新的 CSV 文件
    output_file = 'output_' + input_file
    result_df.to_csv(output_file, index=False)

    print(f"处理完成，结果已保存到 {output_file}")
