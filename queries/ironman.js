ironman = db.getCollection('ironman')

// ironman.createIndex({'data.ContactId': 1})

// ironman.find({'SubEvent': /2014 IRONMAN 70.3 European/, 'data.Contact.FullName': /Tollakson/}).sort({_id: -1})
// ironman.find({'SubEvent': /Sunshine Coast/}).sort({_id: -1})
// ironman.find({'SubEvent': /2011 IRONMAN 70.3 Switzerland/}, {data: {'$elemMatch': {'Contact.FullName': 'Viktor Zhidkov'} } })
// ironman.find({'SubEvent': /2019 IRONMAN 70.3 Sunshine Coast/}, {data: {'$elemMatch': {'ResultId': '2F0B8563-B8FB-4007-9D7B-04433E53584F'} } })
// ironman.find({'SubEvent': /2019 IRONMAN 70.3 Sunshine Coast/})

// ironman.aggregate([ {'$project': {SubEvent: 1, data: {'$filter': {input: '$data', as: 'item', cond: { '$eq': [ '$$item.ContactId', '63326262-89B4-E511-940C-005056951BF1']}}}}} ])
// ironman.aggregate([ {'$project': {url: 1, SubEvent: 1}} ])

// ironman.find()

// ironman.find({'SubEvent': /IRONMAN/}, {SubEvent: 1}).sort({_id: -1})
// ironman.find({'SubEvent': /2002 IRONMAN Florida/}).sort({SubEvent: -1})
// ironman.aggregate([{'$match': {'SubEvent': '002 IRONMAN Florida'}}, {'$unwind': '$data'}, {'$sort': {'data.FinishRankOverall': 1}}, {'$skip': 0}, {'$limit': 0}])

// ironman.updateOne({SubEventId: '0E43C278-7D5A-E211-B7A2-005056956277'}, {'$set': {invalid: true}})
// ironman.count()