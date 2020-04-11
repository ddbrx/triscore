tristats = db.getCollection('tristats')
// tristats.createIndex('RaceName')
tristats.find({RaceName: /Brazil/})