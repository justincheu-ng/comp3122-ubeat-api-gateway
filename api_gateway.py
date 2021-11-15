import flask

flask_app = flask.Flask(__name__)
mongo_client = pymongo.MongoClient('mongodb://comp3122:23456@user_db:27017')
redis_conn = redis.Redis(host='message_queue', port=6379)



if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', debug=True, port=15000)
    