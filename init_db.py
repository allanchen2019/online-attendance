import sqlite3

# 连接到数据库（如果文件不存在，会自动创建）
connection = sqlite3.connect('attendance.db')
cursor = connection.cursor()

print("正在初始化数据库...")

# --- 创建数据表 ---
# 如果表已存在，先删除，以便重新创建
cursor.execute("DROP TABLE IF EXISTS students")
cursor.execute("DROP TABLE IF EXISTS classes")
cursor.execute("DROP TABLE IF EXISTS attendance_records")

# 创建班级表
cursor.execute("""
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grade TEXT NOT NULL,
    name TEXT NOT NULL UNIQUE
);
""")

# 创建学生表
cursor.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_id INTEGER NOT NULL,
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
""")

# 创建考勤记录表
cursor.execute("""
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    is_absent INTEGER NOT NULL DEFAULT 1, -- 1表示缺勤
    FOREIGN KEY (student_id) REFERENCES students (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);
""")

print("数据表创建成功。")

# --- 插入样本数据 ---
classes_to_add = [
    ('六年级', '六1班'),
    ('六年级', '六2班'),
    ('七年级', '七3班')
]
cursor.executemany("INSERT INTO classes (grade, name) VALUES (?, ?)", classes_to_add)

students_to_add = [
    # 六1班学生 (class_id = 1)
    ('王少钦', 1), ('颜圣容', 1), ('武琳琅', 1), ('李思明', 1), ('陈一凡', 1),
    # 六2班学生 (class_id = 2)
    ('赵宇航', 2), ('孙晓梅', 2), ('周子轩', 2),
    # 七3班学生 (class_id = 3)
    ('吴伟', 3), ('郑秀英', 3), ('冯静', 3)
]
cursor.executemany("INSERT INTO students (name, class_id) VALUES (?, ?)", students_to_add)

print("样本数据插入成功。")

# 提交更改并关闭连接
connection.commit()
connection.close()

print("数据库初始化完成！")