echo Installing build tools deps
apt-get install screen
echo Installing CPM dependencies
pip install networkx
pip install matplotlib
apt-get install graphviz
apt-get install python-pygraphviz
pip install pydot

echo Installting DM dependencies

#apt-get install lamp-server^
apt-get install python-dev libmysqlclient-dev
pip2 install MySQL-python
pip2 install requests
#apt-get install php-gd
#apt-get install php7.0-gd

echo Installing HUM deps

#install htop
apt-get install htop
#install perf. CHECK KERNEL VERSION FIRST, then paste it on the apt-get below
#sudo apt-get install linux-tools-<kernel_version>

#psutil library
pip install psutil

#Linux_metrics library
pip install linux_metrics

#stress
apt-get install stress

#pidstat, mpstat
apt install sysstat 

echo Installing RPM
apt-get install python-numpy

echo TODO:
echo Following needs to be manually performed...
echo For mysql set the required password for the root user to 12345678
echo create database with name "testdb" 


#
pip install virtualenv
