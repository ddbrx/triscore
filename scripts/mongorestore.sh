# Dump database on source server
mongodump --db triscore --out triscore-backup-2020-04-06

# Copy to target server
rsync -avR triscore-backup-2020-04-06 static.135.98.202.116.clients.your-server.de:/home/dmitriyd/

# Restore database from dump
mongorestore --db triscore --drop triscore-backup-2020-04-06/triscore --numParallelCollections 1