import sqlite3
from flask import Flask, render_template, request, jsonify
from datetime import date

app = Flask(__name__)

DATABASE = 'attendance.db'

def get_db_connection():
    """创建一个数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # 让查询结果可以像字典一样访问列
    return conn

@app.route('/')
def index():
    """渲染主页面"""
    conn = get_db_connection()
    classes = conn.execute('SELECT * FROM classes ORDER BY grade, name').fetchall()
    conn.close()
    return render_template('index.html', classes=classes)

@app.route('/api/students/<int:class_id>')
def get_students(class_id):
    """根据班级ID获取学生列表API"""
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students WHERE class_id = ? ORDER BY name', (class_id,)).fetchall()
    conn.close()
    # 将查询结果转换为字典列表
    return jsonify([dict(student) for student in students])

@app.route('/api/attendance', methods=['POST'])
def submit_attendance():
    """接收考勤提交并生成报告的API"""
    data = request.get_json()
    class_id = data.get('class_id')
    absent_student_ids = data.get('absent_ids', [])
    today_str = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 将当天的缺勤记录写入数据库
    for student_id in absent_student_ids:
        cursor.execute(
            'INSERT INTO attendance_records (student_id, class_id, attendance_date, is_absent) VALUES (?, ?, ?, 1)',
            (student_id, class_id, today_str)
        )
    conn.commit()
    
    # --- 生成当天的缺勤报告 ---
    report_lines = []
    # 查询所有有缺勤记录的年级
    grades = conn.execute(
        'SELECT DISTINCT c.grade FROM classes c JOIN attendance_records ar ON c.id = ar.class_id WHERE ar.attendance_date = ?',
        (today_str,)
    ).fetchall()

    for grade in grades:
        grade_name = grade['grade']
        report_lines.append(f"{grade_name}缺勤情况统计")
        
        # 查询该年级下所有有缺勤记录的班级
        classes_in_grade = conn.execute(
            'SELECT DISTINCT c.id, c.name FROM classes c JOIN attendance_records ar ON c.id = ar.class_id WHERE ar.attendance_date = ? AND c.grade = ?',
            (today_str, grade_name)
        ).fetchall()

        for cls in classes_in_grade:
            report_lines.append(f"班级：{cls['name']}")
            
            # 查询该班级当天的缺勤学生
            absent_students = conn.execute(
                """
                SELECT s.name FROM students s
                JOIN attendance_records ar ON s.id = ar.student_id
                WHERE ar.attendance_date = ? AND ar.class_id = ?
                """,
                (today_str, cls['id'])
            ).fetchall()
            
            absent_count = len(absent_students)
            absent_names = "，".join([s['name'] for s in absent_students])
            
            report_lines.append(f"缺勤人数：{absent_count}")
            report_lines.append(f"缺勤学生姓名：{absent_names}。")
            report_lines.append("") # 添加空行

    conn.close()
    
    final_report = "\n".join(report_lines)
    return jsonify({"report": final_report})


if __name__ == '__main__':
    app.run(debug=True) # debug=True模式可以在修改代码后自动重启服务