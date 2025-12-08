# VULNERABLE:
# query = "SELECT * FROM users WHERE username = '" + username + "'"
# cursor.execute(query)

# SECURE (Parameterized Query):
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (username,))
