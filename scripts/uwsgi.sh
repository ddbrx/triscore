# https://dev.to/hackersandslackers/deploy-flask-applications-with-uwsgi-and-nginx-38a1
uwsgi --http-socket :5000 --plugin python38 --module api:app --virtualenv /home/dmitriyd/triscore-env --processes 2 --threads 4

# https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/
uwsgi -s /tmp/triscore.sock --manage-script-name --mount /triscore=api:app
