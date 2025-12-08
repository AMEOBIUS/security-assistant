# VULNERABLE:
# user.update(request.form) # Updates ANY field sent by user (e.g., is_admin=True)

# SECURE (Pydantic / FastAPI):
from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: str
    email: str
    # is_admin is NOT included here, so it cannot be updated via this model

def update_user(user_id, data: UserUpdate):
    # Only fields in UserUpdate can be processed
    user = db.get(user_id)
    user.update(data.dict())

# SECURE (Django):
# class UserForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['username', 'email'] # Explicit allowlist
