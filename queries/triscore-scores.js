scores = db.getCollection('scores-C-1-D-2')
// scores.createIndex({'n': 'text'})
// scores.count()
// scores.find({'$text': {'$search': '\"Zeinab Faye\"'}})
scores.find({'$and': [{'c': 'AFG'}, {'$text': {'$search': '"Zeinab Faye"'}}]})
// scores.find({n: /Tim Van Berkel/}).sort({s: -1})
// scores.find().sort({s: -1})