# Dump source database
mongodump --db triscore --out triscore-backup-2020-04-06

# Restore database from dump
sudo mongorestore --db triscore --drop triscore-backup-2020-04-06/triscore