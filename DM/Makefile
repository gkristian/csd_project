#Edit makefile
make:
	sudo nano Makefile

#Run DM
dm:
	sudo python ./dm_main.py

#Open MySQL prompt
sql:
	sudo mysql -u root --password=12345678 --init-command='use testdb;'

#Drop all tables before receive new data
drop:
	sudo mysql -u root -p12345678 -e 'use testdb; drop tables nfm_util; drop tables nfm_dropped; drop tables hum; drop tables rpm; show tables;'

#Update number of links according to topology
updatekey:
	sudo mysql -u root -p12345678 -e "use testdb; update keycount set count=46 where module='nfm_util';"

