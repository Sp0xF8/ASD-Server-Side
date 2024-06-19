from flask import Flask, request, jsonify, session

app = Flask(__name__)

@app.route('/')
def home():
	return 'API IS LISTENING'


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

	

if __name__ == '__main__':

	app.run(debug=True)

	print("tuh")