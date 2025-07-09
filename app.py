from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask.json.provider import JSONProvider
from flask_mail import Mail, Message

from collections import Counter

import requests
from bs4 import BeautifulSoup

from repository import *
import json
import sys
import random
import datetime

import schedule
import time
import threading

app = Flask(__name__)

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

# Flask-Mail 설정
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'seo980620@gmail.com'
app.config['MAIL_PASSWORD'] = 'hhvw vlgp neca mtyk'
app.config['MAIL_DEFAULT_SENDER'] = 'seo980620@gmail.com'
mail = Mail(app)

#이메일 발송 함수
def send_verification_email(user_email, code):
    msg = Message(
        subject = "[Flask App] 이메일 주소 확인 코드",
        recipients=[user_email],
        html=f"""
        <h1>이메일 주소 확인</h1>
        <p>계속하려면 6자리 코드를 입력해주세요</p>
        <h2>{code}</h2>
        <p>이 코드는 5분간 유효합니다.</p>
        """
    )
    mail.send(msg)

def makeTestUser():
    name = 'userName'
    id = 'userId'
    pw = 'userPw'
    githubAccount = 'userGithubAccount'
    appTicket = 1
    getAppTicket = False
    appList = [{'productName': '콜라', 'appPrice': 10, 'appDate': datetime.datetime(2025,7,6)},
                {'producctName': '사이다', 'appPrice': 20,'appDate': datetime.datetime(2025,7,7)}]
    attendanceList = [{'dateTime': datetime.datetime(2025,7,6), 'isAttendance': True},
                      {'dateTime': datetime.datetime(2025,7,7), 'isAttendance': True},
                      {'dateTime': datetime.datetime(2025,7,8), 'isAttendance': True}]
    
    user = {'name': name, 'id': id, 'pw': pw, 'githubAccount': githubAccount,
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

@app.route('/')
def home():
   return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        id = request.args.get('id')
        pw = request.args.get('pw')

        user = db.user.find_one({'id': id})
        if user['pw'] == pw:
            return jsonify({'result': 'success'})
        else:
            return jsonify({'result': 'failure'})
    
    return render_template('login.html')
    
@app.route('/login/pwChange', methods=['GET'])
def pwChange():
    code = request.args.get('code')
    id = request.args.get('id')
    new_pw = request.args.get('pw')

    result = db.user.update_one({'id': id}, {'$set' : {'pw': new_pw}})

    if result.modified_count == 1:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'failure'})
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        id = request.form.get('id')
        pw = request.form.get('password')

        code = str(random.randint(100000,999999))
        expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=5)

        user = {'email': email, 'id': id, 'pw': pw, 'code': code, 'code_expires_at': expiration_time}

        db.user.insert_one(user)
        send_verification_email(email, code)

        return render_template('register.html')
        # return redirect(url_for('verify-email', email=email))
    
    return render_template('register.html')

@app.route('/verify-email', methods=['GET'])
def verifyEmail():
    code = request.args.get('code')
    return jsonify({'result': 'success'})

#현재회차상품이름받기
@app.route('/getAppProductName', methods=['GET'])
def getAppProductName():
    # 응모 마감일이 오늘 23:59:59.999999 = 현재 회차 상품
    endDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': endDate})
    return jsonify({'result': 'success', 'productName': product['productName']})

#응모하기
@app.route('/apply', methods=['POST'])
def apply():
    userId = request.form.get('userId')
    appPrice = request.form.get('appPrice')

    user = db.user.find_one({'id': userId})

    #응모권 부족한 경우
    if user['appTicket'] < 0:
        return jsonify({'resuslt': 'failure'})
    
    #티켓사용및 출석처리
    newAppTicket = user['appTicket'] - 1
    db.user.update_one({'id': id}, {'$set' : {'appTicket': newAppTicket}})
    newAttendanceList = user['attendanceList']
    for record in newAttendanceList:
        if record['datetime'] == datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0):
            record['isAttendance'] = True
            break
    db.user.update_one({'id': id}, {'$set' : {'attendanceList': newAttendanceList}})

    #연속 응모시 4배수에 추가 도전권 지급
    consecutiveDay = calcConsecutiveAttendance(user)
    if (consecutiveDay % 4 == 0):
        newAppTicket = user['appTicket'] + 1
        db.user.update_one({'id': id}, {'$set' : {'appTicket': newAppTicket}})

    #응모 딕셔너리 만들어서 DB내 리스트에 추가
    endDate = datetime.datetime.today().replace(hour=23, minute=59, second=59, microsecond=0)
    product = db.product.find_one({'appEndDate': endDate})
    app = {'productName': product['productName'], 'appPrice': appPrice, 'appDate': datetime.datetime.now()}
    db.user.update_one({'id': id}, {'$push' : {'appList': app}})

    return jsonify({'result': 'success'})

#user DB받아서 연속 출석일 계산하기
def calcConsecutiveAttendance(user):
    attendanceList = user['attendanceList']
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
def getApplist():
    userId = request.args.get('userId')
    user = db.user.find_one({'id': userId})
    appList = user['appList']
    # datetime을 isoformat 문자열로 교체
    # datetime은 json 객체에 담을 수 없음!!!
    for app in appList:
        app['appDate'] = app['appDate'].isoformat()

    return jsonify({'result': 'success', 'appList': appList})

#연속응모횟수받기
@app.route('/getConsecutiveDay', methods=['GET'])
def getConsecutiveDay():
    userId = request.args.get('userId')
    user = db.user.find_one({'id': userId})
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

#경품리스트받기 ~도전 당첨 결과 확인~
@app.route('/getRewards', methods=['GET'])
def getRewards():
    all_doc_cursor = db.reward.find({})
    rewards = list(all_doc_cursor)
    #appRound로 정렬해서 주기
    #내림차순
    sorted_rewards = sorted(rewards, key=lambda reward: reward['appRound'], reverse=True)
    return jsonify({'result': 'success', 'rewards': sorted_rewards})

@app.route('/test', methods=['GET'])
def test():
    userId = 'userId'
    user = db.user.find_one({'id': userId})
    githubAccount = user['githubAccount']
    req = requests.get(f'http://github.com/{githubAccount}')
    html = req.text

    soup = BeautifulSoup(html, 'html.parser')
    repos = soup.select('.position-relative').select('.ContributionCalendar-grid.js-calendar-graph-table')

    return jsonify({'result': 'success', 'repos': str(repos)})

if __name__ == '__main__':
   start_scheduler()
   print(sys.executable)  
   app.run('0.0.0.0', port=5001, debug=False)