db.auth('comp3122', '23456')
db = db.getSiblingDB('user')

db.createCollection('customer');
db.customer.insertOne({'id':1, 'username':'charlie', 'password':'9c3800e8f13e343b646abaa27073d47d','Address':'Hong Kong Happy House', 'phone_number': 92410781});
db.customer.insertOne({'id':2, 'username':'chloe', 'password':'a0586b56401c585e49efadfc123130b5','Address':'Hong Kong Exciting House', 'phone_number': 94356213});
db.customer.insertOne({'id':3, 'username':'charlotte','password':'2f76542646da7a92264d2f5ce52439a2', 'Address':'Hong Kong Playing House', 'phone_number': 97325641});

db.createCollection('restaurant');
db.restaurant.insertOne({'id':1, 'username':'riley', 'password':'a4ca1f62823d1f0ce35b25c700bac3ce','Address':'Hong Kong Happy Dim Sum', 'phone_number': 25309035});
db.restaurant.insertOne({'id':2, 'username':'ruby', 'password':'b0ba58dc074547b974443b803c0d85bc','Address':'Hong Kong Happy Meal', 'phone_number': 24569632});
db.restaurant.insertOne({'id':3, 'username':'ryan','password':'33001e6a47fbc0da6671fb42dd6a7803', 'Address':'Hong Kong Happy Restaurant', 'phone_number': 27543684});

db.createCollection('delivery');
db.delivery.insertOne({'id':1, 'username':'daniel','password':'9eda0ac267e7cbc8506b9c4ee6a80f06', 'phone_number': 95326188});
db.delivery.insertOne({'id':2, 'username':'daisy','password':'04354ec5a573cdfbcc41f1bea5cd2094', 'phone_number': 93457654});
db.delivery.insertOne({'id':3, 'username':'dylan','password':'709488e90b981b35e9a634b6ab414277', 'phone_number': 98657731});

db.createCollection('admin');
db.admin.insertOne({'id':1, 'username':'amelia','password':'e7c6e3e97e97a71ccfa54eea208a5359'});
