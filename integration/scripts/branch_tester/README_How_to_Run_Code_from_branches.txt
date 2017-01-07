mkdir /sdn
cd /sdn

##checkout integration branch in this folder using git

cp integration/integration/scripts/branch_tester/Makefile  .

##now checkout all branches by giving below command, you just have to type password
make cloneall 

#now run the code by opening many terminals
make mstart #shall run modules
make stopall #shall kill all processes part of our project
make topology #runs the topology you have listed in that target
make dmstart # runs the DM module
make dmstop #stops the DM module

#all logs include dm.log and cpm logs files are created under /var/www/html/spacey so better create an easy link to it:
ln -s /var/www/html/spacey /slogs

