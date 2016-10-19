# coverage erase
coverage run manage.py test > /dev/null
coverage report -m
