from flask import Flask, request, jsonify, render_template_string
from handlers.database import sqlBranch, sqlLocation, sqlEmployee, sqlAuth, sqlSisters, sqlEmployeeDiscounts, sqlDiscounts, sqlReservations, sqlStock, sqlInventory, sqlFood, sqlDrink, sqlAllergins, sqlOrders, sqlMenu, sqlManger
import logging
from collections import deque
from handlers.encryption import Encryption
import sys

app = Flask(__name__)

encryption = Encryption()

print("Server started")

log_messages = deque(maxlen=50)

# Custom logging handler to store messages in the in-memory deque
class MemoryHandler(logging.Handler):
	def emit(self, record):
		log_messages.append(self.format(record))

# Set up logging
memory_handler = MemoryHandler()
memory_formatter = logging.Formatter('%(asctime)s - %(message)s')
memory_handler.setFormatter(memory_formatter)
app.logger.addHandler(memory_handler)
app.logger.setLevel(logging.DEBUG)

# Stream handler to print to console
console_handler = logging.StreamHandler(sys.stdout)
app.logger.addHandler(console_handler)

# Redirect stdout and stderr to logging
class StreamToLogger:
	def __init__(self, logger, log_level=logging.INFO):
		self.logger = logger
		self.log_level = log_level

	def write(self, message):
		if message.strip():  # Ignore empty messages
			self.logger.log(self.log_level, message.strip())

	def flush(self):
		pass

stdout_logger = logging.getLogger('STDOUT')
stdout_logger.addHandler(memory_handler)
stdout_logger.addHandler(console_handler)
stdout_logger.setLevel(logging.INFO)

stderr_logger = logging.getLogger('STDERR')
stderr_logger.addHandler(memory_handler)
stderr_logger.addHandler(console_handler)
stderr_logger.setLevel(logging.ERROR)

sys.stdout = StreamToLogger(stdout_logger, logging.INFO)
sys.stderr = StreamToLogger(stderr_logger, logging.ERROR)


print("Logging setup complete")

@app.route('/logs')
def logs():
	return render_template_string('<pre>{{ logs }}</pre>', logs='\n'.join(log_messages))

def decryptRecieved(request):
	data = request.get_json(force=True)

	return encryption.decrypt(data['transfer'].encode('latin1')), data['token']



def returnEncrypted(token, data, code):
	encrypted_result = encryption.encrypt(token, data)

	return jsonify(encrypted_result), code


def errorCallback(err):
	raise Exception(err)


@app.route('/')
def home():
	app.logger.info('Home page accessed')
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

			token, uid, role = sqlAuth.login(data['email'], data['password'])
			print("point4")
			print("")


			if token == '' or role == '':
				encrypted_message = encryption.hsencrypt(tag, {"error": "Invalid login credentials"})
				return jsonify({"transfer":encrypted_message}), 400
			
			encrypted_message = encryption.hsencrypt(tag, {"token": token, "role": role, "uid": uid})
			return jsonify({"success": "Login complete", "transfer": encrypted_message}), 200

		except Exception as e:
			print(e)
			return jsonify({"error": str(e)}), 400

@app.route('/api/v1/logout', methods=['POST'])
def logout():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)

			encryption.public_keys.pop(data['token'], None)

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
				raise Exception("Could not get the requested branch data, likely an invalid id")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			print(e)
			return returnEncrypted(token, {"error": str(e)}, 400)

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

			print(retList)

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


			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getAllEmployeeData', methods=['POST'])
def getAllEmployeeData():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)
			result = sqlEmployee.get_all_data(token=data['token'])
			if result == None:
				raise Exception("Could not retreive requested Employee data")


			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getEmployeeDataByBranch', methods=['POST'])
def getEmployeeDataByBranch():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)
			result = sqlEmployee.get_all_data_by_branch(data["branch_id"], token=token)
			if result == None:
				raise Exception("Could not retreive requested Employee data")


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

@app.route('/api/v1/updateRegister', methods=['POST'])
def updateRegister():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlEmployee.Register.update(data["employee_id"], branch_id=data["branch_id"], position=data['position'], token=token)):
				raise Exception("Could not update Employee data")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		SISTERHOOD API ROUTES
###				C.R.U.D. & FIND

@app.route('/api/v1/createSisterhood', methods=['POST'])
def createSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlSisters.create(data["branch1"],data["branch2"],data["location"], data['access_code_1'], data['access_code_2'], token=token)):
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

@app.route('/api/v1/updateSisterhood', methods=['POST'])
def updateSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlSisters.update(data["sisterhood_id"], data["branch1"], data["branch2"], data["location"], token=token)):
				raise Exception("Could not update Sisterhood data")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/deleteSisterhood', methods=['POST'])
def deleteSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlSisters.delete(data["sisterhood_id"], token=token)):
				raise Exception("Failed to delete Sisterhood entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/findSisterhood', methods=['POST'])
def findSisterhood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlSisters.find(data["search"], token=token)
			if result == None:
				raise Exception("Could not find Sisterhood")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


###
### 		EMPLOYEE DISCOUNT API ROUTES
###				C.U.

@app.route('/api/v1/genDiscount', methods=['POST'])
def genDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			code = sqlEmployeeDiscounts.generate(data["employee_id"], token=token)

			return returnEncrypted(token, code, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/useDiscount', methods=['POST'])
def useDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlEmployeeDiscounts.check(data["code"], token=token)):
				raise Exception("Discount does not exist or has already been used")

			return returnEncrypted(token, {"success": "Discount code used"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		DISCOUNT API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createDiscount', methods=['POST'])
def createDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlDiscounts.create(data["branch_id"], data["tag"], data["code"], data["discount"], data["end_date"], token=token)):
				raise Exception("Could not create new Discount, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getDiscounts', methods=['POST'])
def getDiscounts():
	if request.method == 'POST':
		try:

			data = request.get_json(force=True)
			result = sqlDiscounts.get_all(token=data["token"])
			if result == None:
				raise Exception("Could not retreive Discounts from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/checkDiscount', methods=['POST'])
def checkDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlDiscounts.check(data["code"], token=token)
			print(result)
			if result == False:
				raise Exception("Discount invalid or expired")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


###
### 		RESERVATION API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createReservation', methods=['POST'])
def createReservation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlReservations.create(data['branch_id'], data['cus_name'], data['cus_number'], data['size'], data['requirements'], data['datetime'], token=token)):
				raise Exception("Could not create new Reservation, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getReservations', methods=['POST'])
def getReservations():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlReservations.get(data['branch_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Reservations from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/checkinReservation', methods=['POST'])
def checkinReservation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlReservations.checkin(data['reservation_id'], data['cus_number'], token=token)):
				raise Exception("Could not verify Reservation")

			return returnEncrypted(token, {"success": "Reservation verified"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/updateReservation', methods=['POST'])
def updateReservation():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			print(data)

			if(not sqlReservations.update(data['reservation_id'], data['cus_name'], data['cus_number'], data['size'], data['requirements'], data['datetime'], token=token)):
				raise Exception("Could not update Reservation")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/createAtSister', methods=['POST'])
def createAtSister():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlReservations.create_at_sister(data['branch_id'], data['cus_name'], data['cus_number'], data['size'], data['requirements'], data['datetime'], token=token)):
				raise Exception("Could not create new Reservation, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		STOCK API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createStock', methods=['POST'])
def createStock():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlStock.create(data['name'], data['max_stock'], data['price'], data['allergins'], token=token)):
				raise Exception("Could not create new Stock, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


@app.route('/api/v1/getStock', methods=['POST'])
def getStock():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			stock, allergins = sqlStock.get(data['stock_id'], token=token)
			if stock == None or allergins == None:
				raise Exception("Could not retreive Stock from database")

			return returnEncrypted(token, {"stock":stock, "allergins":allergins}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getStocks', methods=['POST'])
def getStocks():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlStock.get_all(token=data['token'])
			if result == None:
				raise Exception("Could not retreive Stocks from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/updateStock', methods=['POST'])
def updateStock():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlStock.update(data['stock_id'], data['name'], data['max_stock'], data['price'], data['allergins'], token=token)):
				raise Exception("Could not update Stock")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/deleteStock', methods=['POST'])
def deleteStock():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlStock.delete(data['stock_id'], token=token)):
				raise Exception("Failed to delete Stock entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		INVENTORY API ROUTES
###				C.R.U.D. & Setup

@app.route('/api/v1/setupInventory', methods=['POST'])
def setupInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlInventory.setup(data['branch_id'], token=token)):
				raise Exception("Could not create new Stock, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertions Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/createInventory', methods=['POST'])
def createInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlInventory.create(data['stock_id'], data['branch_id'], data['current_stock'], token=token)):
				raise Exception("Could not create new Inventory, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getInventory', methods=['POST'])
def getInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlInventory.get(data['branch_id'], data['stock_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Inventory from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getInventoryLst', methods=['POST'])
def getInventoryLst():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlInventory.get_all(branch_id=data['branch_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Inventory from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/updateInventory', methods=['POST'])
def updateInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlInventory.update(data['branch_id'], data['stock_id'], data['current_stock'], token=token)):
				raise Exception("Could not update Inventory")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/deleteInventory', methods=['POST'])
def deleteInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlInventory.delete(data['branch_id'], data['stock_id'], token=token)):
				raise Exception("Failed to delete Inventory entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/addInventory', methods=['POST'])
def addInventory():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlInventory.add(data['branch_id'], data['stock_id'], data['addition'], token=token)):
				raise Exception("Could not add to Inventory")

			return returnEncrypted(token, {"success": "Inventory Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


###
### 		FOOD API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createFood', methods=['POST'])
def createFood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlFood.create(data['category'], data['name'], data['description'], data['main'], data['type'], data['price'], data['ingredients'], token=token)):
				raise Exception("Could not create new Food, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getFoods', methods=['POST'])
def getFoods():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlFood.get_all(token=data['token'])
			if result == None:
				raise Exception("Could not retreive Foods from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getFood', methods=['POST'])
def getFood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			food, ingredients = sqlFood.get(data['food_id'], token=token)
			if food == None or ingredients == None:
				raise Exception("Could not retreive Food from database")

			return returnEncrypted(token, {"food": food, "ingredients": ingredients}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/updateFood', methods=['POST'])
def updateFood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlFood.update(data['food_id'], data['category'], data['name'], data['description'], data['main'], data['type'], data['price'], data['ingredients'], token=token)):
				raise Exception("Could not update Food")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/deleteFood', methods=['POST'])
def deleteFood():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlFood.delete(data['food_id'], token=token)):
				raise Exception("Failed to delete Food entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		DRINK API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createDrink', methods=['POST'])
def createDrink():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlDrink.create(data['category'], data['name'], data['description'], data['id_req'], data['alc_perc'], data['prices'], data['ingredients'], token=token)):
				raise Exception("Could not create new Drink, likely duplicate entry")
			
			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getDrinks', methods=['POST'])
def getDrinks():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlDrink.get_all(token=data['token'])
			if result == None:
				raise Exception("Could not retreive Drinks from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getDrink', methods=['POST'])
def getDrink():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			drink, prices, ingredients = sqlDrink.get(data['drink_id'], token=token)
			if drink == None or ingredients == None:
				raise Exception("Could not retreive Drink from database")

			return returnEncrypted(token, {"drink": drink, "prices":prices, "ingredients": ingredients}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/updateDrink', methods=['POST'])
def updateDrink():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlDrink.update(data['drink_id'], data['category'], data['name'], data['description'], data['id_req'], data['alc_perc'], data['prices'], data['ingredients'], token=token)):
				raise Exception("Could not update Drink")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/deleteDrink', methods=['POST'])
def deleteDrink():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlDrink.delete(data['drink_id'], token=token)):
				raise Exception("Failed to delete Drink entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
###
### 		ALLERGINS API ROUTES
###				C.R.U.D.

@app.route('/api/v1/createAllergin', methods=['POST'])
def createAllergin():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlAllergins.create(data['name'], token=token)):
				raise Exception("Could not create new Allergin, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getAllergins', methods=['POST'])
def getAllergins():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlAllergins.get_all(token=data['token'])
			if result == None:
				raise Exception("Could not retreive Allergins from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)
		
@app.route('/api/v1/getAllergin', methods=['POST'])
def getAllergin():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlAllergins.get(data['allergin_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Allergin from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/updateAllergin', methods=['POST'])
def updateAllergin():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlAllergins.update(data['allergin_id'], data['name'], token=token)):
				raise Exception("Could not update Allergin")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/deleteAllergin', methods=['POST'])
def deleteAllergin():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlAllergins.delete(data['allergin_id'], token=token)):
				raise Exception("Failed to delete Allergin entry")

			return returnEncrypted(token, {"success": "Entry deletion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		ORDERS API ROUTES
###				C.R.U.D. & Find

@app.route('/api/v1/createOrder', methods=['POST'])
def createOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlOrders.create(data['branch_id'], data['discount'], data['drinks'], data['food'], data['delivery'], token=token)):
				raise Exception("Could not create new Order, likely duplicate entry")

			return returnEncrypted(token, {"success": "Table Insertion Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getOrders', methods=['POST'])
def getOrders():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlOrders.get_all(data['branch_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Orders from database")
			
			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/getUnservedOrders', methods=['POST'])
def getUnservedOrders():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlOrders.get_unserved(data['branch_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Orders from database")
			
			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getOrder', methods=['POST'])
def getOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlOrders.get(data['order_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Order from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/updateOrder', methods=['POST'])
def updateOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlOrders.update(data['order_id'], data['drinks'], data['food'], token=token)):
				raise Exception("Could not update Order")

			return returnEncrypted(token, {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/serveOrder', methods=['POST'])
def serveOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlOrders.serve(data['order_id'], token=token)):
				raise Exception("Could not serve Order")

			return returnEncrypted(token, {"success": "Order Served"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/unserveOrder', methods=['POST'])
def unserveOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if(not sqlOrders.unserve(data['order_id'], token=token)):
				raise Exception("Could not unserve Order")

			return returnEncrypted(token, {"success": "Order unserved"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		
@app.route('/api/v1/findOrder', methods=['POST'])
def findOrder():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlOrders.find(data['branch_id'], data['drink'], data['food'], token=token)
			if result == None:
				raise Exception("Could not find Order")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getMenu', methods=['POST'])
def getMenu():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlMenu.get(data['branch_id'], data['category'], token=token)
			if result == None:
				raise Exception("Could not retreive Menu from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)


###
### 		Manager Discount API ROUTES
###				C.R.U.D.

@app.route('/api/v1/checkManagerDiscount', methods=['POST'])
def checkManagerDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			if( not sqlManger.discount(data['branch_id'], data['code'], token=token)):
				raise Exception("Discount code invalid or expired")
			

			return returnEncrypted(token, {"success": "Discount Code Accepted"}, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

@app.route('/api/v1/getManagerDiscount', methods=['POST'])
def getManagerDiscount():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlManger.get(data['branch_id'], token=token)
			if result == None:
				raise Exception("Could not retreive Discounts from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)
		

@app.route('/api/v1/updateManagerDiscount', methods=['POST'])
def updateManagerDiscount():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			if(not sqlManger.update(token=data['token'])):
				raise Exception("Could not update Discount")

			return returnEncrypted(data['token'], {"success": "Table Update Complete"}, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/getCategories', methods=['POST'])
def getCategories():
	if request.method == 'POST':
		try:
			data = request.get_json(force=True)

			result = sqlMenu.get_categories(token=data['token'])
			if result == None:
				raise Exception("Could not retreive Categories from database")

			return returnEncrypted(data['token'], result, 200)
		except Exception as e:
			return returnEncrypted(data['token'], {"error": str(e)}, 400)

@app.route('/api/v1/listDateReservations', methods=['POST'])
def listDateReservations():
	if request.method == 'POST':
		try:
			data, token = decryptRecieved(request)

			result = sqlReservations.list_date(data['branch_id'], data['date'], token=token)
			if result == None:
				raise Exception("Could not retreive Reservations from database")

			return returnEncrypted(token, result, 200)
		except Exception as e:
			return returnEncrypted(token, {"error": str(e)}, 400)

###
### 		MAIN
###

if __name__ == '__main__':
	app.run(debug=True)
	print("tuh")