from flask import Flask, request, jsonify, session
from handlers.database import sqlBranch, sqlLocation, sqlEmployee, sqlAuth, sqlSisters

from handlers.encryption import Encryption

app = Flask(__name__)

encryption = Encryption()



def decryptRecieved(request):
	data = request.get_json(force=True)

	return encryption.decrypt(data['transfer'].encode('latin1')), data['token']



def returnEncrypted(token, data, code):
	encrypted_result = encryption.encrypt(token, data)

	return jsonify(encrypted_result), code



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
			data, tag = decryptRecieved(request)

			token = sqlAuth.login(data['email'], data['password'])

			encrypted_message = encryption.hsencrypt(tag, {"token": token})

			
			if(token == ''):
				return jsonify({"failure": "Failed to login"}), 400
			
			return jsonify({"success": "Login complete", "transfer": encrypted_message}), 200

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
			data, token = decryptRecieved(request)

			if(not sqlBranch.create(data["name"], token=token)):
				raise Exception("Failed to insert data, likely a duplicate name")
			
			return returnEncrypted(token, {"success": "New branch successfully created"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getBranches', methods=['POST'])
def getBranches():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlBranch.get_branches(token=data["token"])
			if result == None:
				raise Exception("Could not retreive branches from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/getBranch', methods=['POST'])
def getBranch():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)
		
			result = sqlBranch.get_branch(data["branch_id"], token=token)
			if result == None:
				raise Exception("Could not get the requested branch data")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			print(e)
			return jsonify({"error": str(e)}), 200

@app.route('/api/v1/updateBranch', methods=['POST'])
def updateBranch():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlBranch.update(data["branch_id"], data["name"], token=token)):
				raise Exception("Branch could not be updated")

			return returnEncrypted(token, {"success": "Branch update completed successfully"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/deleteBranch', methods=['POST'])
def deleteBranch():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlBranch.delete(data["branch_id"], token=token)):
				raise Exception("Could not delete branch entry")
			
			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		LOCATION API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createLocation', methods=['POST'])
def createLocation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlLocation.create(city=data["city"], token=token)):
				raise Exception("Failed to create new Location")

			return returnEncrypted(token, {"success": "New Location successfully created"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getLocations', methods=['POST'])
def getLocations():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlLocation.get_locations(token=data["token"])
			if result == None:
				raise Exception("Could not retreive Locations from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/getLocation', methods=['POST'])
def getLocation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlLocation.get_location(data["location_id"], token=token)
			if result == None:
				raise Exception("Could not retreive requested Location data")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/updateLocation', methods=['POST'])
def updateLocation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlLocation.update(data["location_id"], data["city"], token=token)):
				raise Exception("Could not update Location data")
				
			return returnEncrypted(token, {"success": "Location update completed successfully"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/deleteLocation', methods=['POST'])
def deleteLocation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlLocation.delete(data["location_id"], token=token)):
				raise Exception("Failed to delete Location entry")
			
			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


###
### 		EMPLOYEE API ROUTES
###				C.R.U.D.


#### doesnt work - fix encryption

@app.route('/api/v1/createEmployee', methods=['POST'])
def createEmployee():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlEmployee.create(data["first_name"], data["last_name"], data["email"], data["password"], data["branch_id"], data["position"], token=token)):
				raise Exception("Could not create new employee, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getEmployees', methods=['POST'])
def getEmployees():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)
			result = sqlEmployee.get_all(token=data["token"])
			if result == None:
				raise Exception("Could not retreive Employees from database")

			retList = []
			for res in result:
				resList = list(res)
				resList[5] = resList[5].strftime("%Y-%m-%d %H:%M:%S")
				resList[6] = resList[6].strftime("%Y-%m-%d %H:%M:%S")
				retList.append(resList)

			return returnEncrypted(data['token'], retList, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getEmployee', methods=['POST'])
def getEmployee():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)
			result = sqlEmployee.get(data["employee_id"], token=token)
			if result == None:
				raise Exception("Could not retreive requested Employee data")

			result = list(result)
			result[5] = result[5].strftime("%Y-%m-%d %H:%M:%S")
			result[6] = result[6].strftime("%Y-%m-%d %H:%M:%S")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/updateEmployee', methods=['POST']) 
def updateEmployee():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			new_password = data["new_password"] if "new_password" in data else None

			if(not sqlEmployee.update(data["employee_id"], data["first_name"], data["last_name"], data["email"], data["password"], new_password=new_password, token=token)):
				raise Exception("Could not update Employee data")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/deleteEmployee', methods=['POST'])
def deleteEmployee():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(sqlEmployee.delete(data["employee_id"], token=token)):
				raise Exception("Failed to delete Employee entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/createSisterhood', methods=['POST'])
def createSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlSisters.create(data["branch1"],data["branch2"],data["location"], token=token)):
				raise Exception("Could not create new Sisterhood, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


@app.route('/api/v1/getSisterhoods', methods=['POST'])
def getSisterhoods():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)
			result = sqlSisters.get_all(token=data["token"])
			if result == None:
				raise Exception("Could not retreive Sisterhoods from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getSisterhood', methods=['POST'])
def getSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)
			result = sqlSisters.get(data["sisterhood_id"], token=token)
			if result == None:
				raise Exception("Could not retreive requested Sisterhood data")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		



if __name__ == '__main__':


	app.run(debug=True)

	print("tuh")