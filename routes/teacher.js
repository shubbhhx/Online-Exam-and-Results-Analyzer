const express = require("express");
const pool = require("../config/db");
const { requireAuth } = require("./helpers");

const router = express.Router();

router.get("/dashboard", requireAuth("teacher"), async (req, res) => {
  const [subjects] = await pool.query(
    "SELECT s.id, s.name, c.name AS course_name, sem.semester_number, " +
      "COALESCE(SUM(CASE WHEN q.question_type = 'MCQ' THEN 1 END), 0) AS mcq_count, " +
      "COALESCE(SUM(CASE WHEN q.question_type = 'DESCRIPTIVE' THEN 1 END), 0) AS desc_count " +
      "FROM teacher_subjects ts " +
      "JOIN subjects s ON ts.subject_id = s.id " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "LEFT JOIN question_bank q ON q.subject_id = s.id AND q.teacher_id = ts.teacher_id " +
      "WHERE ts.teacher_id = ? " +
      "GROUP BY s.id, s.name, c.name, sem.semester_number " +
      "ORDER BY s.name",
    [req.session.user.id]
  );
  const [[pending]] = await pool.query(
    "SELECT COUNT(*) AS count FROM student_answers sa " +
      "JOIN exams e ON sa.exam_id = e.id " +
      "WHERE sa.question_type = 'DESCRIPTIVE' AND sa.evaluated = 0 AND e.teacher_id = ?",
    [req.session.user.id]
  );
  res.render("teacher/dashboard", {
    title: "Teacher Dashboard",
    subjects,
    pendingEvaluations: pending.count,
    pageLoading: true
  });
});

router.get("/subjects", requireAuth("teacher"), async (req, res) => {
  const [subjects] = await pool.query(
    "SELECT s.id, s.name, c.name AS course_name, sem.semester_number " +
      "FROM teacher_subjects ts " +
      "JOIN subjects s ON ts.subject_id = s.id " +
      "JOIN semesters sem ON s.semester_id = sem.id " +
      "JOIN courses c ON sem.course_id = c.id " +
      "WHERE ts.teacher_id = ?",
    [req.session.user.id]
  );
  res.render("teacher/subjects", { title: "Assigned Subjects", subjects });
});

router.get("/questions", requireAuth("teacher"), async (req, res) => {
  const [subjects] = await pool.query(
    "SELECT s.id, s.name " +
      "FROM teacher_subjects ts JOIN subjects s ON ts.subject_id = s.id " +
      "WHERE ts.teacher_id = ?",
    [req.session.user.id]
  );

  const [questions] = await pool.query(
    "SELECT q.*, s.name AS subject_name " +
      "FROM question_bank q JOIN subjects s ON q.subject_id = s.id " +
      "WHERE q.teacher_id = ? ORDER BY q.id DESC",
    [req.session.user.id]
  );

  res.render("teacher/questions", {
    title: "Question Bank",
    subjects,
    questions,
    error: req.query.error || null
  });
});

router.get("/questions/:id/edit", requireAuth("teacher"), async (req, res) => {
  const [[question]] = await pool.query(
    "SELECT q.*, s.name AS subject_name FROM question_bank q JOIN subjects s ON q.subject_id = s.id WHERE q.id = ? AND q.teacher_id = ?",
    [req.params.id, req.session.user.id]
  );

  if (!question) {
    return res.redirect("/teacher/questions");
  }

  res.render("teacher/question_edit", {
    title: "Edit Question",
    question
  });
});

router.post("/questions", requireAuth("teacher"), async (req, res) => {
  const {
    subject_id,
    question_type,
    question_text,
    option_a,
    option_b,
    option_c,
    option_d,
    correct_option
  } = req.body;

  const [counts] = await pool.query(
    "SELECT question_type, COUNT(*) AS count FROM question_bank WHERE subject_id = ? GROUP BY question_type",
    [subject_id]
  );

  const mcqCount = counts.find((row) => row.question_type === "MCQ")?.count || 0;
  const descCount =
    counts.find((row) => row.question_type === "DESCRIPTIVE")?.count || 0;

  if (question_type === "MCQ" && mcqCount >= 40) {
    return res.redirect("/teacher/questions?error=MCQ%20limit%20reached");
  }

  if (question_type === "DESCRIPTIVE" && descCount >= 10) {
    return res.redirect("/teacher/questions?error=Descriptive%20limit%20reached");
  }

  await pool.query(
    "INSERT INTO question_bank (subject_id, teacher_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    [
      subject_id,
      req.session.user.id,
      question_type,
      question_text,
      option_a || null,
      option_b || null,
      option_c || null,
      option_d || null,
      correct_option || null
    ]
  );

  res.redirect("/teacher/questions");
});

router.post("/questions/:id/update", requireAuth("teacher"), async (req, res) => {
  const {
    question_text,
    option_a,
    option_b,
    option_c,
    option_d,
    correct_option
  } = req.body;

  await pool.query(
    "UPDATE question_bank SET question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ? WHERE id = ? AND teacher_id = ?",
    [
      question_text,
      option_a || null,
      option_b || null,
      option_c || null,
      option_d || null,
      correct_option || null,
      req.params.id,
      req.session.user.id
    ]
  );

  res.redirect("/teacher/questions");
});

router.post("/questions/:id/delete", requireAuth("teacher"), async (req, res) => {
  await pool.query(
    "DELETE FROM question_bank WHERE id = ? AND teacher_id = ?",
    [req.params.id, req.session.user.id]
  );
  res.redirect("/teacher/questions");
});

router.get("/schedule", requireAuth("teacher"), async (req, res) => {
  const [subjects] = await pool.query(
    "SELECT s.id, s.name " +
      "FROM teacher_subjects ts JOIN subjects s ON ts.subject_id = s.id " +
      "WHERE ts.teacher_id = ?",
    [req.session.user.id]
  );

  const [exams] = await pool.query(
    "SELECT e.id, s.name AS subject_name, e.exam_date, e.duration_minutes " +
      "FROM exams e JOIN subjects s ON e.subject_id = s.id " +
      "WHERE e.teacher_id = ? ORDER BY e.exam_date DESC",
    [req.session.user.id]
  );

  res.render("teacher/schedule", {
    title: "Schedule Exams",
    subjects,
    exams,
    error: req.query.error || null
  });
});

router.post("/schedule", requireAuth("teacher"), async (req, res) => {
  const { subject_id, exam_date, duration_minutes } = req.body;

  const [[mcqCount]] = await pool.query(
    "SELECT COUNT(*) AS count FROM question_bank WHERE subject_id = ? AND question_type = 'MCQ'",
    [subject_id]
  );
  const [[descCount]] = await pool.query(
    "SELECT COUNT(*) AS count FROM question_bank WHERE subject_id = ? AND question_type = 'DESCRIPTIVE'",
    [subject_id]
  );

  if (mcqCount.count < 40 || descCount.count < 10) {
    return res.redirect("/teacher/schedule?error=Question%20bank%20incomplete");
  }

  await pool.query(
    "INSERT INTO exams (subject_id, teacher_id, exam_date, duration_minutes) VALUES (?, ?, ?, ?)",
    [subject_id, req.session.user.id, exam_date, duration_minutes]
  );

  res.redirect("/teacher/schedule");
});

router.get("/evaluate", requireAuth("teacher"), async (req, res) => {
  const [answers] = await pool.query(
    "SELECT sa.id, sa.answer_text, sa.marks_awarded, st.name AS student_name, s.name AS subject_name, e.id AS exam_id " +
      "FROM student_answers sa " +
      "JOIN students st ON sa.student_id = st.id " +
      "JOIN exams e ON sa.exam_id = e.id " +
      "JOIN subjects s ON e.subject_id = s.id " +
      "WHERE sa.question_type = 'DESCRIPTIVE' AND sa.evaluated = 0 AND e.teacher_id = ?",
    [req.session.user.id]
  );

  res.render("teacher/evaluate", {
    title: "Evaluate Descriptive",
    answers
  });
});

router.post("/evaluate/:id", requireAuth("teacher"), async (req, res) => {
  const { marks_awarded } = req.body;
  const answerId = req.params.id;

  const [[answer]] = await pool.query(
    "SELECT exam_id, student_id FROM student_answers WHERE id = ?",
    [answerId]
  );

  await pool.query(
    "UPDATE student_answers SET marks_awarded = ?, evaluated = 1 WHERE id = ?",
    [marks_awarded, answerId]
  );

  if (answer) {
    const [[totals]] = await pool.query(
      "SELECT SUM(marks_awarded) AS total FROM student_answers WHERE exam_id = ? AND student_id = ?",
      [answer.exam_id, answer.student_id]
    );

    const totalMarks = totals.total || 0;
    const percentage = ((totalMarks / 25) * 100).toFixed(2);
    const status = percentage >= 40 ? "Pass" : "Fail";

    await pool.query(
      "UPDATE results SET total_marks = ?, percentage = ?, status = ? WHERE exam_id = ? AND student_id = ?",
      [totalMarks, percentage, status, answer.exam_id, answer.student_id]
    );
  }

  res.redirect("/teacher/evaluate");
});

router.get("/results", requireAuth("teacher"), async (req, res) => {
  const [results] = await pool.query(
    "SELECT r.id, st.name AS student_name, s.name AS subject_name, r.total_marks, r.percentage, r.status " +
      "FROM results r " +
      "JOIN students st ON r.student_id = st.id " +
      "JOIN subjects s ON r.subject_id = s.id " +
      "JOIN exams e ON r.exam_id = e.id " +
      "WHERE e.teacher_id = ? ORDER BY r.id DESC",
    [req.session.user.id]
  );

  res.render("teacher/results", { title: "Student Results", results });
});

module.exports = router;
