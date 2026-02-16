require("dotenv").config();
const path = require("path");
const express = require("express");
const session = require("express-session");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const csrf = require("csurf");
const MySQLStore = require("express-mysql-session")(session);
const pool = require("./config/db");

const authRoutes = require("./routes/auth");
const adminRoutes = require("./routes/admin");
const teacherRoutes = require("./routes/teacher");
const studentRoutes = require("./routes/student");

const app = express();
app.set("trust proxy", 1);
const isProduction = process.env.NODE_ENV === "production";

app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(
  helmet({
    contentSecurityPolicy: false
  })
);

const loginLimiter = rateLimit({
  windowMs: 10 * 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false
});
app.use("/login", loginLimiter);

const sessionStore = isProduction
  ? new MySQLStore(
      {
        clearExpired: true,
        checkExpirationInterval: 15 * 60 * 1000,
        expiration: 24 * 60 * 60 * 1000
      },
      pool
    )
  : undefined;

app.use(
  session({
    secret: process.env.SESSION_SECRET || "change_me",
    resave: false,
    saveUninitialized: false,
    store: sessionStore,
    cookie: {
      secure: process.env.NODE_ENV === "production",
      httpOnly: true,
      sameSite: "lax"
    }
  })
);

app.use(csrf());

app.use((req, res, next) => {
  if (req.body && typeof req.body === "object") {
    for (const key of Object.keys(req.body)) {
      if (typeof req.body[key] === "string") {
        req.body[key] = req.body[key].trim().replace(/\0/g, "");
      }
    }
  }
  next();
});

app.use((req, res, next) => {
  res.locals.user = req.session.user || null;
  res.locals.pageLoading = false;
  res.locals.title = res.locals.title || "Dashboard";
  res.locals.showAuthButtons = false;
  res.locals.csrfToken = req.csrfToken ? req.csrfToken() : null;
  res.locals.toast = req.session.toast || null;
  if (req.session.toast) {
    req.session.toast = null;
  }
  next();
});

app.use("/public", express.static(path.join(__dirname, "public")));
app.use(
  "/vendor/bootstrap",
  express.static(path.join(__dirname, "node_modules", "bootstrap", "dist"))
);
app.use(
  "/vendor/chartjs",
  express.static(path.join(__dirname, "node_modules", "chart.js", "dist"))
);

app.get("/", (req, res) => {
  res.redirect("/login");
});

app.use(authRoutes);
app.use("/admin", adminRoutes);
app.use("/teacher", teacherRoutes);
app.use("/student", studentRoutes);

app.use((req, res) => {
  res.status(404).render("not_found", { title: "Not Found" });
});

app.use((err, req, res, next) => {
  if (err.code === "EBADCSRFTOKEN") {
    return res.status(403).render("forbidden", { title: "Forbidden" });
  }
  console.error("Unhandled error:", err);
  res.status(500).send("Internal Server Error");
});

const PORT = process.env.PORT || 3000;
const server = app.listen(PORT, () => {
  console.log(`Server running on ${PORT}`);
});

const shutdown = async (signal) => {
  console.log(`Received ${signal}. Shutting down...`);
  server.close(async () => {
    try {
      await pool.end();
      console.log("Database pool closed.");
    } catch (err) {
      console.error("Error closing database pool:", err);
    }
    process.exit(0);
  });
};

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("unhandledRejection", (reason) => {
  console.error("Unhandled rejection:", reason);
  process.exit(1);
});
process.on("uncaughtException", (err) => {
  console.error("Uncaught exception:", err);
  process.exit(1);
});
