# VULNERABLE:
# @app.route('/users/<int:user_id>/profile')
# def get_profile(user_id):
#     # Insecure Direct Object Reference (IDOR)
#     return db.get_user(user_id)

# SECURE:
from flask_login import current_user

@app.route('/users/<int:user_id>/profile')
@login_required
def get_profile(user_id):
    # Verify ownership
    if current_user.id != user_id and not current_user.is_admin:
        abort(403)
    
    return db.get_user(user_id)
