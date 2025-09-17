import sqlite3
import csv
import io
from flask import Flask, render_template, request, jsonify
from datetime import date

app = Flask(__name__)

DATABASE = 'attendance.db'

def get_db_connection():
    """创建一个数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """渲染主页面"""
    conn = get_db_connection()
    # 【重构】查询所有教学班级，并动态找出它们对应的真实年级
    classes = conn.execute("""
        SELECT
            tc.id,
            tc.name,
            -- 子查询：根据业务规则（同一教学班级内年级相同），
            -- 从该班级的学生中找到他们行政班级的年级。
            (SELECT ac.grade
             FROM classes ac
             JOIN student_class_memberships sm_admin ON ac.id = sm_admin.class_id
             JOIN student_class_memberships sm_teach ON sm_admin.student_id = sm_teach.student_id
             WHERE ac.type = '行政' AND sm_teach.class_id = tc.id
             LIMIT 1) AS grade
        FROM
            classes tc
        WHERE
            tc.type = '教学'
        ORDER BY
            grade, tc.name
    """).fetchall()
    conn.close()
    return render_template('index.html', classes=classes)

@app.route('/api/students/<int:class_id>')
def get_students(class_id):
    """【重构】根据班级ID获取学生列表，并附带今日考勤状态"""
    today_str = date.today().isoformat()
    conn = get_db_connection()
    
    # 【修改】使用 LEFT JOIN 查询学生及其今日的缺勤记录
    students = conn.execute("""
        SELECT
            s.id,
            s.name,
            -- 如果能在当天的考勤记录中找到该学生，则 is_absent_today 为 1 (true)，否则为 0 (false)
            CASE
                WHEN ar.id IS NOT NULL THEN 1
                ELSE 0
            END AS is_absent_today
        FROM
            students s
        JOIN
            student_class_memberships sm ON s.id = sm.student_id
        LEFT JOIN
            attendance_records ar ON s.id = ar.student_id AND ar.attendance_date = ?
        WHERE
            sm.class_id = ?
        ORDER BY
            s.name
    """, (today_str, class_id)).fetchall()
    
    conn.close()
    return jsonify([dict(student) for student in students])

@app.route('/api/attendance', methods=['POST'])
def submit_attendance():
    """【重构】以最新提交为准，更新考勤数据"""
    data = request.get_json()
    class_id = data.get('class_id') # 教学班级ID
    absent_student_ids = data.get('absent_ids', [])
    today_str = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 找出该教学班级下的所有学生ID
    students_in_class = cursor.execute(
        "SELECT student_id FROM student_class_memberships WHERE class_id = ?",
        (class_id,)
    ).fetchall()
    student_ids_in_class = [s['student_id'] for s in students_in_class]

    # 2. 删除这些学生今天所有的旧考勤记录
    if student_ids_in_class:
        # 构建占位符以安全地使用 IN 子句
        placeholders = ','.join('?' for _ in student_ids_in_class)
        params = student_ids_in_class + [today_str]
        cursor.execute(
            f"DELETE FROM attendance_records WHERE student_id IN ({placeholders}) AND attendance_date = ?",
            params
        )

    # 3. 插入本次提交的新的缺勤记录
    for student_id in absent_student_ids:
        cursor.execute(
            'INSERT INTO attendance_records (student_id, class_id, attendance_date, is_absent) VALUES (?, ?, ?, 1)',
            (student_id, class_id, today_str)
        )
            
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "考勤记录已更新"})

@app.route('/report')
def show_report():
    """【重构】专门用于生成和显示报告的页面"""
    today_str = date.today().isoformat()
    conn = get_db_connection()
    
    # 核心查询：获取今天所有缺勤学生，并 JOIN 查询出他们所在的行政班级信息
    absent_students_details = conn.execute("""
        SELECT
            s.name AS student_name,
            c.grade AS admin_grade,
            c.name AS admin_class_name
        FROM attendance_records ar
        JOIN students s ON ar.student_id = s.id
        JOIN student_class_memberships sm ON s.id = sm.student_id
        JOIN classes c ON sm.class_id = c.id
        WHERE ar.attendance_date = ? AND c.type = '行政'
    """, (today_str,)).fetchall()

    if not absent_students_details:
        final_report = "今日所有班级均无缺勤记录。"
    else:
        # 在内存中组织报告数据
        grades_report = {}  # 结构: { '年级': { '班级': [学生名, ...], ... }, ... }
        for row in absent_students_details:
            grade = row['admin_grade']
            class_name = row['admin_class_name']
            student_name = row['student_name']
            
            if grade not in grades_report:
                grades_report[grade] = {}
            if class_name not in grades_report[grade]:
                grades_report[grade][class_name] = []
            
            # 防止同一学生因加入多个教学班级而在报告中重复出现
            if student_name not in grades_report[grade][class_name]:
                grades_report[grade][class_name].append(student_name)

        # 格式化为最终的报告字符串
        report_lines = []
        # 按年级排序
        for grade in sorted(grades_report.keys()):
            report_lines.append(f"{grade}缺勤情况统计")
            # 按班级名排序
            for class_name in sorted(grades_report[grade].keys()):
                students = grades_report[grade][class_name]
                if not students: continue # 如果班级内没有缺勤学生，则跳过
                
                report_lines.append(f"班级：{class_name}")
                report_lines.append(f"缺勤人数：{len(students)}")
                report_lines.append(f"缺勤学生姓名：{'，'.join(students)}。")
                report_lines.append("")
        
        if not report_lines:
            final_report = "今日所有班级均无缺勤记录。"
        else:
            final_report = "\n".join(report_lines)

    conn.close()
    
    return render_template('report.html', report_data=final_report)


@app.route('/api/import_students', methods=['POST'])
def import_students():
    """【新增】处理上传的CSV文件并导入学生数据"""
    if 'student_file' not in request.files:
        return jsonify({"status": "error", "message": "没有找到文件部分"}), 400

    file = request.files['student_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "没有选择文件"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # 将文件内容读取为字符串并解码
            stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.reader(stream)
            
            header = next(csv_reader) # 跳过表头
            expected_header = ['年级', '班级', '姓名', '上课班级']
            if header != expected_header:
                return jsonify({"status": "error", "message": f"CSV文件表头不正确，应为: {','.join(expected_header)}"}), 400

            conn = get_db_connection()
            cursor = conn.cursor()
            
            imported_count = 0
            for row in csv_reader:
                grade, class_name, student_name, teaching_class_name = row

                # 1. 处理行政班级
                cursor.execute("SELECT id FROM classes WHERE grade = ? AND name = ? AND type = '行政'", (grade, class_name))
                admin_class = cursor.fetchone()
                if not admin_class:
                    cursor.execute("INSERT INTO classes (grade, name, type) VALUES (?, ?, '行政')", (grade, class_name))
                    admin_class_id = cursor.lastrowid
                else:
                    admin_class_id = admin_class['id']

                # 2. 处理学生
                unique_key = f"{grade}-{class_name}-{student_name}"
                cursor.execute("SELECT id FROM students WHERE unique_key = ?", (unique_key,))
                student = cursor.fetchone()
                if not student:
                    cursor.execute("INSERT INTO students (name, unique_key) VALUES (?, ?)", (student_name, unique_key))
                    student_id = cursor.lastrowid
                else:
                    student_id = student['id']

                # 3. 处理教学班级
                cursor.execute("SELECT id FROM classes WHERE name = ? AND type = '教学'", (teaching_class_name,))
                teaching_class = cursor.fetchone()
                if not teaching_class:
                    # 教学班级的 grade 设为 '通用'
                    cursor.execute("INSERT INTO classes (grade, name, type) VALUES ('通用', ?, '教学')", (teaching_class_name,))
                    teaching_class_id = cursor.lastrowid
                else:
                    teaching_class_id = teaching_class['id']

                # 4. 建立关系 (使用 INSERT OR IGNORE 避免重复导入时出错)
                # 关联学生与行政班级
                cursor.execute("INSERT OR IGNORE INTO student_class_memberships (student_id, class_id) VALUES (?, ?)", (student_id, admin_class_id))
                # 关联学生与教学班级
                cursor.execute("INSERT OR IGNORE INTO student_class_memberships (student_id, class_id) VALUES (?, ?)", (student_id, teaching_class_id))
                
                imported_count += 1

            conn.commit()
            conn.close()
            
            return jsonify({"status": "success", "message": f"成功导入 {imported_count} 条记录！页面即将刷新..."})

        except Exception as e:
            return jsonify({"status": "error", "message": f"处理文件时发生错误: {str(e)}"}), 500
    else:
        return jsonify({"status": "error", "message": "不支持的文件类型，请上传CSV文件"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5333, debug=True)
