import os

# 创建文件名列表
filenames = []

# 添加27pwon_1到27pwon_6
for i in range(1, 7):
    filenames.append(f"27pwon_{i}.txt")

# 添加27pwoff_1到27pwoff_6
for i in range(1, 7):
    filenames.append(f"27pwoff_{i}.txt")

# 添加26pwon_1到26pwon_6
for i in range(1, 7):
    filenames.append(f"26pwon_{i}.txt")

# 添加26pwoff_1到26pwoff_6
for i in range(1, 7):
    filenames.append(f"26pwoff_{i}.txt")

# 创建所有文件
for filename in filenames:
    with open(filename, 'w') as f:
        pass  # 创建空文件

print(f"已成功创建{len(filenames)}个空文件")
