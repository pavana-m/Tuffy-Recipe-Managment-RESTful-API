from flask import Flask, jsonify,request,render_template
from app import Recipes,db, Users #class models from app
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os

api = Flask(__name__)

api.config["JWT_SECRET_KEY"] = "world999$"  #configure the JWT
jwt = JWTManager(api)


api.config["SQLALCHEMY_DATABASE_URI"]="mysql://root:world999%24@localhost/recipedb"
api.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db.init_app(api) #initializing the db






@api.route('/',methods=['GET'])
def index():
  return "<h1>Welcome to Recipe Management</h1> Try adding <code>/recipes</code> in the URL to view all the available recipes and prepare good food. "
  

#GET(Public) method that displays all the recipe names present. Only authorized users would be able to view the recipe instructions which is a protected endpoint.
@api.route('/recipes', methods=['GET']) 
def get_recipes():
    try:
        recipes = Recipes.query.all()
        output = [] #empty list for appending the recipes to display.
        for recipe in recipes:
            recipe_data = {'id': recipe.id, 'recipe_name': recipe.recipe_name}
            output.append(recipe_data)
        if not output:
            return jsonify({'message': 'No recipes found'}), 404
        return jsonify({'recipes': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
  

#POST method to insert/create the recipe name and instructions into the system.
@api.route('/recipes',methods=['POST']) 
def add_recipe():
    try:
        data = request.get_json()
        if 'recipe_name' not in data or 'instructions' not in data:
            return jsonify({'error': 'Recipe name and instructions are required'}), 400
        existing_recipe = Recipes.query.filter_by(recipe_name=data['recipe_name']).first()
        
        if existing_recipe:  #To avoid multiple entries of the same recipe on to the db.
            return jsonify({'error': 'Recipe already exists'}), 409
        
        new_recipe = Recipes(recipe_name=data['recipe_name'], instructions=data['instructions'])
        db.session.add(new_recipe)
        db.session.commit()
        return jsonify({'message': 'New recipe added successfully!!!!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#PUT method updates the instructions of a particular recipe when passed as a parameter(recipe_name) in the URL  
@api.route('/recipes/<string:recipe_name>', methods=['PUT'])
def update_recipe(recipe_name):
    data = request.get_json()
    recipe = Recipes.query.filter_by(recipe_name=recipe_name).first()
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    if 'instructions' in data:
        recipe.instructions = data['instructions']
        db.session.commit()
        return jsonify({'message': f'Recipe "{recipe_name}" instructions updated successfully!!'})
    else:
        return jsonify({'error': 'Instructions not provided'}), 400
      
     
#DELETE method deletes one particular recipe when passed as a parameter on to the URL.
@api.route('/recipes/<string:recipe_name>', methods=['DELETE'])
def delete_recipe(recipe_name):
    try:
        recipe = Recipes.query.filter_by(recipe_name=recipe_name).first()
        if not recipe:
            return jsonify({'message': 'Recipe not found'}), 404

        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'message': 'Recipe deleted successfully'})
    except Exception as e:
        return jsonify({'message': 'An error occurred while deleting the recipe', 'error': str(e)}), 500



#400 for Bad Request
@api.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'This is a Bad request.'}), 400

#401 for Unauthorized
@api.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'You are unauthorized.'}), 401

#404 for Not Found
@api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Item not found.'}), 404

#500 for Internal Server Error
@api.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'There has been an internal server error.'}), 500
  
@api.errorhandler(409)
def conflict_error(error):
    return jsonify({'error': 'Resource already exists.'}), 409


@api.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({'error': 'Method not allowed for this requested URL'}), 405
  
  
#Authentication for viewing Recipe Instructions.
#for users to register.
@api.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    existing_user = Users.query.filter_by(username=username).first()
    #add exception for null input of user.
    if username =="":
      return jsonify({'message':'User name should be added.'})
    
    if existing_user: #check if user exists or not.
        return jsonify({'message': 'Username already exists'}), 409
    user = Users(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"})


#Users to login 
@api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = Users.query.filter_by(username=username, password=password).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"message": "Invalid credentials"}), 401

#Protected endpoint to check the user logged in as.
@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

#Protected endpoint for auth users to access all the recipes and their respective instructions
@api.route('/protected/recipes', methods=['GET'])
@jwt_required()
def get_protected_recipes():
    try:
        recipes = Recipes.query.all()
        output = []  # Empty list to store the recipes and their instructions.
        for recipe in recipes:
            recipe_data = {
                'id': recipe.id,
                'recipe_name': recipe.recipe_name,
                'instructions': recipe.instructions
            }
            output.append(recipe_data)
        if not output:
            return jsonify({'message': 'No recipes found'}), 404
        return jsonify({'recipes': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500







  





if __name__ == "__main__":
  api.run(debug=True)