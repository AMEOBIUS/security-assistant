// VULNERABLE (Node.js mysql):
// const query = "SELECT * FROM users WHERE id = " + userId;
// connection.query(query, (error, results) => { ... });

// SECURE (Node.js mysql):
// Use ? placeholders
const query = "SELECT * FROM users WHERE id = ?";
connection.query(query, [userId], (error, results) => { ... });

// VULNERABLE (Postgres pg):
// client.query("SELECT * FROM users WHERE id = " + userId);

// SECURE (Postgres pg):
// Use $1, $2 placeholders
client.query("SELECT * FROM users WHERE id = $1", [userId]);
