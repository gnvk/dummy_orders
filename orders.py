from dataclasses import dataclass, fields
import random
import os

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'alma'
jwt = JWTManager(app)
if os.getenv('AUTH_ENABLED', 'true').lower() not in ('yes', 'true', '1'):
    jwt_required = lambda fn: fn

@dataclass
class Order:
    symbol: str
    side: str
    price: float
    qty: int

def read_symbols():
    with open('nasdaqlisted.txt') as f:
        for line in f.read().splitlines()[1:]:
            symbol = line.split('|')[0]
            yield symbol

def generate_random_orders(count):
    for _ in range(count):
        yield Order(
            symbol=random.choice(symbols),
            side=random.choice(('buy', 'sell')),
            price=random.random() * 100,
            qty=random.randrange(1, 1000))

symbols = list(read_symbols())
order_count = os.getenv('ORDER_COUNT') or 30
orders = list(generate_random_orders(order_count))

@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify('Missing JSON in request'), 400

    username = request.json.get('username')
    password = request.json.get('password')
    if not username:
        return jsonify('Missing username parameter'), 400
    if not password:
        return jsonify('Missing password parameter'), 400

    if username != 'interjuser' or password != 'alma':
        return jsonify('Bad username or password'), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200

@app.route('/orders', methods=['GET'])
@jwt_required
def list_orders():
    return jsonify(orders), 200

@app.route('/order', methods=['POST'])
@jwt_required
def put_order():
    if not request.is_json:
        return jsonify('Missing JSON in request'), 400

    props = {}
    for field in fields(Order):
        prop = field.name
        value = request.json.get(prop)
        if not value:
            return jsonify(f'Missing parameter: {prop}'), 400
        props[prop] = value

    order = Order(**props)
    orders.append(order)

    return jsonify(order), 200

@app.route('/symbols', methods=['GET'])
def list_symbols():
    symbols = list(read_symbols())
    return jsonify(symbols), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0')
