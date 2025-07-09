from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017')
db = client.miniproject  # 데이터베이스 이름
users_collection = db.users

@app.route('/')
def home():
   return 'This is Home!'

@app.route('/hi')
def main():
    user = users_collection.find_one({'name': 'john'})  
    user_id = user.get('id')  
    return render_template('main.html', userId=user_id, )



@app.route('/his')
def users():
    user_list = [
        {"level": 1, "appDate": '2025-07-08T21:25:43.754993' }, 
        {"level": 0, "appDate": '2025-08-08T21:26:43.754993'}, 
        {"level": 1, "appDate": '2025-07-12T21:17:43.754993'}, ]
    
    return render_template("main.html", appList=user_list)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)

