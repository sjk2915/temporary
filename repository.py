import requests

from bs4 import BeautifulSoup
from pymongo import MongoClient


client = MongoClient('localhost', 27017)
db = client.miniproject

db.users.insert_one({'name':'bobby','age':21})
db.users.insert_one({'name':'kay','age':27})
db.users.insert_one({'name':'john','age':30})


