# VULNERABLE (MongoDB):
# db.users.find({"username": request.json['username']})
# If username is {"$ne": null}, it returns the first user (usually admin)

# SECURE:
username = request.json.get("username")

# 1. Type Check
if not isinstance(username, str):
    raise ValueError("Invalid username format")

# 2. Use ODM (like MongoEngine) which handles typing
# User.objects(username=username).first()
