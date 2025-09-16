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
                    const isAbsent = student.is_absent_today === 1;
                    const rowClass = isAbsent ? 'absent-row' : '';
                    const statusText = isAbsent ? '❌ 缺勤' : '✔️ 出勤';

                    const row = `
                        <tr data-student-id="${student.id}" style="cursor: pointer;" class="${rowClass}">
                            <th scope="row">${index + 1}</th>
                            <td>${student.name}</td>
                            <td>${statusText}</td>
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
                // 【修改】提交成功后，只显示提示信息
                alert('考勤记录提交成功！');
                // 刷新页面或重置表单，以便进行下一次点名
                location.reload();
            },
            error: function() {
                alert('提交失败，请稍后重试。');
            }
        });
    });

    // 处理文件上传表单
    $('#import-form').on('submit', function(e) {
        e.preventDefault(); // 阻止表单默认提交

        const fileInput = $('#student-file')[0];
        if (fileInput.files.length === 0) {
            alert('请先选择一个CSV文件。');
            return;
        }

        const formData = new FormData();
        formData.append('student_file', fileInput.files[0]);

        const statusDiv = $('#import-status');
        statusDiv.text('正在上传并处理...').removeClass('text-danger text-success');

        $.ajax({
            url: '/api/import_students',
            type: 'POST',
            data: formData,
            processData: false, // 告诉jQuery不要处理数据
            contentType: false, // 告诉jQuery不要设置contentType
            success: function(response) {
                statusDiv.text(response.message).addClass('text-success');
                // 导入成功后刷新页面，以更新班级下拉列表
                setTimeout(function() {
                    location.reload();
                }, 2000);
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.message : '导入失败，请检查文件格式或联系管理员。';
                statusDiv.text(errorMsg).addClass('text-danger');
            }
        });
    });
});
