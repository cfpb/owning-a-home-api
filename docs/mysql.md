## Using MySQL

For testing, the default Django sqlite database will be set up for you automatically. If you want to load a MySQL dataset, you can edit `settings_for_testing.py` to uncomment the MySQL database section and install MySQL as follows:
```shell
brew install mysql
```
Start the MySQL Server, this command may need to be run again (if stopped) when trying to bring up the web server later:
```shell
mysql.server start
```
Set Password for root:
```shell
mysql_secure_installation
```
Connect to MySQL with root and password:

```shell
mysql -uroot -p
```

Or, if you're using [cfgov-refresh's](https://github.com/cfpb/cfgov-refresh) no-password local development setup, you can forgo the password step:

```shell
mysql -uroot
```

Then create an owning-a-home database:
```shell
create database oah;
```
If you would like to connect with a different user other than root, you can create a user, and replace `oah_user` with your desired username and `password` with your desired password:
```shell
create user 'oah_user'@'localhost' identified by 'password';
grant all privileges on oah.* to 'oah_user'@'localhost';
flush privileges;
exit
```
You can now connect to MySQL with your newly created username and password and have access to `oah`:
```shell
mysql -u oah_user -p
# enter your password
show databases;
use oah;
exit
``` 

If you have access to mortgage data, you could load it like so:

```
mysql -uroot -p oah < [PATH TO YOUR .sql DUMP]
```
