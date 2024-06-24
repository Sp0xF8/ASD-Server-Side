
import os
from mysql.connector import Error as sqlError
from mysql.connector import pooling
from dotenv import load_dotenv

##import random for generating random numbers
import random

## import sha-256 for password hashing
import hashlib
import time
from datetime import datetime
import os


load_dotenv()
script_dir = os.path.dirname(os.path.abspath(__file__))

number_of_restraunts = 5

pool = pooling.MySQLConnectionPool(
	pool_name="HRCons",
	pool_size=number_of_restraunts,
	user=os.getenv("MYSQL_USER"),
	host=os.getenv("MYSQL_HOST"),
	password=os.getenv("MYSQL_PASS"),
	database=os.getenv("MYSQL_DABA")

)

def check_auth(func):
	def wrapper(*args, **kwargs):
		try:
			if 'token' not in kwargs:
				raise ValueError("Token is required to access this function.")

			token = kwargs.pop('token')

			if (sqlAuth.check_token(token=token) != 2):
				raise ValueError("Token is invalid.")
			
			sqlAuth.update_token(token)

			return func(*args, **kwargs)

		except sqlError as e:
			print("sqlError", str(e))
			return {"sql error:": str(e)}
		except Exception as e:
			print("Error in check_auth: ", e)
			return {"error": str(e)}
		
		

	return wrapper

class sqlAuth:

	def create_token(user_id) -> str:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			token = hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()
			
			cursor.execute("INSERT INTO tblTokens (employee_id, token) VALUES (%s, %s)", [user_id, token])
			cnx.commit()

			return token

		except sqlError as e:
			print("Error creating token: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	def delete_token(token) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblTokens WHERE token = %s", [token])
			cnx.commit()


			if(os.path.exists(os.path.join(script_dir, "../keys/" + token + ".pem"))):
				os.remove(os.path.join(script_dir, "../keys/" + token + ".pem"))
				print("Token file deleted")

			return True

		except sqlError as e:
			print("Error deleting token: ", e)
			return e

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	def check_token(token) -> int:
		try:
			print("Checking token: ", token)
			if token == '':
				return 0
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblTokens WHERE token = %s", [token])

			if cursor.rowcount == 0:
				return 0

			tokenret = cursor.fetchone()

			timestamp = tokenret[3] #datetime.datetime timestamp

			if (datetime.now() - timestamp).seconds > 3600:
				print("Token expired")
				sqlAuth.delete_token(token)
				return 1
			
			print("Token is Valid")
			
			return 2
		
		except sqlError as e:
			print("Error checking token: ", e)
			return e

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	def __get_token(employee_id) -> str:
		try:
			print("Getting token: ", employee_id)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblTokens WHERE employee_id = %s", [employee_id])

			if cursor.rowcount == 0:
				return ''
			
			token = cursor.fetchone()
			return token[2]

		except TypeError as e:
			print("Token not found: User does not yet have a token")
			return ''

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	def update_token(token) -> bool:
		try:
			print("Updating token: ", token)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE tblTokens SET created_at = %s WHERE token = %s", [datetime.now(), token])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error updating token: ", e)
			return False
		
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	def login(email, password) -> str:
		try:


			print("Logging in: ", email)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblEmployees WHERE email = %s AND password = %s", [email, password])
			
			if cursor.rowcount == 0:
				return ''
			
			user = cursor.fetchone()
			print("User found: ", user[3])

			token = sqlAuth.__get_token(user[0])

			token_exists = True if token != '' else False
			
			print("Token exists: ", token_exists)

			if token_exists:
				print("Token exists, deleting")
				sqlAuth.delete_token(token)

			print("Creating new token")

			token = sqlAuth.create_token(user[0])
			return token
			
		except sqlError as e:
			print("Error logging in: ", e)
			return 

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlBranch:

	@check_auth
	def create(name) -> bool:

		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblBranches (name) VALUES (%s)", [name])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error inserting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_branches() -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblBranches")
			result = cursor.fetchall()
			return result

		except sqlError as e:
			print("Error getting branches: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_branch(branch_id) -> dict:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblBranches WHERE id = %s", [branch_id])
			result = cursor.fetchone()
			return result

		except sqlError as e:
			print("Error getting branch: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(branch_id, name) -> bool:
		try:
			print("Updating branch: ", branch_id, name)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE tblBranches SET name = %s WHERE id = %s", [name, branch_id])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error updating branch: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(branch_id) -> bool:
		
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblBranches WHERE id = %s", [branch_id])
			cnx.commit()
			return True
		
		except sqlError as e:
			print("Error deleting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlLocation:

	@check_auth
	def create(city) -> bool:
		try:
			print("Creating location: ", city)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblLocations (city) VALUES (%s)", [city])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error inserting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_locations() -> list:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblLocations")
			result = cursor.fetchall()
			return result

		except sqlError as e:
			print("Error getting locations: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_location(location_id) -> dict:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblLocations WHERE id = %s", [location_id])
			result = cursor.fetchone()
			return result

		except sqlError as e:
			print("Error getting location: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(loc_id, city) -> bool:
		try:
			print("Updating Locatioin: ", loc_id, city)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE tblLocations SET city = %s WHERE id = %s", [city, loc_id])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error updating branch: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(location_id) -> bool:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblLocations WHERE id = %s", [location_id])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error deleting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlEmployee:

	@check_auth
	def create(first_name, last_name, email, password, branchID, position) -> bool:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblEmployees (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", [first_name, last_name, email, password])
			cursor.execute("INSERT INTO lnkEmployeeRegister (employee_id, branch_id, position) VALUES (%s, %s, %s)", [cursor.lastrowid, branchID, position])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error inserting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()
	
	@check_auth
	def get_all() -> list:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblEmployees")
			result = cursor.fetchall()
			return result

		except sqlError as e:
			print("Error getting employees: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(employee_id) -> dict:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblEmployees WHERE id = %s", [employee_id])
			result = cursor.fetchone()
			return result

		except sqlError as e:
			print("Error getting employee: ", e)
			return None

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	@check_auth
	def update(employee_id, first_name, last_name, email, old_password, new_password=None) -> bool:

		try:
			print("updating")

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblEmployees WHERE id = %s AND password = %s", [employee_id, old_password])
			if cursor.rowcount == 0:
				return False
			
			print("employee valid")
			cursor.fetchall()

			cursor.execute("UPDATE tblEmployees SET first_name = %s, last_name = %s, email = %s WHERE id = %s", [first_name, last_name, email, employee_id])
			print("updated std")

			if not new_password == None:
				cursor.execute("UPDATE tblEmployees SET password = %s WHERE id = %s", [new_password, employee_id])

			cnx.commit()
			return True
		
		except sqlError as e:
			print("Error updating: ", e)
			return False
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(employee_id) -> bool:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblEmployees WHERE id = %s", [employee_id])
			cnx.commit()
			return True

		except sqlError as e:
			print("Error deleting: ", e)
			return False

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlSisters:
	@check_auth
	def create(branch1, branch2, location) -> bool:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblBranches (name) VALUES (%s), (%s)", [branch1, branch2])

			cursor.execute("INSERT INTO tblLocations (city) VALUES (%s)", [location])
			

			cursor.execute("SELECT LAST_INSERT_ID()")
			if cursor.rowcount == 0:
				return False
			location_id = cursor.fetchone()[0]

			cursor.execute("SELECT id FROM tblBranches ORDER BY id DESC LIMIT 2")
			if cursor.rowcount == 0:
				return False
			ids = cursor.fetchall()


			cursor.execute("INSERT INTO lnkSisterBranches (branch_id_1, branch_id_2, location_id) VALUES (%s, %s, %s)", [ids[0][0], ids[1][0], location_id])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error inserting: ", e)
			return False

	@check_auth
	def get_all() -> list:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("""SELECT 
								ls.id,
								b1.name AS branch1_name,
								b2.name AS branch2_name,
								l.city AS location_city
							FROM 
								lnkSisterBranches ls
							JOIN 
								tblBranches b1 ON ls.branch_id_1 = b1.id
							JOIN 
								tblBranches b2 ON ls.branch_id_2 = b2.id
							JOIN 
								tblLocations l ON ls.location_id = l.id;
				""")
			
			result = cursor.fetchall()

			print(result)
			return result
		
		except sqlError as e:
			print("Error getting sisters: ", e)
			return None
		
	@check_auth
	def get(sister_id) -> dict:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("""SELECT 
								ls.id,
								b1.name AS branch1_name,
								b2.name AS branch2_name,
								l.city AS location_city
							FROM 
								lnkSisterBranches ls
							JOIN 
								tblBranches b1 ON ls.branch_id_1 = b1.id
							JOIN 
								tblBranches b2 ON ls.branch_id_2 = b2.id
							JOIN 
								tblLocations l ON ls.location_id = l.id
							WHERE
				  			ls.id = %s;
				""", [sister_id])
			
			if cursor.rowcount == 0:
				raise Exception("Sister does not exist")

			result = cursor.fetchone()
			return result

		except sqlError as e:
			print("Error getting sisters: ", e)
			return None
		except Exception as e:
			print("Error getting sisters: ", e)
			return None
		



