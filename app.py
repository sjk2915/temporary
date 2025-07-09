from flask import Flask, jsonify, render_template, request, redirect, url_for, make_response
from flask.json.provider import JSONProvider

from collections import Counter

import requests
from bs4 import BeautifulSoup

from repository import *
import json
import sys
import jwt
import bcrypt
from functools import wraps

import random
import datetime

import schedule
import time
import threading
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

app.json = CustomJSONProvider(app)

# 1회차 = 7월 7일 (기준)
firstRound = datetime.date(2025, 7, 7)

def create_access_token(user_id):
    encoded = jwt.encode(
        payload={
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)
        },
        key=app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return encoded

def create_refresh_token(user_id):
    jti = str(uuid.uuid4())
    encoded = jwt.encode(
        payload={
            'jti': jti,
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        },
        key=app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    tokendoc = {
        'jti': jti,
        'user_id':user_id,
        'revoke': False
    }
    # db 저장
    store_refresh_token(tokendoc)

    return encoded

# 엑세스 토큰 재발급
@app.route('/refresh', methods=['POST'])
# 모든 403 에는 재 로그인 시킬 것
def refresh():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'msg': '리프레시 토큰이 존재하지 않습니다.'}), 403
    try:
        payload = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        jti = payload['jti']

        # 블랙리스트 인지 조회
        is_blacklist = is_refresh_token_valid(jti)
        if is_blacklist['revoke']:
            return jsonify({'msg': '리프레시 토큰이 revoke 되었습니다.'}), 403
        
        new_access_token = create_access_token(payload['user_id'])
        response = make_response(jsonify({'result':'엑세스 토큰 재발급 완료'}))
        response.set_cookie('access_token', new_access_token, httponly=True, samesite='Strict')
        return response
    
    except jwt.ExpiredSignatureError:
        return jsonify({'msg': '리프레시 토큰이 만료됐습니다.'}), 403    
    except jwt.InvalidTokenError:
        return jsonify({'msg': '리프레시 토큰이 유효하지 않습니다.'}), 403

# 토큰 검증 데코레이터
def verify_token(f):
    @wraps(f)
    # 모든 403 에는 엑세스 토큰 재발급
    def decorated(*args, **kwargs):
        access_token = request.cookies.get('access_token')
        
        if not access_token:
            return jsonify({'msg': '엑세스 토큰이 존재하지 않습니다.'}), 403
        try:
            payload = jwt.decode(access_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'msg': '엑세스 토큰이 만료됐습니다.'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'msg': '엑세스 토큰이 유효하지 않습니다.'}), 403
        
        return f(current_user_id, *args, **kwargs)
    return decorated

def makeTestUser():
    name = 'userName'
    id = 'userId22'
    pw = '1q2w3e4r'
    encodedPw = pw.encode('utf-8')
    salt = bcrypt.gensalt()
    hashedPw = bcrypt.hashpw(encodedPw, salt)

    githubAccount = 'userGithubAccount'
    appTicket = 1
    getAppTicket = False
    appList = [{'productName': '콜라', 'appPrice': 10, 'appDate': datetime.datetime(2025,7,6)},
                {'productName': '사이다', 'appPrice': 20,'appDate': datetime.datetime(2025,7,7)}]
    attendanceList = [{'dateTime': datetime.datetime(2025,7,6), 'isAttendance': True},
                      {'dateTime': datetime.datetime(2025,7,7), 'isAttendance': True},
                      {'dateTime': datetime.datetime(2025,7,8), 'isAttendance': True}]
    
    user = {'name': name, 'id': id, 'pw': hashedPw, 'githubAccount': githubAccount,
                'appTicket': appTicket, 'getAppTicket': getAppTicket, 'appList': appList, 'attendanceList': attendanceList}
    db.user.insert_one(user)

def makeRandomProduct():
    productName = "productName"
    minPrice = 10
    maxPrice = 20
    appStartDate = datetime.datetime.now()
    appEndDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)

    appUsers = []
    for i in range(5):
        userid = i
        appPrice = random.randint(minPrice, maxPrice)
        appUsers.append({'id': userid, 'appPrice': appPrice})

    product = {'productName': productName, 'minPrice': minPrice, 'maxPrice': maxPrice, 
                'appStartDate': appStartDate, 'appEndDate': appEndDate, 'appUsers': appUsers}
    db.product.insert_one(product)

def selectWinner():
    appEndDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': appEndDate})
    productName = product['productName']

    appUsers = product['appUsers']
    appPriceList = [item['appPrice'] for item in appUsers]
    
    appLog = []
    priceCounts = Counter(appPriceList)
    for price, count in priceCounts.items():
        appLog.append({'price': price, 'count': count})

    #최소면서 중복되지 않는 수 찾기
    unique_prices = []
    for item in appLog:
        if item['count'] == 1:
            unique_prices.append(item['price'])

    if(unique_prices):
        appPrice = min(unique_prices)
        appUser = next((item['id'] for item in appUsers if item['appPrice'] == appPrice), None)

    else:
        appPrice = None
        appUser = None

    appRound = (datetime.date.today() - firstRound).days + 1

    reward = {'productName': productName, 'appPrice': appPrice, 'appUser': appUser, 'appRound': appRound, 'appLog': appLog}
    db.reward.insert_one(reward)

def run_scheduler():
    # schedule.run_pending()을 계속 실행하는 루프.
    while True:
        schedule.run_pending()
        time.sleep(1) # 1초마다 예약된 작업이 있는지 확인

def start_scheduler():
    # 테스트용 5초마다 함수실행
    # schedule.every(5).seconds.do(makeRandomProduct)

    # 매일 23시 59분 59초에 selectWinner 함수 실행
    schedule.every().day.at("23:59:59").do(selectWinner)
    # 매일 0시 0분 0초에 미출석 기록
    schedule.every().day.at("00:00:00").do(pushAttendance)

    # 스케줄러를 별도의 스레드에서 실행
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True # 메인 스레드가 종료되면 함께 종료되도록 설정
    scheduler_thread.start()

@app.route('/', methods=['GET'])
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        id = request.form['id']
        pw = request.form['pw']

        encoded_pw = pw.encode('utf-8')

        user = find_id(id)
        
        if user != None and bcrypt.checkpw(encoded_pw, user['pw']):
            user.pop('pw')
            access_token = create_access_token(user['id'])
            refresh_token = create_refresh_token(user['id'])

            response = make_response(jsonify({'result':'success'}))
            
            response.set_cookie('access_token', access_token, httponly=True, samesite='Strict')
            response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Strict')
            return response   
        else:
            return jsonify({'result':'failure', 'msg':'아이디가 존재하지 않거나 비밀번호가 틀렸습니다.'})

    else:
        return render_template("login.html")
    
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        id = request.form['id']
        pw = request.form['pw']
        id_github = request.form['id_github']

        # 바이트 문자열로 변환
        encoded_pw = pw.encode('utf-8')
        # 동일한 입력에 대해서도 항상 다른 값 
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(encoded_pw, salt)

        userdoc = {
            'name':name,
            'id':id,
            'pw':hashed_pw,
            'id_github':id_github
        }

        create_user(userdoc)

        return jsonify({'result':'success'})
    
    else:
        return render_template("join.html")

@app.route('/checkid', methods=['GET'])
def checkid():
    id = request.args.get('id')
    user = find_id(id)

    if user != None:
        return jsonify({'result':'failure', 'msg':user['id'] + ' 는 중복된 아이디 입니다.'})
    else:
        return jsonify({'result':'success', 'msg':id + ' 는 사용가능한 아이디 입니다.'})

@app.route('/main', methods=['GET'])
@verify_token
def main(current_user_id):
    user = db.user.find_one({'id': current_user_id})
    #appList
    appList_make = user.get('appList', [])
    for app in appList_make:
        app['appDate'] = app['appDate'].isoformat()
      
    #consecutiveDay, attendanceList
    consecutiveDay = calcConsecutiveAttendance(user)
    #줘야되는 형식[{'dateTime': datetime,'level': int}]
    atdList = user.get('attendanceList', [])
    if atdList:
        attendanceList = [
            {
                'dateTime': item['dateTime'].isoformat(),
                'level': int(item['isAttendance'])
            }
            for item in atdList
        ]
    else:
        attendanceList = []

    #appTicket
    appTicket = user.get('appTicket', 0)

    #productName(나중에 이미지로), minPrice, maxPrice
    #응모 마감일이 오늘 23:59:59.999999 = 현재 회차 상품
    endDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': endDate})
    productName = product['productName']
    minPrice = product['minPrice']
    maxPrice = product['maxPrice']
    print(appList_make,appTicket)
    return render_template("main.html",result="success",
                           appList=appList_make, consecutiveDay=consecutiveDay, attendanceList=attendanceList, appTicket=appTicket,
                           productName=productName, minPrice=minPrice, maxPrice=maxPrice)

#경품리스트페이지 주기
@app.route('/getRewards', methods=['GET'])
def getRewards():
    all_doc_cursor = db.reward.find({})
    rewards = list(all_doc_cursor)
    #appRound로 정렬해서 주기
    #내림차순
    sorted_rewards = sorted(rewards, key=lambda reward: reward['appRound'], reverse=True)
    return render_template('reward.html',
                            rewards=sorted_rewards)

#응모하기
@app.route('/apply', methods=['POST'])
@verify_token
def apply(current_user_id):
    appPrice = request.form.get('appPrice')
    user = db.user.find_one({'id': current_user_id})

    #응모권 부족한 경우
    if user['appTicket'] < 0:
        return jsonify({'resuslt': 'failure'})
    
    #티켓사용및 출석처리
    newAppTicket = user['appTicket'] - 1
    db.user.update_one({'id': current_user_id}, {'$set' : {'appTicket': newAppTicket}})
    newAttendanceList = user['attendanceList']
    for record in newAttendanceList:
        if record['dateTime'] == datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0):
            record['isAttendance'] = True
            isAttendance = True
            break
        else:
            isAttendance = False
    db.user.update_one({'id': current_user_id}, {'$set' : {'attendanceList': newAttendanceList}})

    #출석시 연속 응모 4배수에 추가 도전권 지급
    if isAttendance:
        consecutiveDay = calcConsecutiveAttendance(user)
        if (consecutiveDay % 4 == 0):
            newAppTicket = user['appTicket'] + 1
            db.user.update_one({'id': current_user_id}, {'$set' : {'appTicket': newAppTicket}})

    #응모 딕셔너리 만들어서 DB내 리스트에 추가
    endDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': endDate})
    app = {'productName': product['productName'], 'appPrice': appPrice, 'appDate': datetime.datetime.now()}
    db.user.update_one({'id': current_user_id}, {'$push' : {'appList': app}})

    return jsonify({'result': 'success'})

#user DB받아서 연속 출석일 계산하기
def calcConsecutiveAttendance(user):
    attendanceList = user.get('attendanceList', [])
    if not attendanceList:
        return 0

    attendanceList.sort(key=lambda x: x['dateTime'])
    
    lastAttendedDay = datetime.datetime.today()
    consecutiveDay = 1
    for i, record in enumerate(attendanceList):
        currentDate = record['dateTime']

        if record['isAttendance']:
            if (currentDate - lastAttendedDay).days == 1:
                consecutiveDay += 1
            elif (currentDate - lastAttendedDay).days > 1:
                consecutiveDay = 1
            lastAttendedDay = currentDate

    return consecutiveDay

def pushAttendance():
    newAttendance = {'dateTime': datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0), 'isAttendance': True}
    db.user.update_many({}, {'$push' : {'attendanceList': newAttendance}})

#응모리스트받기 ~도전 기록~
@app.route('/getApplist', methods=['GET'])
@verify_token
def getApplist(current_user_id):
    user = db.user.find_one({'id': current_user_id})
    appList = user['appList']
    # datetime을 isoformat 문자열로 교체
    # datetime은 json 객체에 담을 수 없음!!!
    for app in appList:
        app['appDate'] = app['appDate'].isoformat()

    return jsonify({'result': 'success', 'appList': appList})

#연속응모횟수받기
@app.route('/getConsecutiveDay', methods=['GET'])
@verify_token
def getConsecutiveDay(current_user_id):
    user = db.user.find_one({'id': current_user_id})
    consecutiveDay = calcConsecutiveAttendance(user)
    #줘야되는 형식[{'dateTime': datetime,'level': int}]
    attendanceList = user['attendanceList']
    newAttendanceList = [
        {
            'dateTime': item['dateTime'].isoformat(),
            'level': int(item['isAttendance'])
        }
        for item in attendanceList
    ]

    return jsonify({'result': 'success', 'consecutiveDay': consecutiveDay, 'attendanceList': newAttendanceList})

#도전권 개수 받기
@app.route('/getTicketCount', methods=['GET'])
@verify_token
def getTicketCount(current_user_id):
    user = db.user.find_one({'id': current_user_id})
    appTicket = user['appTicket']
    return jsonify({'result': 'success', 'appTicket': appTicket})

#현재회차 상품정보 받기
@app.route('/getProductInfo', methods=['GET'])
def getProductInfo():
    # 응모 마감일이 오늘 23:59:59.999999 = 현재 회차 상품
    endDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': endDate})
    productName = product['productName']
    minPrice = product['minPrice']
    maxPrice = product['maxPrice']
    return jsonify({'result': 'success', 'productName': productName, 'minPrice': minPrice, 'maxPrice': maxPrice})

def testGithub():
    userId = 'userId'
    user = db.user.find_one({'id': userId})
    githubAccount = user['githubAccount']
    req = requests.get(f'http://github.com/{githubAccount}')
    html = req.text

    soup = BeautifulSoup(html, 'html.parser')
    repos = soup.select('.ContributionCalendar-grid.js-calendar-graph-table')

    return jsonify({'result': 'success', 'repos': str(repos)})
    
@app.route('/test', methods=['GET'])
def test():
    githubAccount = 'sjk2915'
    date = datetime.date.today()
    req = requests.get(f'http://github.com/uesrs/{githubAccount}/contributions?from={date}&to={date}')
    html = req.text

    #soup = BeautifulSoup(html, 'html.parser')
    #repos = soup.select('.ContributionCalendar-grid.js-calendar-graph-table')

    return jsonify({'result': 'success', 'repos': html})

if __name__ == '__main__':
   start_scheduler()
   print(sys.executable)  
   app.run('0.0.0.0', port=5001, debug=False)