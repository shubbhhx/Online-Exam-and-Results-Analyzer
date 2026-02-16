const pool = require("../config/db");

function requireRole(role) {
  return (req, res, next) => {
    if (!req.session.user || req.session.user.role !== role) {
      return res.redirect("/login");
    }
    next();
  };
}

function requireAuth(role) {
  return (req, res, next) => {
    if (!req.session.user) {
      return res.redirect("/login");
    }

    if (role && req.session.user.role !== role) {
      return res.status(403).render("forbidden", {
        title: "Access Denied"
      });
    }

    next();
  };
}

async function generateTeacherCode() {
  const year = new Date().getFullYear();
  const prefix = `TCH-${year}-`;
  const [rows] = await pool.query(
    "SELECT teacher_code FROM teachers WHERE teacher_code LIKE ? ORDER BY teacher_code DESC LIMIT 1",
    [`${prefix}%`]
  );

  let nextNumber = 1;
  if (rows.length) {
    const lastCode = rows[0].teacher_code || "";
    const lastNumber = parseInt(lastCode.split("-").pop(), 10);
    if (!Number.isNaN(lastNumber)) {
      nextNumber = lastNumber + 1;
    }
  }

  return `${prefix}${String(nextNumber).padStart(3, "0")}`;
}

async function generateRollNumber(semesterNumber) {
  const year = new Date().getFullYear();
  const prefix = `${year}-SEM${semesterNumber}-`;
  const [rows] = await pool.query(
    "SELECT roll_number FROM students WHERE roll_number LIKE ? ORDER BY roll_number DESC LIMIT 1",
    [`${prefix}%`]
  );

  let nextNumber = 1;
  if (rows.length) {
    const lastRoll = rows[0].roll_number || "";
    const lastNumber = parseInt(lastRoll.split("-").pop(), 10);
    if (!Number.isNaN(lastNumber)) {
      nextNumber = lastNumber + 1;
    }
  }

  return `${prefix}${String(nextNumber).padStart(3, "0")}`;
}

module.exports = {
  requireRole,
  requireAuth,
  generateTeacherCode,
  generateRollNumber
};
