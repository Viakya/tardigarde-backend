"""Example Swagger spec block for future Attendance module routes.

Use this style in the attendance route file with inline docs or @swag_from.

---
tags:
  - Attendance
summary: Mark attendance for a student
description: Records attendance for a student in a batch by a teacher.
security:
  - BearerAuth: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      $ref: '#/definitions/AttendanceCreateExample'
responses:
  201:
    description: Attendance marked successfully
    schema:
      $ref: '#/definitions/StandardResponse'
  400:
    description: Validation error
    schema:
      $ref: '#/definitions/StandardResponse'
  401:
    description: Unauthorized
    schema:
      $ref: '#/definitions/StandardResponse'
"""
