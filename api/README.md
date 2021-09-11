# enable service to start after reboot
sudo systemctl enable nginx
sudo systemctl enable triscore.uwsgi

# races
http://151.248.125.89:5000/api/v1/races?sort=date&order=desc&from=0&to=10

# athletes
http://151.248.125.89:5000/api/v1/athletes?sort=score&order=desc&from=0&to=10
http://151.248.125.89:5000/api/v1/athletes?sort=score&order=desc&from=0&to=10&name=zhidkov
http://151.248.125.89:5000/api/v1/athletes?sort=score&order=desc&from=0&to=19&country=RUS

# race results
http://151.248.125.89:5000/api/v1/race-results?name=IRONMAN%2070.3%20Dubai&date=2021-03-12&athlete=&skip=0&limit=20&sort=finish&order=asc&group=
