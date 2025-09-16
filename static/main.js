$(document).ready(function() {
    let currentClassId = null;

    // 当用户选择一个班级时
    $('#class-select').on('change', function() {
        currentClassId = $(this).val();
        if (!currentClassId) return;

        // 通过API获取该班级的学生
        $.get(`/api/students/${currentClassId}`, function(students) {
            const tableBody = $('#student-table-body');
            tableBody.empty(); // 清空旧的名单

            if (students.length === 0) {
                tableBody.append('<tr><td colspan="3" class="text-center">该班级下没有学生</td></tr>');
            } else {
                students.forEach((student, index) => {
                    // 创建每一行
                    const row = `
                        <tr data-student-id="${student.id}" style="cursor: pointer;">
                            <th scope="row">${index + 1}</th>
                            <td>${student.name}</td>
                            <td>✔️ 出勤</td>
                        </tr>
                    `;
                    tableBody.append(row);
                });
            }
            
            $('#student-section').removeClass('d-none'); // 显示学生表格和提交按钮
            $('#report-section').addClass('d-none'); // 隐藏旧报告
        });
    });

    // 点击表格行来标记缺勤 (事件委托)
    $('#student-table-body').on('click', 'tr', function() {
        const row = $(this);
        // 切换CSS类和状态文本
        row.toggleClass('absent-row');
        if (row.hasClass('absent-row')) {
            row.find('td:last').text('❌ 缺勤');
        } else {
            row.find('td:last').text('✔️ 出勤');
        }
    });

    // 点击提交按钮时
    $('#submit-attendance').on('click', function() {
        const absentStudentRows = $('#student-table-body tr.absent-row');
        const absent_ids = [];

        absentStudentRows.each(function() {
            absent_ids.push($(this).data('student-id'));
        });

        // 构造要发送的数据
        const payload = {
            class_id: currentClassId,
            absent_ids: absent_ids
        };

        // 发送POST请求到后端API
        $.ajax({
            url: '/api/attendance',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            success: function(response) {
                // 成功后，显示报告
                $('#report-output').text(response.report || "今日所有班级均无缺勤记录。");
                $('#report-section').removeClass('d-none');
                alert('提交成功！');
            },
            error: function() {
                alert('提交失败，请稍后重试。');
            }
        });
    });
});