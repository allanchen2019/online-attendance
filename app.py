import sqlite3
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
    classes = conn.execute('SELECT * FROM classes ORDER BY grade, name').fetchall()
    conn.close()
    return render_template('index.html', classes=classes)

@app.route('/api/students/<int:class_id>')
def get_students(class_id):
    """根据班级ID获取学生列表API"""
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students WHERE class_id = ? ORDER BY name', (class_id,)).fetchall()
    conn.close()
    return jsonify([dict(student) for student in students])

@app.route('/api/attendance', methods=['POST'])
def submit_attendance():
    """【修改】只负责接收和保存考勤数据"""
    data = request.get_json()
    class_id = data.get('class_id')
    absent_student_ids = data.get('absent_ids', [])
    today_str = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # 将当天的缺勤记录写入数据库
    for student_id in absent_student_ids:
        # 为防止重复提交，可以先检查是否存在
        existing_record = cursor.execute(
            'SELECT id FROM attendance_records WHERE student_id = ? AND attendance_date = ?',
            (student_id, today_str)
        ).fetchone()
        
        if not existing_record:
            cursor.execute(
                'INSERT INTO attendance_records (student_id, class_id, attendance_date, is_absent) VALUES (?, ?, ?, 1)',
                (student_id, class_id, today_str)
            )
            
    conn.commit()
    conn.close()
    
    # 【修改】不再生成报告，只返回成功状态
    return jsonify({"status": "success", "message": "考勤记录已保存"})

@app.route('/report')
def show_report():
    """【新增】专门用于生成和显示报告的页面"""
    today_str = date.today().isoformat()
    conn = get_db_connection()
    
    report_lines = []
    # 查询所有有缺勤记录的年级
    grades = conn.execute(
        'SELECT DISTINCT c.grade FROM classes c JOIN attendance_records ar ON c.id = ar.class_id WHERE ar.attendance_date = ? ORDER BY c.grade',
        (today_str,)
    ).fetchall()

    if not grades:
        final_report = "今日所有班级均无缺勤记录。"
    else:
        for grade in grades:
            grade_name = grade['grade']
            report_lines.append(f"{grade_name}缺勤情况统计")
            
            # 查询该年级下所有有缺勤记录的班级
            classes_in_grade = conn.execute(
                'SELECT DISTINCT c.id, c.name FROM classes c JOIN attendance_records ar ON c.id = ar.class_id WHERE ar.attendance_date = ? AND c.grade = ? ORDER BY c.name',
                (today_str, grade_name)
            ).fetchall()

            for cls in classes_in_grade:
                report_lines.append(f"班级：{cls['name']}")
                
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
                report_lines.append("")

        final_report = "\n".join(report_lines)

    conn.close()
    
    return render_template('report.html', report_data=final_report)


if __name__ == '__main__':
    app.run(debug=True)