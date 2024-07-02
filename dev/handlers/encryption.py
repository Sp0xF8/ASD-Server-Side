from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

import dotenv
import os
import json

dotenv.load_dotenv()
script_dir = os.path.dirname(os.path.abspath(__file__))

class Encryption:

	def __init__(self):
		self.private_key = self.load_private_key()
		self.public_key = self.private_key.public_key() if self.private_key else None

		if self.private_key is None:
			print("No private key found, creating new keys...")
			self.create_keys()


		self.public_keys = {}

		

	def load_private_key(self):
		try:
			with open(os.path.join(script_dir, "../keys/hrs/private_key.pem"), "rb") as key_file:
				private_key = serialization.load_pem_private_key(
					key_file.read(),
					password=None,  
					backend=default_backend()
				)
			return private_key
		except Exception as e:
			print(f"An error occurred while loading the private key: {e}")
			return None
		

	def load_public_key(self, token, keypath="../keys/"):
		try:
			
			fullkeypath = os.path.join(script_dir, keypath, token + ".pem")

			with open(fullkeypath, "rb") as key_file:
				public_key = serialization.load_pem_public_key(
					key_file.read(),
					backend=default_backend()
				)

			os.remove(fullkeypath)

			if keypath == "../keys/":
				self.public_keys[token] = public_key
				return True
			else:
				return public_key
		except Exception as e:
			print(f"An error occurred while loading the public key: {e}")
			return None



	def create_keys(self):
		self.private_key = rsa.generate_private_key(
			public_exponent=65537,
			key_size=4096,
		)

		self.public_key = self.private_key.public_key()

		os.makedirs(os.path.join(script_dir, "../keys/hrs/"), exist_ok=True)

		with open(os.path.join(script_dir, "../keys/hrs/private_key.pem"), "wb") as f:
			f.write(
				self.private_key.private_bytes(
					encoding=serialization.Encoding.PEM,
					format=serialization.PrivateFormat.TraditionalOpenSSL,
					encryption_algorithm=serialization.NoEncryption(),
				)
			)

		with open(os.path.join(script_dir, "../keys/hrs/public_key.pem"), "wb") as f:
			f.write(
				self.public_key.public_bytes(
					encoding=serialization.Encoding.PEM,
					format=serialization.PublicFormat.SubjectPublicKeyInfo,
				)
			)

	def __toString(self, data):
		string = json.dumps(data)
		return string

	def __toDict(self, data):
		return json.loads(data)

	def encrypt(self, token, dick):
		try:
			if token not in self.public_keys:
				if not self.load_public_key(token):
					return None
				
			if isinstance(dick, dict):
				message = self.__toString(dick)
			else:
				message = self.__toString({"data": dick})

			encMessage = self.public_keys[token].encrypt(
				message.encode(),
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None,
				)
			)


			return  {"transfer": encMessage.decode('latin1')}
		except Exception as e:
			print(f"An error occurred while encrypting the message: {e}")
			return None
		
	def hsencrypt(self, token, dick):
		try:
			
			enigma = self.load_public_key(token, "../keys/hs/")
				
				
			if isinstance(dick, dict):
				message = self.__toString(dick)
			else:
				message = self.__toString({"data": dick})

			encMessage = enigma.encrypt(
				message.encode(),
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None,
				)
			)


			return  {"transfer": encMessage.decode('latin1')}
		except Exception as e:
			print(f"An error occurred while encrypting the message: {e}")
			return None
	
	def decrypt(self, encrypted_message):


		decrypted_message = self.private_key.decrypt(
			encrypted_message,
			padding.OAEP(
				mgf=padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None,
			)
		)

		decDict = self.__toDict(decrypted_message)

		return decDict
	
