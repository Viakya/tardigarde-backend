def test_student_cannot_access_admin(client, student_token):
    res = client.get("/api/v1/admin/tables", headers=student_token)
    assert res.status_code == 403

def test_parent_cannot_mark_attendance(client, parent_token):
    res = client.post("/api/v1/attendance", headers=parent_token, json={})
    assert res.status_code == 403

def test_teacher_access_allowed(client, teacher_token):
    res = client.get("/api/v1/students", headers=teacher_token)
    assert res.status_code == 200