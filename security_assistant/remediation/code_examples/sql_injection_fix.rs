// VULNERABLE:
// let query = format!("SELECT * FROM users WHERE username = '{}'", username);
// let rows = conn.query(&query, &[])?;

// SECURE (Parameterized Query with rusqlite):
let query = "SELECT * FROM users WHERE username = ?1";
let mut stmt = conn.prepare(query)?;
let rows = stmt.query(params![username])?;
