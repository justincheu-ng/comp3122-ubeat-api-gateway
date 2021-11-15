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
def hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def generate_token(user_info):
    return jwt.encode(user_info, "secretPassword", algorithm="HS256")

def authenticate_token(token):
    if not token:
        return None
    try:
        decode = jwt.decode(token, "secretPassword", algorithms=["HS256"], require=['id', 'group'])
    except:
        return None
    return decode

def bool_in_str_to_zero_one(str):
    str = str.lower()
    if str == 'true':
        return 1
    elif str == 'false':
        return 0
    return None

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

@flask_app.route('/order', methods=['POST'])
def post_order():
    # Authenticate token
    token = flask.request.args.get('token')
    if not token:
        return {'error': 'token is required'}, 401
    user = authenticate_token(token)
    if not user:
        return {'error': 'invalid token'}, 403
    if user['group'] != 'customer':
        return {'error': 'you do not have the permission to perform this request'}, 403
    
    # Check if food existsd
    restaurant_id = flask.request.args.get('restaurant_id')
    if not restaurant_id:
        return {'error', 'restaurant_id is required'}, 400
    food_id = flask.request.args.get('food_id')
    if not food_id:
        return {'error', 'food_id is required'}, 400
    response = requests.get('http://menu:15000/'+restaurant_id+'/'+food_id)
    if response.status_code == 404:
        return flask.jsonify(response.json()), response.status_code
    
    # Create order_id and load
    order_id = hash(str(user['id'])+str(datetime.datetime.now().timestamp))
    load = json.dumps({
        'order_id': order_id,
        'user_id': user['id'],
        'restaurant_id': restaurant_id,
        'food_id': food_id
    })

    # Add order to restaurant
    redis_conn.publish('restaurantOrder_newOrder', load)
    redis_conn.publish('customerOrder_newOrder', load)
    return {'order_id': order_id}, 200

@flask_app.route('/order/<order_id>', methods=['PUT'])
def put_order(order_id):
    # Authenticate token
    token = flask.request.args.get('token')
    if not token:
        return {'error': 'token is required'}, 401
    user = authenticate_token(token)
    if not user:
        return {'error': 'invalid token'}, 403
    if user['group'] == 'customer':
        return {'error': 'you do not have the permission to perform this request'}, 403


    if user['group'] == 'restaurant':
        # Check if order exists in restaurant
        response = requests.get('http://restaurant_order:15000/order/'+order_id)
        if response.status_code == 404:
            return {'error': 'order id not in restaurant order'}, 404
        ########
        # check if order is your restaurant
        ########
        if response.json()['restaurant_id'] != user['id']:
            return {'error': 'order id is not your restaurant\'s '}, 403

        # Get arguments prepared 
        prepared = flask.request.args.get('prepared')
        if not prepared:
            return {'error: action is needed (i.e. prepared)'}, 400
        prepared = bool_in_str_to_zero_one(prepared)
        if prepared == None:
            return {'error: prepared should be true or false)'}, 400

        # Send event
        load = json.dumps({
            'order_id': order_id,
            'prepared': prepared
        })
        redis_conn.publish('restaurantOrder_setPrepared', load)
        return '', 204

    # For action shipped
    if user['group'] == 'delivery':
        # Check arguments exists
        shipped = flask.request.args.get('shipped')
        arrived = flask.request.args.get('arrived')
        if shipped == None != arrived == None:
            return {'error: argument shipped and arrived is mutual exclusive'}, 400


        # Action to set ship
        if shipped:
            # Check if order exists in restaurant
            response = requests.get('http://restaurant_order:15000/order/'+order_id)
            if response.status_code == 404:
                return {'error': 'order id not in restaurant order'}, 404
            response_content = response.json()
            # Check if order is prepared by the restaurant
            if response_content['prepare'] == 0:
                return {'error': 'order id not in restaurant order'}, 425

            # Send event to restaurant to set delivery
            customer_id = response_content['customer_id']
            restaurant_id = response_content['customer_id']
            
            load = json.dumps({
                'order_id': order_id,
                'delivery_id': user['id']
            })
            redis_conn.publish('restaurantOrder_setShipped', load)

            # Send event to delivery to insert row
            load = json.dumps({
                'order_id': order_id,
                'delivery_id': user['id'],
                'restaurant_id': restaurant_id,
                'customer_id': customer_id
            })
            redis_conn.publish('deliveryOrder_setShipped', load)
            return '', 204

        # For action arrived
        if arrived:
            # Check if order exists in restaurant
            #response = requests.get('http://delivery_order:15000/'+order_id)
            #if response.status_code == 404:
            #    return {'error': 'order id not in delivery order'}, 404
            arrived = bool_in_str_to_zero_one(arrived)
            print(arrived, order_id, flush=True)
            # Send event to delivery
            load = json.dumps({
                'order_id': order_id,
                'taken': arrived
            })
            redis_conn.publish('deliveryOrder_setTaken', load)

            # Send event to customer
            load = json.dumps({
                'order_id': order_id,
                'taken': arrived
            })
            redis_conn.publish('customerOrder_setTaken', load)
            return '', 204


##########################
# Start flask
##########################
if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=15000)
    