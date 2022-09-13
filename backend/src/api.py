from http.client import HTTPException
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# Get short description of drinks


@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()

    # abort 404 if no drinks
    if (len(drinks) == 0):
        abort(404)

    return jsonify({
        'success':
            True,
            'drinks': [drink.short() for drink in drinks]
    }), 200


# Get long description of drinks

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):

    drinks = Drink.query.all()

    # abort 404 if no drinks
    if (len(drinks) == 0):
        abort(404)

    return jsonify({
        'success':
            True,
            'drinks': [drink.long() for drink in drinks]
    }), 200


# Add a new drink

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_new_drink(payload):
    data = dict(request.form or request.json or request.data)

    # abort 404 if title or recipe is not in the body
    new_title = request.json.get("title")
    new_recipe = request.json.get("recipe")
    check_title = Drink.query.filter_by(title=new_title).first()
    if not (new_title and new_recipe):
        abort(400)
    # check if title for the drink already exists
    if not check_title:
        try:
            drink = Drink(title=data.get('title'),
                          recipe=json.dumps(data.get('recipe')))
            drink.insert()
            return jsonify({'success': True, 'drink': drink.long()}), 200
        except HTTPException:
            abort(422)
    else:
        return jsonify({'success': False,
                       'message': 'Drink title already exists'}), 400


# Update an existing drink

@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):

    # abort 404 if title or recipe is not in the body
    edit_title = request.json.get("title")
    edit_recipe = request.json.get("recipe")
    if not (edit_title or edit_recipe):
        abort(400)

    try:
        data = dict(request.form or request.json or request.data)
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink:
            drink.title = data.get('title') if data.get(
                'title') else drink.title
            recipe = data.get('recipe') if data.get('recipe') else drink.recipe
            drink.recipe = recipe if type(recipe) == str else json.dumps(
                recipe)
            drink.update()
            return jsonify({'success': True, 'drinks': [drink.long()]}), 200
        else:
            abort(404)
    except HTTPException:
        abort(422)

# Delete an existing drink


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)

        drink.delete()
        return jsonify({
            'success': True,
            'deleted': drink.id
        }), 200
    except HTTPException:
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    """
     Propagates the formatted 404 error to the response
     """
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(403)
def forbidden(error):
    """
     Propagates the formatted 403 error to the response
     """
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Forbidden"
    }), 403


@app.errorhandler(400)
def bad_request(error):
    """
     Propagates the formatted 403 error to the response
     """
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    """
    Receive the raised authorization error and propagates it as response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
