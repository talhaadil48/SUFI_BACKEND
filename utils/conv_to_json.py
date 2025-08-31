def user_to_dict(user_row):
    if not user_row:
        return None
    keys = ["id", "email", "name", "permissions", "role", 
            "country", "city", "is_registered", "created_at", "updated_at"]
    # Skip password_hash, otp, otp_expiry
    # Map row indices to keys (adjust according to actual DB row)
    indices = [0, 1, 2, 4, 5, 6, 7, 8, 9, 10]  # skip password_hash=3, otp=11, otp_expiry=12
    return {k: user_row[i] if i < len(user_row) else None for k, i in zip(keys, indices)}
