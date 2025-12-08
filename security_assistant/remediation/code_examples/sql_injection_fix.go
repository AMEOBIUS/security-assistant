// VULNERABLE:
// query := "SELECT * FROM users WHERE username = '" + username + "'"
// rows, err := db.Query(query)

// SECURE (Parameterized Query):
query := "SELECT * FROM users WHERE username = ?"
rows, err := db.Query(query, username)
if err != nil {
    log.Fatal(err)
}
defer rows.Close()
