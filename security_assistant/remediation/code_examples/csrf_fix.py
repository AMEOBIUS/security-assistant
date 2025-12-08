# VULNERABLE (Flask):
# @app.route('/delete_account', methods=['POST'])
# def delete_account():
#     # ... logic to delete account ...
#     return "Account deleted"

# SECURE (using Flask-WTF):
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In your HTML forms:
# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

# VULNERABLE (requests):
# cookies = {'session': '...'}
# requests.post('http://api.com/update', data=data, cookies=cookies)

# SECURE (ensure custom header):
# Many APIs require a custom header like X-Requested-With to prevent CSRF
headers = {"X-Requested-With": "XMLHttpRequest"}
requests.post("http://api.com/update", data=data, headers=headers)
