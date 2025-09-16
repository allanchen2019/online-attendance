import sqlite3

# 连接到数据库（如果文件不存在，会自动创建）
connection = sqlite3.connect('attendance.db')
cursor = connection.cursor()

print("正在初始化数据库...")

# --- 1. 删除旧表 ---
# 为了确保从一个干净的状态开始，我们先删除所有可能存在的旧表
cursor.execute("DROP TABLE IF EXISTS student_class_memberships")
cursor.execute("DROP TABLE IF EXISTS students")
cursor.execute("DROP TABLE IF EXISTS classes")
cursor.execute("DROP TABLE IF EXISTS attendance_records")

# --- 2. 创建新表结构 ---

# 创建班级表 (classes)
# 新增了 type 字段来区分 '行政班级' 和 '教学班级' (上课班级)
# 使用组合唯一键确保不会有重复的班级
cursor.execute("""
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('行政', '教学')),
    UNIQUE(grade, name, type)
);
""")

# 创建学生表 (students)
# 移除了 class_id，学生不再固定属于某个班级
# 新增了 unique_key 来通过 "行政班级ID-姓名" 的方式保证学生的唯一性
cursor.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unique_key TEXT NOT NULL UNIQUE
);
""")

# 创建学生与班级的关系表 (student_class_memberships)
# 这是一个全新的表，用于建立学生和班级之间的多对多关系
cursor.execute("""
CREATE TABLE student_class_memberships (
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    PRIMARY KEY (student_id, class_id),
    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
""")

# 创建考勤记录表 (attendance_records)
# 结构保持不变，但业务上 class_id 将指向一个'教学'类型的班级
cursor.execute("""
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    is_absent INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
""")

print("新数据表结构创建成功。")

# --- 3. 插入新的样本数据 ---

try:
    # 插入行政班级
    admin_classes = [
        ('六年级', '六1班', '行政'),
        ('六年级', '六2班', '行政'),
        ('七年级', '七3班', '行政')
    ]
    cursor.executemany("INSERT INTO classes (grade, name, type) VALUES (?, ?, ?)", admin_classes)
    print("样本[行政班级]已插入。")

    # 插入教学班级 (上课班级/教室)
    teaching_classes = [
        ('通用', '101教室', '教学'),
        ('通用', '102教室', '教学')
    ]
    cursor.executemany("INSERT INTO classes (grade, name, type) VALUES (?, ?, ?)", teaching_classes)
    print("样本[教学班级]已插入。")

    # 插入学生
    # unique_key = f"{admin_class_grade}-{admin_class_name}-{student_name}"
    students_to_add = [
        ('王少钦', '六年级-六1班-王少钦'),
        ('颜圣容', '六年级-六1班-颜圣容'),
        ('武琳琅', '六年级-六1班-武琳琅'),
        ('赵宇航', '六年级-六2班-赵宇航'),
        ('吴伟', '七年级-七3班-吴伟')
    ]
    cursor.executemany("INSERT INTO students (name, unique_key) VALUES (?, ?)", students_to_add)
    print("样本[学生]已插入。")

    # 建立学生与班级的关系
    # 查询ID以便建立关系
    # 六1班(行政) id=1, 六2班 id=2, 七3班 id=3
    # 101教室(教学) id=4, 102教室 id=5
    # 王少钦 id=1, 颜圣容 id=2, 武琳琅 id=3, 赵宇航 id=4, 吴伟 id=5
    memberships = [
        # 行政班级关系
        (1, 1), (2, 1), (3, 1), # 六1班的3个学生
        (4, 2), # 六2班的1个学生
        (5, 3), # 七3班的1个学生
        # 教学班级关系
        (1, 4), (2, 4), # 王少钦, 颜圣容 在 101教室
        (4, 4), # 赵宇航 也在 101教室
        (3, 5), (5, 5)  # 武琳琅, 吴伟 在 102教室
    ]
    cursor.executemany("INSERT INTO student_class_memberships (student_id, class_id) VALUES (?, ?)", memberships)
    print("样本[学生-班级关系]已建立。")

except sqlite3.IntegrityError as e:
    print(f"插入样本数据时发生错误 (可能是重复运行脚本): {e}")


# 提交更改并关闭连接
connection.commit()
connection.close()

print("数据库初始化完成！")
