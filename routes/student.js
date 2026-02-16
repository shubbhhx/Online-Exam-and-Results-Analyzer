const express = require("express");
const pool = require("../config/db");
const { requireAuth } = require("./helpers");

const router = express.Router();

router.get("/dashboard", requireAuth("student"), async (req, res) => {
  const [[student]] = await pool.query(
    "SELECT st.*, c.name AS course_name, sem.semester_number, sem.title AS semester_title " +
      "FROM students st " +
      "JOIN courses c ON st.course_id = c.id " +
      "JOIN semesters sem ON st.semester_id = sem.id " +
      "WHERE st.id = ?",
    [req.session.user.id]
  );

  const [subjects] = await pool.query(
    "SELECT s.id, s.name, c.name AS course_name, sem.semester_number " +
      "FROM subjects s " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "WHERE s.semester_id = ? ORDER BY s.name",
    [student.semester_id]
  );

  const [exams] = await pool.query(
    "SELECT e.id, s.name AS subject_name, e.exam_date, e.duration_minutes, " +
      "CASE WHEN r.id IS NULL THEN 'Not Started' ELSE r.status END AS status, r.id AS result_id " +
      "FROM exams e " +
      "JOIN subjects s ON e.subject_id = s.id " +
      "LEFT JOIN results r ON r.exam_id = e.id AND r.student_id = ? " +
      "WHERE s.semester_id = ? ORDER BY e.exam_date DESC",
    [req.session.user.id, student.semester_id]
  );

  const [subjectPerf] = await pool.query(
    "SELECT s.name AS subject_name, r.percentage " +
      "FROM results r JOIN subjects s ON r.subject_id = s.id " +
      "WHERE r.student_id = ?",
    [req.session.user.id]
  );

  res.render("student/dashboard", {
    title: "Student Dashboard",
    student,
    subjects,
    exams,
    pageLoading: true,
    subjectPerf
  });
});

router.get("/exams/:examId/start", requireAuth("student"), async (req, res) => {
  const examId = req.params.examId;
  const [[exam]] = await pool.query(
    "SELECT e.*, s.name AS subject_name, s.semester_id FROM exams e JOIN subjects s ON e.subject_id = s.id WHERE e.id = ?",
    [examId]
  );

  if (!exam) {
    return res.redirect("/student/dashboard");
  }

  const [[student]] = await pool.query("SELECT * FROM students WHERE id = ?", [
    req.session.user.id
  ]);

  if (student.semester_id !== exam.semester_id) {
    return res.redirect("/student/dashboard");
  }

  const now = new Date();
  if (new Date(exam.exam_date) > now) {
    return res.redirect("/student/dashboard");
  }

  const [mcqs] = await pool.query(
    "SELECT * FROM question_bank WHERE subject_id = ? AND question_type = 'MCQ' ORDER BY RAND() LIMIT 23",
    [exam.subject_id]
  );
  const [descs] = await pool.query(
    "SELECT * FROM question_bank WHERE subject_id = ? AND question_type = 'DESCRIPTIVE' ORDER BY RAND() LIMIT 2",
    [exam.subject_id]
  );

  req.session.examQuestions = {
    examId: exam.id,
    mcqIds: mcqs.map((q) => q.id),
    descIds: descs.map((q) => q.id)
  };

  res.render("student/exam", {
    title: "Exam",
    exam,
    mcqs,
    descs
  });
});

router.post("/exams/:examId/submit", requireAuth("student"), async (req, res) => {
  const examId = parseInt(req.params.examId, 10);
  const studentId = req.session.user.id;

  if (!req.session.examQuestions || req.session.examQuestions.examId !== examId) {
    return res.redirect("/student/dashboard");
  }

  const mcqIds = req.session.examQuestions.mcqIds || [];
  const descIds = req.session.examQuestions.descIds || [];

  let totalMarks = 0;

  for (const id of mcqIds) {
    const answer = req.body[`mcq_${id}`];
    const [[question]] = await pool.query(
      "SELECT correct_option FROM question_bank WHERE id = ?",
      [id]
    );

    const isCorrect = question && answer === question.correct_option;
    const marks = isCorrect ? 1 : 0;
    totalMarks += marks;

    await pool.query(
      "INSERT INTO student_answers (exam_id, student_id, question_id, question_type, answer_text, marks_awarded, evaluated) VALUES (?, ?, ?, 'MCQ', ?, ?, 1)",
      [examId, studentId, id, answer || null, marks]
    );
  }

  for (const id of descIds) {
    const answer = req.body[`desc_${id}`];
    await pool.query(
      "INSERT INTO student_answers (exam_id, student_id, question_id, question_type, answer_text, marks_awarded, evaluated) VALUES (?, ?, ?, 'DESCRIPTIVE', ?, 0, 0)",
      [examId, studentId, id, answer || null]
    );
  }

  const [[exam]] = await pool.query("SELECT subject_id FROM exams WHERE id = ?", [
    examId
  ]);

  await pool.query(
    "INSERT INTO results (exam_id, student_id, subject_id, total_marks, percentage, status) VALUES (?, ?, ?, ?, ?, ?)",
    [
      examId,
      studentId,
      exam.subject_id,
      totalMarks,
      ((totalMarks / 25) * 100).toFixed(2),
      "Pending"
    ]
  );

  req.session.examQuestions = null;
  res.redirect("/student/history?toast=Exam%20submitted&type=success");
});

router.get("/history", requireAuth("student"), async (req, res) => {
  const [results] = await pool.query(
    "SELECT r.id, s.name AS subject_name, r.total_marks, r.percentage, r.status " +
      "FROM results r JOIN subjects s ON r.subject_id = s.id " +
      "WHERE r.student_id = ? ORDER BY r.id DESC",
    [req.session.user.id]
  );
  res.render("student/history", {
    title: "Exam History",
    results,
    toast: req.query.toast
      ? { type: req.query.type || "success", message: req.query.toast }
      : null
  });
});

router.get("/results/:id", requireAuth("student"), async (req, res) => {
  const [[result]] = await pool.query(
    "SELECT r.*, s.name AS subject_name FROM results r JOIN subjects s ON r.subject_id = s.id WHERE r.id = ? AND r.student_id = ?",
    [req.params.id, req.session.user.id]
  );

  if (!result) {
    return res.redirect("/student/history");
  }

  res.render("student/result", { title: "Result", result });
});

router.get("/analytics", requireAuth("student"), async (req, res) => {
  const [subjectPerf] = await pool.query(
    "SELECT s.name AS subject_name, r.percentage " +
      "FROM results r JOIN subjects s ON r.subject_id = s.id " +
      "WHERE r.student_id = ?",
    [req.session.user.id]
  );

  res.render("student/analytics", {
    title: "Performance Analytics",
    subjectPerf
  });
});

router.get("/profile", requireAuth("student"), async (req, res) => {
  const [[student]] = await pool.query(
    "SELECT st.*, c.name AS course_name, sem.semester_number, sem.title AS semester_title " +
      "FROM students st " +
      "JOIN courses c ON st.course_id = c.id " +
      "JOIN semesters sem ON st.semester_id = sem.id " +
      "WHERE st.id = ?",
    [req.session.user.id]
  );

  res.render("student/profile", {
    title: "Student Profile",
    student,
    toast: req.query.toast
      ? { type: req.query.type || "success", message: req.query.toast }
      : null
  });
});

router.post("/profile", requireAuth("student"), async (req, res) => {
  const { name, email, address, phone } = req.body;
  await pool.query(
    "UPDATE students SET name = ?, email = ?, address = ?, phone = ? WHERE id = ?",
    [name, email, address || null, phone || null, req.session.user.id]
  );
  res.redirect("/student/profile?toast=Profile%20updated&type=success");
});

module.exports = router;
