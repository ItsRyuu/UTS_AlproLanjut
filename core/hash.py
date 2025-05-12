import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(input_password, stored_hash):
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode()
    return bcrypt.checkpw(input_password.encode(), stored_hash)