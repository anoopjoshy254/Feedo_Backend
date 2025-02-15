from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import uuid

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://dbanoop:dbanoop123@cluster0.3fl6x.mongodb.net")
db = client.mydatabase

users_collection = db.users  # Access the users collection
schedules_collection = db.schedules  # Access the schedules collection

# Signup endpoint
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('name')
        password = data.get('password')
        email = data.get('email')
        phone_no = data.get('phone_no')

        if not name or not password or not email or not phone_no:
            return jsonify({"error": "All fields are required!"}), 400

        if users_collection.find_one({"email": email}):
            return jsonify({"error": "User with this email already exists!"}), 400

        users_collection.insert_one({
            "name": name,
            "password": password,
            "email": email,
            "phone_no": phone_no
        })

        return jsonify({"message": "Signup successful!"}), 201
    except Exception as e:
        print(f"Error during signup: {e}")
        return jsonify({"error": "An error occurred during signup"}), 500

# Signin endpoint
@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required!"}), 400

        user = users_collection.find_one({"email": email})
        if not user or user["password"] != password:
            return jsonify({"error": "Invalid email or password!"}), 401

        return jsonify({"name": user["name"], "mobile": user["phone_no"], "message": "success"})
    except Exception as e:
        print(f"Error during signin: {e}")
        return jsonify({"error": "An error occurred during signin"}), 500

# Save schedule endpoint
@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    try:
        data = request.json
        time = data.get('time')
        weight = data.get('weight')
        user_email = data.get('user_email')

        if not time or not weight or not user_email:
            return jsonify({"error": "Time, weight, and user email are required!"}), 400

        schedule_id = str(uuid.uuid4())

        schedules_collection.insert_one({
            "id": schedule_id,
            "time": time,
            "weight": weight,
            "user_email": user_email,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({"message": "Schedule saved successfully!", "id": schedule_id}), 201
    except Exception as e:
        print(f"Error saving schedule: {e}")
        return jsonify({"error": "An error occurred while saving the schedule"}), 500

# Fetch schedules endpoint
@app.route('/get_schedules', methods=['POST'])
def get_schedules():
    try:
        data = request.json
        user_email = data.get('user_email')

        if not user_email:
            return jsonify({"error": "User email is required!"}), 400

        schedules = list(schedules_collection.find({}, {"_id": 0}))

        return jsonify({"schedules": schedules}), 200
    except Exception as e:
        print(f"Error fetching schedules: {e}")
        return jsonify({"error": "An error occurred while fetching schedules"}), 500

# Delete schedule endpoint
@app.route('/delete_schedule', methods=['POST'])
def delete_schedule():
    try:
        data = request.json
        schedule_id = data.get('time')

        if not schedule_id:
            return jsonify({"error": "Schedule ID is required!"}), 400

        schedules_collection.delete_one({"time": schedule_id})

        return jsonify({"message": "Schedule deleted successfully!"}), 200
    except Exception as e:
        print(f"Error deleting schedule: {e}")
        return jsonify({"error": "An error occurred while deleting the schedule"}), 500
        # Fetch Feeding History endpoint
@app.route('/feeding-history', methods=['GET'])
def get_feeding_history():
    try:
        # Retrieve all feeding history records from the database
        feeding_history = db.schedules.find({}, {"_id": 0})  # Exclude MongoDB's default _id field
        
        # Create a list of dictionaries that matches the frontend Scheduledata structure
        history_list = []
        for record in feeding_history:
            history_list.append({
                "time": record.get("time", ""),
                "weight": record.get("weight", 0),
                "user_email": record.get("user_email", ""),
                "date": record.get("date", "")
            })

        # Return the feeding history in JSON format
        return jsonify(history_list)
    except Exception as e:
        return jsonify({"error": "An error occurred while fetching feeding history"}), 500

# Insert Feeding History endpoint
@app.route('/feeding-history', methods=['POST'])
def add_feeding_history():
    try:
        data = request.json

        # Extract feeding history details from the request
        time = data.get('time')
        weight = data.get('weight')
        user_email = data.get('user_email')
        date = data.get('date')

        # Validate required fields
        if not time or weight is None or not user_email:
            return jsonify({"error": "Time, weight, and food type are required!"}), 400

        # Insert new feeding record into the database
        db.schedules.insert_one({
            "time": time,
            "weight": weight,
            "user_email": user_email,
            "date": date
        })
        return jsonify({"message": "Feeding history added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": "An error occurred while adding feeding history"}), 500

# Delete Feeding History endpoint
@app.route('/feeding-history/<string:time>', methods=['DELETE'])
def delete_feeding_history(time):
    try:
        # Delete feeding history record by time (or other unique identifier)
        result = feeding_history_collection.delete_one({"time": time})
        
        if result.deleted_count == 0:
            return jsonify({"error": "No feeding history found with the provided time."}), 404

        return jsonify({"message": "Feeding history deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while deleting feeding history"}), 500

# Edit Feeding History endpoint
@app.route('/feeding-history/<string:time>', methods=['PUT'])
def edit_feeding_history(time):
    try:
        data = request.json

        # Extract feeding history details to update
        weight = data.get('weight')
        user_email = data.get('user_email')
        date = data.get('date')

        # Validate required fields
        if weight is None or not food_type:
            return jsonify({"error": "Weight and food type are required!"}), 400

        # Update the feeding history record
        result = feeding_history_collection.update_one(
            {"time": time},
            {"$set": {
                "weight": weight,
                "user_email": user_email,
                "date": date
            }}
        )

        if result.matched_count == 0:
            return jsonify({"error": "No feeding history found with the provided time."}), 404

        return jsonify({"message": "Feeding history updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred while updating feeding history"}), 500

if __name__ == '__main__':
    app.run(debug=True)
