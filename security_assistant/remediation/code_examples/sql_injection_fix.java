// VULNERABLE:
// String query = "SELECT * FROM users WHERE username = '" + username + "'";
// Statement stmt = connection.createStatement();
// ResultSet rs = stmt.executeQuery(query);

// SECURE (Prepared Statement):
String query = "SELECT * FROM users WHERE username = ?";
PreparedStatement pstmt = connection.prepareStatement(query);
pstmt.setString(1, username);
ResultSet rs = pstmt.executeQuery();
