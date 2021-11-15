import flask
import jwt
import pymongo
import redis
import requests


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

@flask_app.route('/menu/<restaurant_id>', methods=['GET'])
def get_a_menu(restaurant_id):
    response = requests.get('http://menu:15000/'+restaurant_id)
    return flask.jsonify(response.json()), response.status_code

@flask_app.route('/menu/<restaurant_id>/<food_id>', methods=['GET'])
def get_a_food(restaurant_id, food_id):
    response = requests.get('http://menu:15000/'+restaurant_id+'/'+food_id)
    return flask.jsonify(response.json()), response.status_code


@flask_app.route('/menu/<restaurant_id>', methods=['POST'])
def add_a_food(restaurant_id):
    food_name = flask.request.args.get('food_name')
    food_price = flask.request.args.get('food_price')
    if not food_name or not food_price:
        return {'error': 'provide food_name and food_price in path'}, 400
    response = requests.post('http://menu:15000/'+restaurant_id+'?food_name='+food_name+'&food_price='+food_price)
    return {'food_id': response.json()['food_id']}, 201

@flask_app.route('/menu/<restaurant_id>/<food_id>', methods=['DELETE'])
def delete_a_food(restaurant_id, food_id):
    response = requests.get('http://menu:15000/'+restaurant_id+'/'+food_id)
    if response.status_code == 404:
        return flask.jsonify(response.json()), response.status_code
    load = json.dumps({
        'restaurant_id': restaurant_id,
        'food_id': food_id
    })
    redis_conn.publish('menu_deleteFood', load)
    return '', 204


##########################
# Flask endpoints: order 
##########################
@flask_app.route('/order/<restaurant_id>', methods=['GET'])
def get_restaurant_order(restaurant_id):
    # Authentication token
    token = flask.request.args.get('token')
    if not token:
        return {'error': 'token is required'}, 401
    user = authenticate_token(token)
    if not user:
        return {'error': 'invalid token'}, 403
    if user['group'] != 'restaurant':
        return {'error': 'you do not have the permission to perform this request'}, 403
    if user['id'] != int(restaurant_id):
        return {'error': 'you do not have the permission to perform this request'}, 403
    
    # Perform request
    response = requests.get('http://restaurant_order:15000/'+restaurant_id)
    return flask.jsonify(response.json()), response.status_code


##########################
# Start flask
##########################
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=15000)
    