from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://dbanoop:dbanoop123@cluster0.3fl6x.mongodb.net")
db = client.mydatabase

users_collection = db.users  # Access the users collection

# Signup endpoint
@app.route('/signup', methods=['POST'])
def signup():
    print("signup")
    data = request.json

    name = data.get('name')
    password = data.get('password')
    email = data.get('email')
    phone_no = data.get('phone_no')

    # Validate required fields
    if not name or not password or not email or not phone_no:
        return jsonify({"error": "All fields (name, password, email, phone_no) are required!"}), 400

    # Check if user already exists
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists!"}), 400


    # Insert user into the database
    users_collection.insert_one({
        "name": name,
        "password": password,
        "email": email,
        "phone_no": phone_no
    })

    return jsonify({"message": "Signup successful!"}), 201

# Signin endpoint
@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json

        # Extract data from the request
        email = data.get('email').strip()
        password = data.get('password').strip()
        print(f"Email is: {email} password: {password}")
        # Validate required fields
        if not email or not password:
            return jsonify({"error": "Email and password are required!"}), 400

        # Find user in the database
        user = users_collection.find_one({"email": email})
        if not user:
            return jsonify({"error": "Invalid email or password!"}), 401

        # Verify the password
        if user["password"] != password:
            return jsonify({"error": "Invalid email or password!"}), 401

        return jsonify({"name": user["name"], "mobile": user["phone_no"], "message": "success"})
    except Exception as e:
        print(f"Error during signin: {e}")
        return jsonify({"error": "An error occurred during signin"}), 500

if __name__ == '__main__':
    app.run(debug=True)