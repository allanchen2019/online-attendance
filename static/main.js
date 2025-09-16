$(document).ready(function() {
    let currentClassId = null;

    // ... (选择班级和标记缺勤的代码保持不变) ...
    // 当用户选择一个班级时
    $('#class-select').on('change', function() {
        currentClassId = $(this).val();
        if (!currentClassId) return;

        $.get(`/api/students/${currentClassId}`, function(students) {
            const tableBody = $('#student-table-body');
            tableBody.empty(); 

            if (students.length === 0) {
                tableBody.append('<tr><td colspan="3" class="text-center">该班级下没有学生</td></tr>');
            } else {
                students.forEach((student, index) => {
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
            
            $('#student-section').removeClass('d-none');
        });
    });

    // 点击表格行来标记缺勤 (事件委托)
    $('#student-table-body').on('click', 'tr', function() {
        const row = $(this);
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
                // 【修改】提交成功后，直接跳转到报告页面
                alert('提交成功！现在将跳转到报告页面。');
                window.location.href = '/report';
            },
            error: function() {
                alert('提交失败，请稍后重试。');
            }
        });
    });
});