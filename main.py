import schedule
import threading
from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import uuid
import serial
import time
import subprocess


app = Flask(__name__)




# Connect to MongoDB
client = MongoClient("mongodb+srv://dbanoop:dbanoop123@cluster0.3fl6x.mongodb.net")
db = client.mydatabase

users_collection = db.users  # Access the users collection
schedules_collection = db.schedules  # Access the schedules collection
past_collection = db.past_schedules

@app.route('/update_schedule', methods=['PUT'])
def update_schedule():
    try:
        data = request.json
        schedule_id = data.get('id')
        isEnabled = data.get('isEnabled')

        if not schedule_id:
            return jsonify({"error": "Schedule ID is required!"}), 400

        result = schedules_collection.update_one({"id": schedule_id}, {"$set": {"isEnabled": isEnabled}})

        if result.matched_count == 0:
            return jsonify({"error": "Schedule not found"}), 404

        return jsonify({"message": "Schedule updated successfully!"}), 200
    except Exception as e:
        print(f"Error updating schedule: {e}")
        return jsonify({"error": "An error occurred while updating the schedule"}), 500



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

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    try:
        data = request.json
        time_val = data.get('time')
        weight = data.get('weight')
        user_email = data.get('user_email')
        pond_name = data.get('pond_name')  # Now storing pond name for later filtering
        isEnabled = data.get('isEnabled', True)
        if not time_val or not weight or not user_email or not pond_name:
            return jsonify({"error": "Time, weight, user email, and pond name are required!"}), 400

        schedule_id = str(uuid.uuid4())
        schedule_doc = {
            "id": schedule_id,
            "pond_name": pond_name,
            "time": time_val,
            "weight": weight,
            "user_email": user_email,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "isEnabled": isEnabled
        }
        schedules_collection.insert_one(schedule_doc)
        # Call new schedule_alarm with all parameters so that the completed schedule is recorded.
        schedule_alarm(time_val, weight, user_email, pond_name)
        return jsonify({"message": "Schedule saved successfully!"}), 201
    except Exception as e:
        print(f"Error saving schedule: {e}")
        return jsonify({"error": "An error occurred while saving the schedule"}), 500

def run_script(script_name):
    """Run a Python script as a subprocess."""
    try:
        subprocess.Popen(["python", script_name])
        print(f"Executed {script_name}")
    except Exception as e:
        print(f"Error executing {script_name}: {e}")

def send_notification(message):
    # Placeholder: Replace with push integration if needed.
    print(f"Notification: {message}")

def schedule_alarm(feed_time, weight, user_email, pond_name):
    try:
        weight_val = int(weight)
    except Exception as ex:
        print("Error converting weight to int:", ex)
        weight_val = 1
    def start_feeding():
        print("Starting feeding process for pond:", pond_name)
        send_notification(f"Feeding for pond {pond_name} started at {feed_time}")
        run_script("start.py")
        stop_delay = weight_val * 30
        print(f"Feeding will stop after {stop_delay} seconds.")
        threading.Timer(stop_delay, stop_and_save).start()
    def stop_and_save():
        run_script("stop.py")
        send_notification(f"Feeding for pond {pond_name} stopped")
        past_doc = {
            "time": feed_time,
            "weight": weight_val,
            "user_email": user_email,
            "pond_name": pond_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            result = db.past_schedules.insert_one(past_doc)
            print("Inserted past schedule with id:", result.inserted_id)
        except Exception as ex:
            print("Error inserting past schedule:", ex)
    # Note: Ensure feed_time is in HH:mm format and represents a time later than current system time
    schedule.every().day.at(feed_time).do(start_feeding)
    print(f"Feeding scheduled at {feed_time} for pond {pond_name} with stop delay of {weight_val * 30} seconds.")

# Function to continuously run scheduled jobs
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Fetch schedules endpoint
@app.route('/get_schedules', methods=['POST'])
def get_schedules():
    try:
        data = request.json
        user_email = data.get('user_email')

        if not user_email:
            return jsonify({"error": "User email is required!"}), 400

        schedules = list(schedules_collection.find({"user_email": user_email}, {"_id": 0}))

        return jsonify({"schedules": schedules}), 200
    except Exception as e:
        print(f"Error fetching schedules: {e}")
        return jsonify({"error": "An error occurred while fetching schedules"}), 500

@app.route('/get_schedules/<pond_name>', methods=['GET'])
def get_schedules_by_pond(pond_name):
    try:
        schedules = list(schedules_collection.find({"pond_name": pond_name}, {"_id": 0}))
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
        feeding_history = db.past_schedules.find({}, {"_id": 0})  # Exclude MongoDB's default _id field
        
        # Create a list of dictionaries that matches the frontend Scheduledata structure
        history_list = []
        for record in feeding_history:
            history_list.append({
                "time": record.get("time", ""),
                "weight": record.get("weight", 0),
                "user_email": record.get("user_email", ""),
                "date": record.get("date", ""),
                "pond_name": record.get("pond_name", "")
            })

        # Log the fetched history for debugging
        print("Fetched feeding history:", history_list)

        # Return the feeding history in JSON format
        return jsonify(history_list)
    except Exception as e:
        print(f"Error fetching feeding history: {e}")
        return jsonify({"error": "An error occurred while fetching feeding history"}), 500
@app.route('/update_schedule_status', methods=['POST'])
def update_schedule_status():
    try:
        data = request.json
        schedule_id = data.get('id')
        is_enabled = data.get('is_enabled')

        if not schedule_id or is_enabled is None:
            return jsonify({"error": "Schedule ID and status are required!"}), 400

        schedules_collection.update_one(
            {"id": schedule_id},
            {"$set": {"is_enabled": is_enabled}}
        )

        return jsonify({"message": "Schedule status updated successfully!"}), 200
    except Exception as e:
        print(f"Error updating schedule status: {e}")
        return jsonify({"error": "An error occurred while updating schedule status"}), 500

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
@app.route('/update_feeding_history', methods=['PUT'])
def update_feeding_history():
    try:
        data = request.json
        time = data.get('time')
        weight = data.get('weight')
        user_email = data.get('user_email')
        date = data.get('date')

        # Update feeding history
        result = feeding_history_collection.update_one(
            {"time": time},
            {"$set": {
                "weight": weight,
                "user_email": user_email,
                "date": date
            }}
        )

        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
import os   

@app.route('/start_feeding', methods=['GET'])
def start_feeding():
    """Send command to Arduino to rotate servo 90 degrees"""
    try:
        os.system("python start.py")
        return jsonify({"message": "Servo started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop_feeding', methods=['GET'])
def stop_feeding():
    """Send command to Arduino to reset servo position"""
    try:
        os.system("python stop.py")
        return jsonify({"message": "Servo stopped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# New endpoint for adding a pond
@app.route('/add_pond', methods=['POST'])
def add_pond():
    try:
        data = request.json
        pond_name = data.get('pond_name')
        feeder_id = data.get('feeder_id')
        breed_type = data.get('breed_type')

        if not pond_name or not feeder_id or not breed_type:
            return jsonify({"error": "Pond name, feeder id, and breed type are required!"}), 400

        pond = {
            "pond_name": pond_name,
            "feeder_id": feeder_id,
            "breed_type": breed_type,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        ponds_collection = db.ponds  # Use or create a new collection for ponds
        ponds_collection.insert_one(pond)

        return jsonify({"message": "Pond added successfully!"}), 201
    except Exception as e:
        print(f"Error adding pond: {e}")
        return jsonify({"error": "An error occurred while adding the pond"}), 500
    
@app.route('/get_ponds', methods=['GET'])
def get_ponds():
    try:
        ponds = list(db.ponds.find({}))
        ponds = [{"pond_name": pond["pond_name"], "feeder_id": pond["feeder_id"], "breed_type": pond["breed_type"], "_id": str(pond["_id"])} for pond in ponds]
        return jsonify(ponds), 200
    except Exception as e:
        print(f"Error fetching ponds: {e}")
        return jsonify({"error": "An error occurred while fetching ponds"}), 500


app.run(host='0.0.0.0', port=5000, debug=True)















if __name__ == '__main__':
    app.run(debug=True)
