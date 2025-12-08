# VULNERABLE:
# @app.route('/admin')
# def admin_panel():
#     return render_template('admin.html')

# SECURE (Flask-Login):
from flask_login import login_required, current_user

@app.route('/admin')
@login_required
def admin_panel():
    # Even if logged in, we must check authorization/access control!
    if not current_user.is_admin:
         abort(403)
    return render_template('admin.html')
