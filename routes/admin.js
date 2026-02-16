const express = require("express");
const pool = require("../config/db");
const {
  requireAuth,
  generateTeacherCode,
  generateRollNumber
} = require("./helpers");

const router = express.Router();

router.get("/dashboard", requireAuth("admin"), async (req, res) => {
  try {
    const [[students]] = await pool.query(
      "SELECT COUNT(*) AS count FROM students"
    );
    const [[teachers]] = await pool.query(
      "SELECT COUNT(*) AS count FROM teachers"
    );
    const [[subjects]] = await pool.query(
      "SELECT COUNT(*) AS count FROM subjects"
    );
    const [[exams]] = await pool.query("SELECT COUNT(*) AS count FROM exams");
    const [[coursesCount]] = await pool.query(
      "SELECT COUNT(*) AS count FROM courses"
    );

    const [courses] = await pool.query(
      "SELECT id, name, code FROM courses ORDER BY name"
    );
    const [semesters] = await pool.query(
      "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
    );
    const [subjectsList] = await pool.query(
      "SELECT id, semester_id, name FROM subjects ORDER BY name"
    );

    const courseMap = new Map();
    courses.forEach((course) => {
      courseMap.set(course.id, { ...course, semesters: [] });
    });

    const semesterMap = new Map();
    semesters.forEach((semester) => {
      const target = courseMap.get(semester.course_id);
      if (target) {
        const item = { ...semester, subjects: [] };
        target.semesters.push(item);
        semesterMap.set(semester.id, item);
      }
    });

    subjectsList.forEach((subject) => {
      const target = semesterMap.get(subject.semester_id);
      if (target) {
        target.subjects.push(subject);
      }
    });

    const [recentStudents] = await pool.query(
      "SELECT name, roll_number FROM students ORDER BY id DESC LIMIT 5"
    );
    const [recentExams] = await pool.query(
      "SELECT e.id, s.name AS subject_name, e.exam_date FROM exams e JOIN subjects s ON e.subject_id = s.id ORDER BY e.exam_date DESC LIMIT 5"
    );
    const [passFail] = await pool.query(
      "SELECT status, COUNT(*) AS count FROM results GROUP BY status"
    );

    res.render("admin/dashboard", {
      title: "Admin Dashboard",
      stats: {
        students: students.count,
        teachers: teachers.count,
        subjects: subjects.count,
        exams: exams.count,
        courses: coursesCount.count
      },
      structure: Array.from(courseMap.values()),
      recentStudents,
      recentExams,
      pageLoading: true,
      passFail
    });
  } catch (error) {
    res.render("admin/dashboard", {
      title: "Admin Dashboard",
      stats: { students: 0, teachers: 0, subjects: 0, exams: 0, courses: 0 },
      structure: [],
      recentStudents: [],
      recentExams: [],
      pageLoading: true,
      passFail: []
    });
  }
});

router.get("/courses", requireAuth("admin"), async (req, res) => {
  const [courses] = await pool.query(
    "SELECT * FROM courses ORDER BY name"
  );
  res.render("admin/courses", { title: "Manage Courses", courses });
});

router.post("/courses", requireAuth("admin"), async (req, res) => {
  const { name, code } = req.body;
  await pool.query("INSERT INTO courses (name, code) VALUES (?, ?)", [
    name,
    code
  ]);
  res.redirect("/admin/courses");
});

router.post("/courses/:id/update", requireAuth("admin"), async (req, res) => {
  const { name, code } = req.body;
  await pool.query("UPDATE courses SET name = ?, code = ? WHERE id = ?", [
    name,
    code,
    req.params.id
  ]);
  res.redirect("/admin/courses");
});

router.post("/courses/:id/delete", requireAuth("admin"), async (req, res) => {
  await pool.query("DELETE FROM courses WHERE id = ?", [req.params.id]);
  res.redirect("/admin/courses");
});

router.get("/semesters", requireAuth("admin"), async (req, res) => {
  const [courses] = await pool.query(
    "SELECT id, name FROM courses ORDER BY name"
  );
  const [semesters] = await pool.query(
    "SELECT sem.id, sem.course_id, sem.semester_number, sem.title, c.name AS course_name " +
      "FROM semesters sem JOIN courses c ON sem.course_id = c.id " +
      "ORDER BY c.name, sem.semester_number"
  );
  const [subjects] = await pool.query(
    "SELECT s.id, s.semester_id, s.name FROM subjects s ORDER BY s.name"
  );

  res.render("admin/semesters", {
    title: "Manage Semesters",
    courses,
    semesters,
    subjects
  });
});

router.post("/semesters", requireAuth("admin"), async (req, res) => {
  const { course_id, semester_number, title, subjects } = req.body;
  const subjectList = (subjects || "")
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();
    const [result] = await connection.query(
      "INSERT INTO semesters (course_id, semester_number, title) VALUES (?, ?, ?)",
      [course_id, semester_number, title]
    );
    const semesterId = result.insertId;

    for (const name of subjectList) {
      await connection.query(
        "INSERT INTO subjects (semester_id, name) VALUES (?, ?)",
        [semesterId, name]
      );
    }

    await connection.commit();
    res.redirect("/admin/semesters");
  } catch (error) {
    await connection.rollback();
    res.redirect("/admin/semesters");
  } finally {
    connection.release();
  }
});

router.post(
  "/semesters/:id/update",
  requireAuth("admin"),
  async (req, res) => {
    const { semester_number, title } = req.body;
    await pool.query(
      "UPDATE semesters SET semester_number = ?, title = ? WHERE id = ?",
      [semester_number, title, req.params.id]
    );
    res.redirect("/admin/semesters");
  }
);

router.post(
  "/semesters/:id/delete",
  requireAuth("admin"),
  async (req, res) => {
    await pool.query("DELETE FROM semesters WHERE id = ?", [req.params.id]);
    res.redirect("/admin/semesters");
  }
);

router.get("/students", requireAuth("admin"), async (req, res) => {
  const [students] = await pool.query(
    "SELECT st.*, c.name AS course_name, sem.semester_number " +
      "FROM students st " +
      "JOIN courses c ON st.course_id = c.id " +
      "JOIN semesters sem ON st.semester_id = sem.id " +
      "ORDER BY st.id DESC"
  );
  const [courses] = await pool.query(
    "SELECT id, name FROM courses ORDER BY name"
  );
  const [semesters] = await pool.query(
    "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
  );

  res.render("admin/students", {
    title: "Manage Students",
    students,
    courses,
    semesters
  });
});

router.post("/students", requireAuth("admin"), async (req, res) => {
  const { name, email, password, course_id, semester_id } = req.body;
  const [[semesterRow]] = await pool.query(
    "SELECT semester_number, course_id FROM semesters WHERE id = ?",
    [semester_id]
  );

  if (!semesterRow || String(semesterRow.course_id) !== String(course_id)) {
    return res.redirect("/admin/students");
  }

  const rollNumber = await generateRollNumber(semesterRow.semester_number);
  await pool.query(
    "INSERT INTO students (roll_number, name, email, password, course_id, semester_id) VALUES (?, ?, ?, ?, ?, ?)",
    [rollNumber, name, email, password, course_id, semester_id]
  );
  res.redirect("/admin/students");
});

router.post("/students/:id/update", requireAuth("admin"), async (req, res) => {
  const { name, email, semester_id } = req.body;
  const [[semesterRow]] = await pool.query(
    "SELECT semester_number, course_id FROM semesters WHERE id = ?",
    [semester_id]
  );

  if (!semesterRow) {
    return res.redirect("/admin/students");
  }

  await pool.query(
    "UPDATE students SET name = ?, email = ?, semester_id = ?, course_id = ? WHERE id = ?",
    [name, email, semester_id, semesterRow.course_id, req.params.id]
  );
  res.redirect("/admin/students");
});

router.post("/students/:id/delete", requireAuth("admin"), async (req, res) => {
  await pool.query("DELETE FROM students WHERE id = ?", [req.params.id]);
  res.redirect("/admin/students");
});

router.get("/teachers", requireAuth("admin"), async (req, res) => {
  const [teachers] = await pool.query("SELECT * FROM teachers ORDER BY id DESC");
  res.render("admin/teachers", { title: "Manage Teachers", teachers });
});

router.post("/teachers", requireAuth("admin"), async (req, res) => {
  const { name, email, password, department, phone } = req.body;
  const teacherCode = await generateTeacherCode();
  await pool.query(
    "INSERT INTO teachers (teacher_code, name, email, password, department, phone) VALUES (?, ?, ?, ?, ?, ?)",
    [teacherCode, name, email, password, department, phone || null]
  );
  res.redirect("/admin/teachers");
});

router.post("/teachers/:id/update", requireAuth("admin"), async (req, res) => {
  const { name, email, department, phone } = req.body;
  await pool.query(
    "UPDATE teachers SET name = ?, email = ?, department = ?, phone = ? WHERE id = ?",
    [name, email, department, phone || null, req.params.id]
  );
  res.redirect("/admin/teachers");
});

router.post("/teachers/:id/delete", requireAuth("admin"), async (req, res) => {
  await pool.query("DELETE FROM teachers WHERE id = ?", [req.params.id]);
  res.redirect("/admin/teachers");
});

router.get("/subjects", requireAuth("admin"), async (req, res) => {
  const [subjects] = await pool.query(
    "SELECT s.id, s.name, sem.semester_number, c.name AS course_name " +
      "FROM subjects s " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "ORDER BY c.name, sem.semester_number, s.name"
  );
  res.render("admin/subjects", { title: "Subjects", subjects });
});

router.get("/assignments", requireAuth("admin"), async (req, res) => {
  const [teachers] = await pool.query(
    "SELECT id, name, teacher_code FROM teachers"
  );
  const [subjects] = await pool.query(
    "SELECT s.id, s.name, sem.semester_number, c.name AS course_name " +
      "FROM subjects s " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "ORDER BY c.name, sem.semester_number, s.name"
  );
  const [assignments] = await pool.query(
    "SELECT ts.id, t.name AS teacher_name, t.teacher_code, s.name AS subject_name, sem.semester_number, c.name AS course_name " +
      "FROM teacher_subjects ts " +
      "JOIN teachers t ON ts.teacher_id = t.id " +
      "JOIN subjects s ON ts.subject_id = s.id " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "ORDER BY ts.id DESC"
  );

  res.render("admin/assignments", {
    title: "Assign Teachers",
    teachers,
    subjects,
    assignments,
    error: req.query.error || null
  });
});

router.post("/assignments", requireAuth("admin"), async (req, res) => {
  const { teacher_id, subject_id } = req.body;
  const [[existing]] = await pool.query(
    "SELECT id FROM teacher_subjects WHERE subject_id = ?",
    [subject_id]
  );
  if (existing) {
    return res.redirect("/admin/assignments?error=Subject%20already%20assigned");
  }
  await pool.query(
    "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)",
    [teacher_id, subject_id]
  );
  res.redirect("/admin/assignments");
});

router.post("/assignments/:id/delete", requireAuth("admin"), async (req, res) => {
  await pool.query("DELETE FROM teacher_subjects WHERE id = ?", [req.params.id]);
  res.redirect("/admin/assignments");
});

router.get("/questions", requireAuth("admin"), async (req, res) => {
  const [questions] = await pool.query(
    "SELECT q.id, q.question_type, q.question_text, s.name AS subject_name, t.name AS teacher_name " +
      "FROM question_bank q " +
      "JOIN subjects s ON q.subject_id = s.id " +
      "JOIN teachers t ON q.teacher_id = t.id " +
      "ORDER BY q.id DESC"
  );
  res.render("admin/questions", {
    title: "Question Bank",
    questions
  });
});

router.get("/exams", requireAuth("admin"), async (req, res) => {
  const [exams] = await pool.query(
    "SELECT e.id, s.name AS subject_name, t.name AS teacher_name, e.exam_date, e.duration_minutes " +
      "FROM exams e " +
      "JOIN subjects s ON e.subject_id = s.id " +
      "JOIN teachers t ON e.teacher_id = t.id " +
      "ORDER BY e.exam_date DESC"
  );
  res.render("admin/exams", { title: "Monitor Exams", exams });
});

router.get("/results", requireAuth("admin"), async (req, res) => {
  const [results] = await pool.query(
    "SELECT r.id, st.name AS student_name, s.name AS subject_name, r.total_marks, r.percentage, r.status " +
      "FROM results r " +
      "JOIN students st ON r.student_id = st.id " +
      "JOIN subjects s ON r.subject_id = s.id " +
      "ORDER BY r.id DESC"
  );
  res.render("admin/results", { title: "Exam Results", results });
});

router.get("/analytics", requireAuth("admin"), async (req, res) => {
  const [passFail] = await pool.query(
    "SELECT status, COUNT(*) AS count FROM results GROUP BY status"
  );
  const [subjectPerf] = await pool.query(
    "SELECT s.name AS subject_name, AVG(r.percentage) AS avg_percent " +
      "FROM results r JOIN subjects s ON r.subject_id = s.id GROUP BY s.name"
  );

  res.render("admin/analytics", {
    title: "Analytics",
    passFail,
    subjectPerf
  });
});

module.exports = router;
