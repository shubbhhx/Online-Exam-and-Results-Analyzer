require("dotenv").config();
const mysql = require("mysql2/promise");

const isProduction = process.env.NODE_ENV === "production";
const databaseUrl = process.env.DATABASE_URL || "";

const parseDatabaseUrl = (urlString) => {
  try {
    const url = new URL(urlString);
    const sslParam =
      url.searchParams.get("ssl") ||
      url.searchParams.get("sslmode") ||
      url.searchParams.get("ssl-mode");

    return {
      host: url.hostname,
      user: decodeURIComponent(url.username || ""),
      password: decodeURIComponent(url.password || ""),
      database: url.pathname.replace(/^\//, ""),
      port: url.port ? Number(url.port) : 3306,
      sslRequested: sslParam ? sslParam !== "false" : null
    };
  } catch (err) {
    console.error("Invalid DATABASE_URL:", err.message);
    return null;
  }
};

const urlConfig = databaseUrl ? parseDatabaseUrl(databaseUrl) : null;
const useSsl =
  process.env.DB_SSL === "true" ||
  (urlConfig && urlConfig.sslRequested !== null
    ? urlConfig.sslRequested
    : Boolean(databaseUrl) && isProduction);

const poolConfig = urlConfig
  ? {
      host: urlConfig.host,
      user: urlConfig.user,
      password: urlConfig.password,
      database: urlConfig.database,
      port: urlConfig.port
    }
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
  ssl: useSsl ? { rejectUnauthorized: !isProduction } : undefined
});

pool.on("error", (err) => {
  console.error("Database pool error:", err);
});

const logAndRetry = (attempt) => {
  const delayMs = Math.min(5000 * attempt, 30000);
  console.warn(`Database connection failed. Retrying in ${delayMs}ms...`);
  setTimeout(() => testConnection(attempt + 1), delayMs);
};

const testConnection = async (attempt = 1) => {
  try {
    const connection = await pool.getConnection();
    console.log("Database connected.");
    connection.release();
  } catch (err) {
    console.error("Database connection failed:", err.message);
    logAndRetry(attempt);
  }
};

testConnection();

module.exports = pool;
