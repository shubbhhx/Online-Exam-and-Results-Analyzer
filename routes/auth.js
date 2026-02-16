const express = require("express");
const pool = require("../config/db");
const { generateRollNumber } = require("./helpers");

const router = express.Router();

router.get("/login", (req, res) => {
  res.render("login", {
    title: "Online Examination System",
    error: null,
    showAuthButtons: true,
    toast: req.query.toast
      ? { type: req.query.type || "success", message: req.query.toast }
      : null
  });
});

router.post("/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    const roleTables = [
      { role: "admin", table: "admins" },
      { role: "teacher", table: "teachers" },
      { role: "student", table: "students" }
    ];

    const matches = [];

    for (const entry of roleTables) {
      const [rows] = await pool.query(
        `SELECT * FROM ${entry.table} WHERE email = ? LIMIT 1`,
        [email]
      );

      if (rows.length && rows[0].password === password) {
        matches.push({ role: entry.role, user: rows[0] });
      }
    }

    if (!matches.length) {
      return res.render("login", {
        title: "Online Examination System",
        error: "Invalid credentials.",
        showAuthButtons: true
      });
    }

    if (matches.length > 1) {
      return res.render("login", {
        title: "Online Examination System",
        error: "Multiple accounts found. Contact support.",
        showAuthButtons: true
      });
    }

    const { role, user } = matches[0];
    req.session.user = {
      id: user.id,
      role,
      name: user.name
    };
    req.session.toast = {
      type: "success",
      message: "Login successful"
    };

    if (role === "admin") return res.redirect("/admin/dashboard");
    if (role === "teacher") return res.redirect("/teacher/dashboard");
    return res.redirect("/student/dashboard");
  } catch (error) {
    return res.render("login", {
      title: "Online Examination System",
      error: "Login failed. Try again.",
      showAuthButtons: true
    });
  }
});

router.get("/register", async (req, res) => {
  const [courses] = await pool.query("SELECT id, name FROM courses ORDER BY name");
  const [semesters] = await pool.query(
    "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
  );

  res.render("register", {
    title: "Student Registration",
    error: null,
    courses,
    semesters
  });
});

router.post("/register", async (req, res) => {
  const { name, email, password, course_id, semester_id, address, phone } =
    req.body;

  try {
    const [existing] = await pool.query(
      "SELECT id FROM students WHERE email = ?",
      [email]
    );

    if (existing.length) {
      const [courses] = await pool.query(
        "SELECT id, name FROM courses ORDER BY name"
      );
      const [semesters] = await pool.query(
        "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
      );

      return res.render("register", {
        title: "Student Registration",
        error: "Email already registered.",
        courses,
        semesters
      });
    }

    const [[semesterRow]] = await pool.query(
      "SELECT id, course_id, semester_number FROM semesters WHERE id = ?",
      [semester_id]
    );

    if (!semesterRow || String(semesterRow.course_id) !== String(course_id)) {
      const [courses] = await pool.query(
        "SELECT id, name FROM courses ORDER BY name"
      );
      const [semesters] = await pool.query(
        "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
      );

      return res.render("register", {
        title: "Student Registration",
        error: "Invalid course and semester selection.",
        courses,
        semesters
      });
    }

    const rollNumber = await generateRollNumber(semesterRow.semester_number);

    await pool.query(
      "INSERT INTO students (roll_number, name, email, password, course_id, semester_id, address, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      [
        rollNumber,
        name,
        email,
        password,
        course_id,
        semester_id,
        address || null,
        phone || null
      ]
    );

    res.redirect("/login?toast=Registration%20successful&type=success");
  } catch (error) {
    const [courses] = await pool.query(
      "SELECT id, name FROM courses ORDER BY name"
    );
    const [semesters] = await pool.query(
      "SELECT id, course_id, semester_number, title FROM semesters ORDER BY semester_number"
    );

    res.render("register", {
      title: "Student Registration",
      error: "Registration failed.",
      courses,
      semesters
    });
  }
});

router.get("/logout", (req, res) => {
  req.session.destroy(() => {
    res.redirect("/login");
  });
});

module.exports = router;
