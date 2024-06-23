from flask import Flask, request, jsonify, session
from handlers.database import sqlBranch, sqlLocation, sqlEmployee, sqlAuth

from handlers.encryption import Encryption

app = Flask(__name__)

encryption = Encryption()

@app.route('/')
def home():
	return 'fuck off hamayon <3'


@app.route('/api/v1/example', methods=[ 'GET' , 'POST' ])
def api():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			response = {
				"message": "The POST example was successfully recieved",
				"data": data
			}
			return jsonify(response), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400
		

	if request.method == 'GET':
		response = {
				"message": "Get was recieved successfully",
				"data": "Get Was a success"
			}
		
		try:
			return jsonify(response), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400

###
###			AUTH API ROUTES
###

@app.route('/api/v1/login', methods=['POST'])
def login():
	if request.method == 'POST':
		
		try:
			data = request.get_json(force=True)

			token = sqlAuth.login(data['email'], data['password'])

			print(token)
			if(token == ''):
				return jsonify({"failure": "Failed to login"}), 400
			
			return jsonify({"success": "Login complete", "token": token}), 200

		except Exception as e:
			return jsonify({"error": str(e)}), 400
		
@app.route('/api/v1/logout', methods=['POST'])
def logout():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)

			if(not sqlAuth.delete_token(data['token'])):
				return jsonify({"failure": "Failed to logout"}), 400

			return jsonify({"success": "Logout complete"}), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400



###
### 		BRANCH API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createBranch', methods=['POST'])
def createBranch():
	if request.method == 'POST':


		try:
			data = request.get_json(force=True)


			print(data['name'])
			if(sqlBranch.create(data["name"], token=data["token"])):
				return jsonify({"success": "Table Insertion Complete"}), 200
			else:
				return jsonify({"failure": "Failed to insert the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/getBranches', methods=['POST'])
def getBranches():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			print(data)

			result = sqlBranch.get_branches(token=data["token"])

			print(result)

			encrypted_result = encryption.encrypt(data['token'], result)

			print(encrypted_result)

			return jsonify(encrypted_result), 200
		except Exception as e:
			print(e)
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/getBranch', methods=['POST'])
def getBranch():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			result = sqlBranch.get_branch(data["branch_id"], token=data["token"])
			return jsonify(result), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/updateBranch', methods=['POST'])
def updateBranch():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlBranch.update(data["branch_id"], data["name"], token=data["token"])):
				return jsonify({"success": "Table Update Complete"}), 200
			else:
				return jsonify({"failure": "Failed to update the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/deleteBranch', methods=['POST'])
def deleteBranch():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			if(sqlBranch.delete(data["branch_id"], token=data["token"])):
				return jsonify({"success": "Table Deletion Complete"}), 200
			else:
				return jsonify({"failure": "Failed to delete the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

###
### 		LOCATION API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createLocation', methods=['POST'])
def createLocation():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlLocation.create(city=data["city"], token=data["token"])):
				return jsonify({"success": "Table Insertion Complete"}), 200
			else:
				return jsonify({"failure": "Token may have expired"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/getLocations', methods=['POST'])
def getLocations():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			result = sqlLocation.get_locations(token=data["token"])
			return jsonify(result), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/getLocation', methods=['POST'])
def getLocation():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			result = sqlLocation.get_location(data["location_id"], token=data["token"])
			return jsonify(result), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/updateLocation', methods=['POST'])
def updateLocation():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlLocation.update(data["location_id"], data["city"], token=data["token"])):
				return jsonify({"success": "Table Update Complete"}), 200
			else:
				return jsonify({"failure": "Failed to update the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/deleteLocation', methods=['POST'])
def deleteLocation():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlLocation.delete(data["location_id"], token=data["token"])):
				return jsonify({"success": "Table Deletion Complete"}), 200
			else:
				return jsonify({"failure": "Failed to delete the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400


###
### 		EMPLOYEE API ROUTES
###				C.R.U.D.


@app.route('/api/v1/createEmployee', methods=['POST'])
def createEmployee():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlEmployee.create(data["first_name"], data["last_name"], data["email"], data["password"], data["branch_id"], data["position"], token=data["token"])):
				return jsonify({"success": "Table Insertion Complete"}), 200
			else:
				return jsonify({"failure": "Failed to insert the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400
		
@app.route('/api/v1/getEmployees', methods=['POST'])
def getEmployees():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)
			result = sqlEmployee.get(token=data["token"])
			return jsonify(result), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400
		
@app.route('/api/v1/getEmployee', methods=['POST'])
def getEmployee():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			result = sqlEmployee.get(data["employee_id"], token=data["token"])
			return jsonify(result), 200
		except Exception as e:
			return jsonify({"error": str(e)}), 400
		
@app.route('/api/v1/updateEmployee', methods=['POST'])
def updateEmployee():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			new_password = data["new_password"] if "new_password" in data else None

			if(sqlEmployee.update(data["employee_id"], data["first_name"], data["last_name"], data["email"], data["password"], new_password=new_password, token=data["token"])):
				return jsonify({"success": "Table Update Complete"}), 200
			else:
				return jsonify({"failure": "Failed to update the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/deleteEmployee', methods=['POST'])
def deleteEmployee():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			if(sqlEmployee.delete(data["employee_id"], token=data["token"])):
				return jsonify({"success": "Table Deletion Complete"}), 200
			else:
				return jsonify({"failure": "Failed to delete the data"}), 400
		except Exception as e:
			return jsonify({"error": str(e)}), 400

if __name__ == '__main__':





	app.run(debug=True)

	print("tuh")