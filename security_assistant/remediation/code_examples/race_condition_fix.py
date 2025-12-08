# VULNERABLE:
# balance = db.get_balance(user_id)
# if balance >= amount:
#     db.set_balance(user_id, balance - amount)

# SECURE (Database Atomic Update):
# UPDATE accounts SET balance = balance - 100 WHERE user_id = 1 AND balance >= 100
# Check rowcount to see if it succeeded

# SECURE (Python Locking - for local resources):
import threading

lock = threading.Lock()

with lock:
    # Critical section
    balance = get_balance()
    if balance >= amount:
        set_balance(balance - amount)
