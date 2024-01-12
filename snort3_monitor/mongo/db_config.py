from pymongo import MongoClient


mongo_client = MongoClient('snort-mongo', 27017)
db = mongo_client['snort']
perf_monitor = db['perf_monitor']
