import bcrypt

password = "password"
hash_to_check = "$2b$12$LQv3c1yqBwEHxv03kqfvqOuHyNoy3AjkJIBqnqHqJQi4W5.1fE5Cu"

if bcrypt.checkpw(password.encode('utf-8'), hash_to_check.encode('utf-8')):
    print("YES - The hash matches 'password'")
else:
    print("NO - The hash does not match 'password'")
