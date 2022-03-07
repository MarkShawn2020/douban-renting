import pymongo

DATABASE_URI = "localhost:27017"
DATABASE_NAME = "douban"

uri = pymongo.MongoClient(DATABASE_URI)

db = uri[DATABASE_NAME]
