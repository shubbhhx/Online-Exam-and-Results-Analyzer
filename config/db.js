require("dotenv").config();
const mysql = require("mysql2/promise");

const hasDatabaseUrl = Boolean(process.env.DATABASE_URL);
const useSsl =
  process.env.DB_SSL === "true" ||
  (hasDatabaseUrl && process.env.NODE_ENV === "production");

const poolConfig = hasDatabaseUrl
  ? { uri: process.env.DATABASE_URL }
  : {
      host: process.env.DB_HOST || "localhost",
      user: process.env.DB_USER || "root",
      password: process.env.DB_PASSWORD || "",
      database: process.env.DB_NAME || "online_exam_system",
      port: process.env.DB_PORT ? Number(process.env.DB_PORT) : 3306
    };

const pool = mysql.createPool({
  ...poolConfig,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  ssl: useSsl ? { rejectUnauthorized: true } : undefined
});

(async () => {
  try {
    const connection = await pool.getConnection();
    console.log("Database connected.");
    connection.release();
  } catch (err) {
    console.error("Database connection failed:", err.message);
  }
})();

module.exports = pool;
