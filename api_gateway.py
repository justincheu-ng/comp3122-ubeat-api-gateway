import flask
import jwt
import pymongo
import redis


##############################
# Init library / connections
##############################
flask_app = flask.Flask(__name__)
mongo_client = pymongo.MongoClient('mongodb://comp3122:23456@user_db:27017')
redis_conn = redis.Redis(host='message_queue', port=6379)


####################
# Define functions 
####################
def generate_token(user_info):
    return jwt.encode(user_info, "secretPassword", algorithm="HS256")


##########################
# Flask endpoints: login
##########################
@flask_app.route('/login', methods=['POST'])
def api_login():
    # Get login credentials
    username = flask.request.args.get('username')
    if not username:
        return {'error': 'username must be provided'}, 400
    password = flask.request.args.get('password')
    if not password:
        return {'error': 'password must be provided'}, 400
    username = username.lower()
    password = hash(password)

    # Get user information
    filter = {'username': username, 'password': password}
    db = mongo_client.user
    if result := db.customer.find_one(filter):
        user = {'id': result['id'], 'group': 'customer'}
    elif result := db.restaurant.find_one(filter):
        user = {'id': result['id'], 'group': 'restaurant'}
    elif result := db.delivery.find_one(filter):
        user = {'id': result['id'], 'group': 'delivery'}
    elif result := db.admin.find_one(filter):
        user = {'id': result['id'], 'group': 'admin'}
    else:
        return {'error': 'incorrect username or password'}, 404
    
    # Return token
    return {'token': generate_token(user)}, 200


#########################
# Flask endpoints: menu
#########################
@flask_app.route('/menu', methods=['GET'])
def get_menu():
    response = requests.get('http://menu:15000')
    return flask.jsonify(response.json()), response.status_code


##########################
# Start flask
##########################
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=15000)
    