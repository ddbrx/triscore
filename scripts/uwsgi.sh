# https://dev.to/hackersandslackers/deploy-flask-applications-with-uwsgi-and-nginx-38a1
uwsgi --http-socket :5000 --plugin python39 --module api:app --virtualenv /home/dmitriyd/.virtualenvs/triscore-env --processes 2 --threads 4

# local run
uwsgi --http-socket 127.0.0.1:5000 --plugin python39 --module api:app --virtualenv /home/dmitriyd/.virtualenvs/triscore-env  --stats 127.0.0.1:9191

uwsgi --socket 127.0.0.1:5000 --plugin python39 --module api:app --virtualenv /home/dmitriyd/.virtualenvs/triscore-env  --stats 127.0.0.1:9191

# https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/
uwsgi -s /tmp/triscore.sock --manage-script-name --mount /triscore=api:app


uwsgi --http-socket :5000 --plugin python39 --module api:app --virtualenv /home/dmitriyd/.virtualenvs/triscore --processes 2 --threads 4
