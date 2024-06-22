from Crypto.Cipher import AES
import base64
import os
import json

class Enigma:
	def __init__(self, key):
		self.iv = os.urandom(16)
		self.cypher = AES.new(key, AES.MODE_CBC, self.iv)

	def __pad(self, s):
		return s + b'\0' * (AES.block_size - len(s) % AES.block_size)
	
	def __unpad(self, s):
		return s.rstrip(b'\0')

	def __toString(self, data):
		return json.dumps(data)
	
	def __toDict(self, data):
		return json.loads(data)

	def set_key(self, key):
		self.cipher = AES.new(key, AES.MODE_CBC, self.iv)

	def encrypt(self, data):
		paddedMessage = self.__pad(self.__toString(data).encode('utf-8'))
		encryptedMessage = self.cipher.encrypt(self.iv + paddedMessage)
		return base64.b64encode(encryptedMessage)

	def decrypt(self, message):
		encryptedMessage = base64.b64decode(message)
		decryptedMessage = self.cipher.decrypt(encryptedMessage[self.iv:])
		return self.__toDict(self.__unpad(decryptedMessage))
