
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

			if 'access_level' not in kwargs:
				access_level = ["Manager"]
			else:
				access_level = kwargs.pop('access_level')

			token = kwargs.pop('token')


			if (sqlAuth.check_token(token=token) != 2):
				raise ValueError("Token is invalid.")

			sqlAuth.update_token(token)

			sqlAuth.check_access(token=token, access_level=access_level)

			return func(*args, **kwargs)
		except Exception as e:
			print("Error in check_auth: ", e)
			raise Exception(e)



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

			user = cursor.fetchone()
			if user == None:
				return '', ''

			print("User found: ", user[3])

			cursor.execute("SELECT position FROM lnkEmployeeRegister WHERE employee_id = %s", [user[0]])
			position = cursor.fetchone()[0]

			token = sqlAuth.__get_token(user[0])

			token_exists = True if token != '' else False

			print("Token exists: ", token_exists)

			if token_exists:
				print("Token exists, deleting")
				sqlAuth.delete_token(token)

			print("Creating new token")

			token = sqlAuth.create_token(user[0])
			return token, position

		except sqlError as e:
			print("Error logging in: ", e)
			return

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	def check_access(token, access_level=["Manager"]) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT position FROM lnkEmployeeRegister WHERE employee_id = (SELECT employee_id FROM tblTokens WHERE token = %s)", [token])

			position = cursor.fetchone()[0]

			if position in access_level:
				return True
			else:
				raise Exception("Access Denied")
		except Exception as e:
			print("Error checking access: ", e)
			raise Exception(e)

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

	class Register:

		@check_auth
		def update(employee_id, branch_id, position) -> bool:
			try:
				cnx = pool.get_connection()
				cursor = cnx.cursor()

				if branch_id != 0:
					cursor.execute("UPDATE lnkEmployeeRegister SET branch_id = %s WHERE employee_id = %s", [branch_id, employee_id])
					if cursor.rowcount == 0:
						raise Exception("Branch does not exist")

				if position != "":
					cursor.execute("UPDATE lnkEmployeeRegister SET position = %s WHERE employee_id = %s", [position, employee_id])
					if cursor.rowcount == 0:
						raise Exception("Position does not exist")

				cnx.commit()
				return True
			except sqlError as e:
				print("Error updating: ", e)
				raise Exception(e)
			except Exception as e:
				print("Error updating: ", e)
				raise Exception(e)
			finally:
				if cursor:
					cursor.close()
				if cnx:
					cnx.close()

class sqlEmployeeDiscounts:

	@check_auth
	def generate(employee_id) -> str:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()


			cursor.execute("SELECT code FROM tblEmployeeDiscounts WHERE employee_id = %s AND used = 0", [employee_id])
			code = cursor.fetchall()
			if cursor.rowcount == 0:
				print("Creating new discount")
				code = hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()

				cursor.execute("INSERT INTO tblEmployeeDiscounts (employee_id, code) VALUES (%s, %s)", [employee_id, code])

				if cursor.rowcount == 0:
					raise Exception("Discount could not be created")

				cnx.commit()

				return code

			return code[0][0]



		except sqlError as e:
			print("Error creating discount: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error creating discount: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def check(code) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblEmployeeDiscounts WHERE code = %s AND used = 0", [code])

			if cursor.rowcount == 0:
				return False


			discount = cursor.fetchone()

			cursor.execute("UPDATE tblEmployeeDiscounts SET used = 1 WHERE id = %s", [discount[0]])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error checking discount: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error checking discount: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlDiscounts:

	@check_auth
	def create(branch_id, tag, code, discount, end) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblDiscounts (branch_id, tag, code, discount, end_date) VALUES (%s, %s, %s, %s, %s)", [branch_id, tag, code, discount, end])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating discount: ", e)
			if e.errno == 1062:
				raise Exception("Discount already exists")
			if e.errno == 1452:
				raise Exception("Branch does not exist")

		except Exception as e:
			print("Error creating discount: ", e)
			raise Exception(e)
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
			cursor.execute("SELECT * FROM tblDiscounts")
			result = cursor.fetchall()

			retlist = []
			for res in result:
				reslist = list(res)

				reslist[5] = reslist[5].strftime("%Y-%m-%d")
				retlist.append([reslist[0], reslist[1], reslist[2], reslist[3], reslist[4], reslist[5]])

			return retlist
		except sqlError as e:
			print("Error getting discounts: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting discounts: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	@check_auth
	def check(code) -> float:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			current_date = datetime.now().strftime("%Y-%m-%d")
			cursor.execute("SELECT * FROM tblDiscounts WHERE code = %s AND end_date >= %s", [code, current_date])

			result = cursor.fetchone()
			if result == None:
				raise Exception("Discount does not exist or has expired")

			return result[4]

		except Exception as e:
			print("Error checking discount: ", e)
			raise Exception(e)
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

	@check_auth
	def update(sister_id, branch1:str, branch2:str, location:str) -> bool:
		try:

			print(branch1, branch2, location)
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			cursor.execute("SELECT * FROM lnkSisterBranches WHERE id = %s", [sister_id])
			if cursor.rowcount == 0:
				raise Exception("Sister does not exist")
			cursor.fetchall()

			if branch1 != "":
				print("updating branch 1")
				cursor.execute("UPDATE lnkSisterBranches SET branch_id_1 = (SELECT id FROM tblBranches WHERE name = %s) WHERE id = %s", [branch1, sister_id])
				if cursor.rowcount == 0:
					raise Exception("Branch 1 does not exist")


			if branch2 != "":
				print("updating branch 2")
				cursor.execute("UPDATE lnkSisterBranches SET branch_id_2 = (SELECT id FROM tblBranches WHERE name = %s) WHERE id = %s", [branch2, sister_id])
				if cursor.rowcount == 0:
					raise Exception("Branch 2 does not exist")

			if location != "":
				print("updating location")
				cursor.execute("UPDATE lnkSisterBranches SET location_id = (SELECT id FROM tblLocations WHERE city = %s) WHERE id = %s", [location, sister_id])
				if cursor.rowcount == 0:
					raise Exception("Branch 2 does not exist")

			cnx.commit()
			return True

		except sqlError as e:
			print(e)
			raise Exception(e)

		except Exception as e:
			print("Error updating: ", e)
			raise Exception(e)

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(sister_id) -> bool:

		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			cursor.execute("SELECT * FROM lnkSisterBranches WHERE id = %s", [sister_id])
			if cursor.rowcount == 0:
				raise Exception("Sister does not exist")

			sister = cursor.fetchone()

			cursor.execute("DELETE FROM lnkSisterBranches WHERE id = %s", [sister_id])
			if cursor.rowcount == 0:
				raise Exception("Sister could not be deletes")

			cursor.execute("DELETE FROM tblBranches WHERE id = (%s)", [sister[1]])
			if cursor.rowcount == 0:
				raise Exception("Branche could not be deleted")

			cursor.execute("DELETE FROM tblBranches WHERE id = (%s)", [sister[2]])
			if cursor.rowcount == 0:
				raise Exception("Branche could not be deleted")

			cursor.execute("DELETE FROM tblLocations WHERE id = %s", [sister[3]])
			if cursor.rowcount == 0:
				raise Exception("Location could not be deleted")
			cnx.commit()

			return True
		except sqlError as err:
			print(f"Error: {err}")
			if cnx:
				cnx.rollback()
			raise
		except Exception as e:
			print(f"Error: {e}")
			if cnx:
				cnx.rollback()
			raise
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def find(search) -> dict:
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
				  			b1.name = %s OR b2.name = %s OR l.city = %s;
				""", [search, search, search])

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
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlReservations:

	@check_auth
	def create(branch_id, cus_name, cus_number, size, requirements, datetime) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblReservations (branch_id, cus_name, cus_number, size, requirements, datetime) VALUES (%s, %s, %s, %s, %s, %s)", [branch_id, cus_name, cus_number, size, requirements, datetime])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating reservation: ", e)

			if e.errno == 1452:
				raise Exception("Branch does not exist")

			if e.errno == 1062:
				raise Exception("Reservation already exists")

			raise Exception(e)
		except Exception as e:
			print("Error creating reservation: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(branch_id) -> list:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblReservations WHERE branch_id = %s", [branch_id])
			if cursor.rowcount == 0:
				raise Exception("No reservations found")
			result = cursor.fetchall()

			retlist = []
			for res in result:
				reslist = list(res)
				print(reslist)

				reslist[6] = reslist[6].strftime("%Y-%m-%d %H:%M:%S")
				retlist.append([reslist[0], reslist[1], reslist[2], reslist[3], reslist[4], reslist[5], reslist[6]])

			cnx.commit()

			return retlist
		except sqlError as e:
			print("Error getting reservations: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting reservations: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def checkin(reservation_id, phone_number) -> bool:
		try:

			print("Verifying reservation: ", reservation_id, phone_number)
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblReservations WHERE id = %s AND cus_number = %s", [reservation_id, phone_number])
			cursor.fetchall()

			if cursor.rowcount == 0:
				raise Exception("Reservation does not exist")


			cursor.execute("DELETE FROM tblReservations WHERE id = %s", [reservation_id])

			cnx.commit()

			return True
		except sqlError as e:
			print("Error verifying reservation: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error verifying reservation: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(reservation_id, cus_name, cus_number, size, requirements, datetime) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			if cus_name != '':
				cursor.execute("UPDATE tblReservations SET cus_name = %s WHERE id = %s", [cus_name, reservation_id])
				print("Updated name")

			if cus_number != '':
				cursor.execute("UPDATE tblReservations SET cus_number = %s WHERE id = %s", [cus_number, reservation_id])
				print("Updated number")

			if size != 0:
				cursor.execute("UPDATE tblReservations SET size = %s WHERE id = %s", [size, reservation_id])
				print("Updated size")

			if requirements != '':
				cursor.execute("UPDATE tblReservations SET requirements = %s WHERE id = %s", [requirements, reservation_id])
				print("Updated requirements")

			if datetime != '':
				cursor.execute("UPDATE tblReservations SET datetime = %s WHERE id = %s", [datetime, reservation_id])
				print("Updated datetime")

			cnx.commit()

			return True
		except sqlError as e:
			print("Error updating reservation: ", e)
			if e.errno == 1452:
				raise Exception("Reservation does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error updating reservation: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlStock:

	@check_auth
	def create(name, max, price, allergins) -> bool:
		try:

			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblStock (name, max_stock, price) VALUES (%s, %s, %s)", [name, max, price])

			if cursor.rowcount == 0:
				raise Exception("Stock could not be created")

			if allergins == []:
				cnx.commit()
				return True

			cursor.execute("SELECT LAST_INSERT_ID()")

			stock_id = cursor.fetchone()[0]

			for allergin in allergins:
				cursor.execute("INSERT INTO lnkStockAllergins (stock_id, allergin_id) VALUES (%s, %s)", [stock_id, allergin])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating stock: ", e)
			if e.errno == 1062:
				raise Exception("Stock already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating stock: ", e)
			raise Exception(e)
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
			cursor.execute("SELECT * FROM tblStock")
			result = cursor.fetchall()
			return result
		except sqlError as e:
			print("Error getting stock: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting stock: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(stock_id) -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblStock WHERE id = %s", [stock_id])
			stock = cursor.fetchone()
			if stock == None:
				raise Exception("Stock does not exist")

			cursor.execute("SELECT a.id, a.allergin FROM lnkStockAllergins sa JOIN tblAllergins a ON sa.allergin_id = a.id WHERE sa.stock_id = %s ", [stock_id])
			allergins = cursor.fetchall()

			if allergins == None:
				allergins = []

			return stock, allergins
		except sqlError as e:
			print("Error getting stock: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting stock: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(stock_id, name, max, price, allergins) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			if name != '':
				cursor.execute("UPDATE tblStock SET name = %s WHERE id = %s", [name, stock_id])
				if cursor.rowcount == 0:
					raise Exception("Stock not updated, possibly does not exist")

			if max != 0:
				cursor.execute("UPDATE tblStock SET max_stock = %s WHERE id = %s", [max, stock_id])
				print("Updated max")
				if cursor.rowcount == 0:
					raise Exception("Stock not updated, possibly does not exist")

			if price != 0.0:
				cursor.execute("UPDATE tblStock SET price = %s WHERE id = %s", [price, stock_id])
				print("Updated price")
				if cursor.rowcount == 0:
					raise Exception("Stock not updated, possibly does not exist")


			if allergins != []:
				cursor.execute("SELECT allergin_id FROM lnkStockAllergins WHERE stock_id = %s", [stock_id])
				old_allergins = cursor.fetchall()

				for allergin in allergins:
					if allergin not in old_allergins:
						print("Adding allergin: ", allergin)
						cursor.execute("INSERT INTO lnkStockAllergins (stock_id, allergin_id) VALUES (%s, %s)", [stock_id, allergin])

				for allergin in old_allergins:
					if allergin not in allergins:
						print("Deleting allergin: ", allergin)
						cursor.execute("DELETE FROM lnkStockAllergins WHERE stock_id = %s AND allergin_id = %s", [stock_id, allergin])


			cnx.commit()
			return True
		except Exception as e:
			print("Error updating stock: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(stock_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblStock WHERE id = %s", [stock_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Stock does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting stock: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlInventory:

	@check_auth
	def create(stock_id, branch_id, current_stock) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO lnkInventory (stock_id, branch_id, current_stock) VALUES (%s, %s, %s)", [stock_id, branch_id, current_stock])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating inventory: ", e)
			if e.errno == 1062:
				raise Exception("Inventory already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_all(branch_id) -> list:
		try:
			print("Getting inventory")
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT s.id, s.name, i.current_stock FROM lnkInventory i JOIN tblStock s ON i.stock_id = s.id WHERE i.branch_id = %s", [branch_id])
			result = cursor.fetchall()
			return result
		except sqlError as e:
			print("Error getting inventory: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(branch_id, stock_id) -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT i.stock_id, s.name, i.current_stock FROM lnkInventory i JOIN tblStock s ON i.stock_id = s.id WHERE i.branch_id = %s AND i.stock_id = %s", [branch_id, stock_id])
			result = cursor.fetchone()
			if result == None:
				raise Exception("Inventory does not exist")

			return result
		except sqlError as e:
			print("Error getting inventory: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(branch_id, stock_id, current_stock) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE lnkInventory SET current_stock = %s WHERE stock_id = %s AND branch_id = %s", [current_stock, stock_id, branch_id])
			if cursor.rowcount == 0:
				raise Exception("Item does not exist")

			cnx.commit()
			return True
		except Exception as e:
			print("Error updating inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	@check_auth
	def add(branch_id, stock_id, addition) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE lnkInventory SET current_stock = current_stock + %s WHERE stock_id = %s AND branch_id = %s", [addition, stock_id, branch_id])
			if cursor.rowcount == 0:
				raise Exception("Item does not exist")

			cnx.commit()
			return True
		except Exception as e:
			print("Error updating inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(branch_id, stock_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM lnkInventory WHERE stock_id = %s AND branch_id = %s", [stock_id, branch_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Inventory does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def setup(branch_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblStock")
			stocks = cursor.fetchall()

			for stock in stocks:

				try:
					cursor.execute("INSERT INTO lnkInventory (stock_id, branch_id, current_stock) VALUES (%s, %s, 0)", [stock[0], branch_id])
				except sqlError as e:
					if e.errno == 1062:
						print("Iventory item already exists for this branch, skipping item ", stock[1])
						continue
					if e.errno == 1452:
						raise Exception("Branch does not exist")

					raise Exception(e)
			cnx.commit()
			return True
		except Exception as e:
			print("Error setting up inventory: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlFood:

	@check_auth
	def create(category, name, description, main, type, price, ingredients) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblFoods (category, name, description, main, type, price) VALUES (%s, %s, %s, %s, %s, %s)", [category, name, description, main, type, price])

			if cursor.rowcount == 0:
				raise Exception("Food could not be created")

			cursor.execute("SELECT LAST_INSERT_ID()")
			food_id = cursor.fetchone()[0]

			for ingredient in ingredients:
				try:
					cursor.execute("INSERT INTO lnkFoodIngredients (food_id, stock_id, count_req) VALUES (%s, %s, %s)", [food_id, ingredient[0], ingredient[1]])
				except sqlError as e:
					if e.errno == 1062:
						print("Ingredient already exists, skipping")
						continue
					if e.errno == 1452:
						cnx.rollback()
						raise Exception(f"Ingredient does not exist: {ingredient[0]}")
					raise Exception(e)


			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating food: ", e)
			if e.errno == 1062:
				raise Exception("Food already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating food: ", e)
			raise Exception(e)
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
			cursor.execute("SELECT * FROM tblFoods")
			result = cursor.fetchall()
			return result
		except sqlError as e:
			print("Error getting food: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting food: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(food_id) -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblFoods WHERE id = %s", [food_id])
			result = cursor.fetchone()
			if result == None:
				raise Exception("Food does not exist")

			cursor.execute("SELECT s.id, s.name, i.count_req FROM lnkFoodIngredients i JOIN tblStock s ON i.stock_id = s.id WHERE i.food_id = %s", [food_id])
			ingredients = cursor.fetchall()
			if ingredients == None:
				raise Exception("Ingredients not found")

			return result, ingredients
		except sqlError as e:
			print("Error getting food: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting food: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(food_id, category, name, description, main, type, price, ingredients) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			if category != '':
				cursor.execute("UPDATE tblFoods SET category = %s WHERE id = %s", [category, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if name != '':
				cursor.execute("UPDATE tblFoods SET name = %s WHERE id = %s", [name, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if description != '':
				cursor.execute("UPDATE tblFoods SET description = %s WHERE id = %s", [description, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if main != '':
				cursor.execute("UPDATE tblFoods SET main = %s WHERE id = %s", [main, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if type != '':
				cursor.execute("UPDATE tblFoods SET type = %s WHERE id = %s", [type, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if price != 0.0:
				cursor.execute("UPDATE tblFoods SET price = %s WHERE id = %s", [price, food_id])
				if cursor.rowcount == 0:
					raise Exception("Food not updated, possibly does not exist")

			if ingredients != []:
				cursor.execute("SELECT stock_id FROM lnkFoodIngredients WHERE food_id = %s", [food_id])
				old_ingredients = cursor.fetchall()


				for ingredient in ingredients:
					should_keep = False
					unseen = True
					delete_id = None
					for old_ingredient in old_ingredients:
						if ingredient[0] == old_ingredient[0]:
							should_keep = True
							unseen = False
							delete_id = old_ingredients.index(old_ingredient)
							print("Updating ingredient: ", ingredient[0])
							cursor.execute("UPDATE lnkFoodIngredients SET count_req = %s WHERE food_id = %s AND stock_id = %s", [ingredient[1], food_id, ingredient[0]])
							break
					if should_keep:
						old_ingredients.remove(old_ingredients[delete_id])

					if unseen:
						print("Inserting new ingredient: ", ingredient[0])
						cursor.execute("INSERT INTO lnkFoodIngredients (food_id, stock_id, count_req) VALUES (%s, %s, %s)", [food_id, ingredient[0], ingredient[1]])

				for ingredient in old_ingredients:
					print("Deleting ingredient: ", ingredient[0])
					cursor.execute("DELETE FROM lnkFoodIngredients WHERE food_id = %s AND stock_id = %s", [food_id, ingredient[0]])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error updating food: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error updating food: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(food_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblFoods WHERE id = %s", [food_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Food does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting food: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlDrink:

	@check_auth
	def create(category, name, description, req_id, alc_perc, prices, ingredients):
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblDrinks (category, name, description, req_id, alc_perc) VALUES (%s, %s, %s, %s, %s)", [category, name, description, req_id, alc_perc])

			if cursor.rowcount == 0:
				raise Exception("Drink could not be created")

			cursor.execute("SELECT LAST_INSERT_ID()")
			drink_id = cursor.fetchone()[0]

			for price in prices:
				cursor.execute("INSERT INTO lnkDrinkPrices (drink_id, type, price) VALUES (%s, %s, %s)", [drink_id, price[0], price[1]])

			for ingredient in ingredients:
				cursor.execute("INSERT INTO lnkDrinkIngredients (drink_id, stock_id, count_req) VALUES (%s, %s, %s)", [drink_id, ingredient[0], ingredient[1]])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating drink: ", e)
			if e.errno == 1062:
				cnx.rollback()
				raise Exception("Drink already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating drink: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_all():
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblDrinks")
			result = cursor.fetchall()

			if cursor.rowcount == 0:
				raise Exception("No drinks found")

			return result
		except sqlError as e:
			print("Error getting drinks: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting drinks: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(drink_id):
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblDrinks WHERE id = %s", [drink_id])
			result = cursor.fetchone()

			if result == None:
				raise Exception("Drink does not exist")

			cursor.execute("SELECT type, price FROM lnkDrinkPrices WHERE drink_id = %s", [drink_id])
			prices = cursor.fetchall()

			cursor.execute("SELECT s.id, s.name, i.count_req FROM lnkDrinkIngredients i JOIN tblStock s ON i.stock_id = s.id WHERE i.drink_id = %s", [drink_id])
			ingredients = cursor.fetchall()

			return result, prices, ingredients
		except sqlError as e:
			print("Error getting drink: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting drink: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(drink_id, category, name, description, req_id, alc_perc, prices, ingredients):
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			if category != '':
				cursor.execute("UPDATE tblDrinks SET category = %s WHERE id = %s", [category, drink_id])
				if cursor.rowcount == 0:
					raise Exception("Drink not updated, possibly does not exist")

			if name != '':
				cursor.execute("UPDATE tblDrinks SET name = %s WHERE id = %s", [name, drink_id])
				if cursor.rowcount == 0:
					raise Exception("Drink not updated, possibly does not exist")

			if description != '':
				cursor.execute("UPDATE tblDrinks SET description = %s WHERE id = %s", [description, drink_id])
				if cursor.rowcount == 0:
					raise Exception("Drink not updated, possibly does not exist")

			if req_id != '':
				cursor.execute("UPDATE tblDrinks SET req_id = %s WHERE id = %s", [req_id, drink_id])
				if cursor.rowcount == 0:
					raise Exception("Drink not updated, possibly does not exist")

			if alc_perc != 0.0:
				cursor.execute("UPDATE tblDrinks SET alc_perc = %s WHERE id = %s", [alc_perc, drink_id])
				if cursor.rowcount == 0:
					raise Exception("Drink not updated, possibly does not exist")

			if prices != []:
				cursor.execute("SELECT type FROM lnkDrinkPrices WHERE drink_id = %s", [drink_id])
				old_prices = cursor.fetchall()

				for price in prices:
					should_keep = False
					unseen = True
					delete_id = None
					for old_price in old_prices:
						if price[0] == old_price[0]:
							should_keep = True
							unseen = False
							delete_id = old_prices.index(old_price)
							cursor.execute("UPDATE lnkDrinkPrices SET price = %s WHERE drink_id = %s AND type = %s", [price[1], drink_id, price[0]])
							break
					if should_keep:
						old_prices.remove(old_prices[delete_id])

					if unseen:
						cursor.execute("INSERT INTO lnkDrinkPrices (drink_id, type, price) VALUES (%s, %s, %s)", [drink_id, price[0], price[1]])

				for price in old_prices:
					cursor.execute("DELETE FROM lnkDrinkPrices WHERE drink_id = %s AND type = %s", [drink_id, price[0]])

			if ingredients != []:
				cursor.execute("SELECT stock_id FROM lnkDrinkIngredients WHERE drink_id = %s", [drink_id])
				old_ingredients = cursor.fetchall()

				for ingredient in ingredients:
					should_keep = False
					unseen = True
					delete_id = None
					for old_ingredient in old_ingredients:
						if ingredient[0] == old_ingredient[0]:
							should_keep = True
							unseen = False
							delete_id = old_ingredients.index(old_ingredient)
							cursor.execute("UPDATE lnkDrinkIngredients SET count_req = %s WHERE drink_id = %s AND stock_id = %s", [ingredient[1], drink_id, ingredient[0]])
							break
					if should_keep:
						old_ingredients.remove(old_ingredients[delete_id])

					if unseen:
						cursor.execute("INSERT INTO lnkDrinkIngredients (drink_id, stock_id, count_req) VALUES (%s, %s, %s)", [drink_id, ingredient[0], ingredient[1]])

				for ingredient in old_ingredients:
					cursor.execute("DELETE FROM lnkDrinkIngredients WHERE drink_id = %s AND stock_id = %s", [drink_id, ingredient[0]])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error updating drink: ", e)

			if e.errno == 1452:
				raise Exception("Drink does not exist")

			if e.errno == 1062:
				raise Exception("Drink already exists")

			raise Exception(e)

		except Exception as e:
			print("Error updating drink: ", e)
			raise Exception(e)

	@check_auth
	def delete(drink_id):
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblDrinks WHERE id = %s", [drink_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Drink does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting drink: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlAllergins:

	@check_auth
	def create(name) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblAllergins (allergin) VALUES (%s)", [name])
			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating allergin: ", e)
			if e.errno == 1062:
				raise Exception("Allergin already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating allergin: ", e)
			raise Exception(e)
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
			cursor.execute("SELECT * FROM tblAllergins")
			result = cursor.fetchall()
			return result
		except sqlError as e:
			print("Error getting allergins: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting allergins: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get(allergin_id) -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblAllergins WHERE id = %s", [allergin_id])
			result = cursor.fetchone()
			if result == None:
				raise Exception("Allergin does not exist")

			return result
		except sqlError as e:
			print("Error getting allergin: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting allergin: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(allergin_id, name) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("UPDATE tblAllergins SET allergin = %s WHERE id = %s", [name, allergin_id])
			if cursor.rowcount == 0:
				raise Exception("Allergin does not exist")

			cnx.commit()
			return True
		except sqlError as e:
			print("Error updating allergin: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error updating allergin: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def delete(allergin_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblAllergins WHERE id = %s", [allergin_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Allergin does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting allergin: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

class sqlOrders:

	@check_auth
	def create(branch_id, discount, drinks, food) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("INSERT INTO tblOrders (branch_id, discount) VALUES (%s, %s)", [branch_id, discount])

			if cursor.rowcount == 0:
				raise Exception("Order could not be created")

			cursor.execute("SELECT LAST_INSERT_ID()")
			order_id = cursor.fetchone()[0]

			for drink in drinks:
				try:
					cursor.execute("INSERT INTO lnkDrinkSales (order_id, item_id, type, quantity, timed_price) VALUES (%s, %s, %s, %s, (SELECT price FROM lnkDrinkPrices WHERE drink_id = %s AND type = %s))", [order_id, drink[0], drink[2], drink[1], drink[0], drink[2]])
				except sqlError as e:
					if e.errno == 1452:
						cnx.rollback()
						raise Exception(f"Drink does not exist: {drink[0]}")
					raise Exception(e)

			for foo in food:
				try:
					cursor.execute("INSERT INTO lnkFoodSales (order_id, item_id, quantity, timed_price) VALUES (%s, %s, %s, (SELECT price from tblFoods where id = %s))", [order_id, foo[0], foo[1], foo[0]])

				except sqlError as e:
					if e.errno == 1452:
						cnx.rollback()
						raise Exception(f"Food does not exist: {foo[0]}")
					raise Exception(e)

			cnx.commit()
			return True
		except sqlError as e:
			print("Error creating order: ", e)
			if e.errno == 1062:
				raise Exception("Order already exists")
			raise Exception(e)
		except Exception as e:
			print("Error creating order: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def get_all(branch_id) -> list:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("""
				SELECT 
					o.id AS order_id,
					o.created_at AS order_created_at,
					td.name AS drink_name,
					ds.quantity AS drink_quantity,
					tf.name AS food_name,
					fs.quantity AS food_quantity
				FROM 
					tblOrders o
				LEFT JOIN 
					lnkDrinkSales ds ON o.id = ds.order_id
				LEFT JOIN 
					tblDrinks td ON ds.item_id = td.id
				LEFT JOIN 
					lnkFoodSales fs ON o.id = fs.order_id
				LEFT JOIN 
					tblFoods tf ON fs.item_id = tf.id
				WHERE 
					o.branch_id = %s
				""", [branch_id])

			results = cursor.fetchall()
			if cursor.rowcount == 0:
				raise Exception("No orders found")

			returned_orders = {}
			for order_id, order_created_at, drink_name, drink_quantity, food_name, food_quantity in results:
				if order_id in returned_orders:
					returned_orders[order_id][2].add((drink_name, drink_quantity))
					returned_orders[order_id][3].add((food_name, food_quantity))
				else:
					returned_orders[order_id] = [
						order_id,
						order_created_at,
						{(drink_name, drink_quantity)},
						{(food_name, food_quantity)}
					]
			
			retlist = []
			for order in returned_orders:
				order = returned_orders[order]

				order[1] = order[1].strftime("%Y-%m-%d %H:%M:%S")
				order[2] = list(order[2])
				order[3] = list(order[3])
				retlist.append(order)

			return retlist
		except sqlError as e:
			print("Error getting orders: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting orders: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	@check_auth
	def get(order_id) -> dict:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblOrders WHERE id = %s", [order_id])
			result = cursor.fetchone()
			if result == None:
				raise Exception("Order does not exist")

			# Fetch drink sales details for the given order_id
			cursor.execute("SELECT od.item_id, od.quantity FROM lnkDrinkSales od JOIN tblDrinks d ON od.item_id = d.id WHERE od.order_id = %s", [order_id])
			drinks = cursor.fetchall()

			# Fetch food sales details for the given order_id
			cursor.execute("SELECT fs.item_id, fs.quantity FROM lnkFoodSales fs JOIN tblFoods f ON fs.item_id = f.id WHERE fs.order_id = %s", [order_id])
			food = cursor.fetchall()

			retlist = list(result)
			retlist[2] = retlist[2].strftime("%Y-%m-%d %H:%M:%S")



			return retlist, drinks, food
		except sqlError as e:
			print("Error getting order: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting order: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def update(order_id, drinks, food) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()

			if drinks != []:
				cursor.execute("SELECT drink_id FROM lnkOrderDrinks WHERE order_id = %s", [order_id])
				old_drinks = cursor.fetchall()

				for drink in drinks:
					should_keep = False
					unseen = True
					delete_id = None
					for old_drink in old_drinks:
						if drink[0] == old_drink[0]:
							should_keep = True
							unseen = False
							delete_id = old_drinks.index(old_drink)
							cursor.execute("UPDATE lnkOrderDrinks SET count = %s WHERE order_id = %s AND drink_id = %s", [drink[1], order_id, drink[0]])
							break
					if should_keep:
						old_drinks.remove(old_drinks[delete_id])

					if unseen:
						cursor.execute("INSERT INTO lnkOrderDrinks (order_id, drink_id, count) VALUES (%s, %s, %s)", [order_id, drink[0], drink[1]])

				for drink in old_drinks:
					cursor.execute("DELETE FROM lnkOrderDrinks WHERE order_id = %s AND drink_id = %s", [order_id, drink[0]])

			if food != []:
				cursor.execute("SELECT food_id FROM lnkOrderFood WHERE order_id = %s", [order_id])
				old_food = cursor.fetchall()

				for food in food:
					should_keep = False
					unseen = True
					delete_id = None
					for old_food in old_food:
						if food[0] == old_food[0]:
							should_keep = True
							unseen = False
							delete_id = old_food
							cursor.execute("UPDATE lnkOrderFood SET count = %s WHERE order_id = %s AND food_id = %s", [food[1], order_id, food[0]])
							break
					if should_keep:
						old_food.remove(old_food[delete_id])

					if unseen:
						cursor.execute("INSERT INTO lnkOrderFood (order_id, food_id, count) VALUES (%s, %s, %s)", [order_id, food[0], food[1]])

				for food in old_food:
					cursor.execute("DELETE FROM lnkOrderFood WHERE order_id = %s AND food_id = %s", [order_id, food[0]])

			cnx.commit()
			return True
		except sqlError as e:
			print("Error updating order: ", e)

			if e.errno == 1452:
				raise Exception("Order does not exist")

			if e.errno == 1062:
				raise Exception("Order already exists")

			raise Exception(e)
		except Exception as e:
			print("Error updating order: ", e)
			raise Exception(e)

		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


	@check_auth
	def delete(order_id) -> bool:
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("DELETE FROM tblOrders WHERE id = %s", [order_id])
			cnx.commit()
			return True
		except sqlError as e:
			if e.errno == 1452:
				raise Exception("Order does not exist")
			raise Exception(e)
		except Exception as e:
			print("Error deleting order: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()

	@check_auth
	def find(drink, food):
		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			cursor.execute("SELECT * FROM tblOrders WHERE id IN (SELECT order_id FROM lnkOrderDrinks WHERE drink_id = %s) OR id IN (SELECT order_id FROM lnkOrderFood WHERE food_id = %s) ORDER BY created_at DESC LIMIT 10", [drink, food])
			result = cursor.fetchall()

			return result
		except sqlError as e:
			print("Error finding orders: ", e)

			if e.errno == 1452:
				raise Exception("Order does not exist")
		except Exception as e:
			print("Error finding orders: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()


class sqlMenu:

	@check_auth
	def get(branch_id, category)-> list:

		try:
			cnx = pool.get_connection()
			cursor = cnx.cursor()
			
			drink = True if category == "Cocktail" or category == "Beers" or category == "Wines" or category == "Shots" or category == "Liqours" or category == "Soft" else False
			print("Category: ", category)
			print("Drink: ", drink)

			result = None

			if drink:
				cursor.execute("SELECT d.id AS item_id, d.name as item_name, d.description AS item_description, d.req_id AS require_id, d.alc_perc AS alcohol_percentage FROM tblDrinks d JOIN lnkDrinkIngredients di ON d.id = di.drink_id JOIN tblStock s ON di.stock_id = s.id JOIN lnkInventory i ON di.stock_id = i.stock_id WHERE category = %s AND i.branch_id = %s AND i.current_stock < (s.max_stock * 0.95)", [category, branch_id ])
				result = cursor.fetchall()
			# else:
			# 	cursor.execute("SELECT * FROM tblFoods WHERE category = %s", [category])
			# 	result = cursor.fetchall()

			if result == None:
				raise Exception("No items found")
				
			return result
		except sqlError as e:
			print("Error getting menu: ", e)
			raise Exception(e)
		except Exception as e:
			print("Error getting menu: ", e)
			raise Exception(e)
		finally:
			if cursor:
				cursor.close()
			if cnx:
				cnx.close()