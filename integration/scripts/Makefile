#author; Adnan Shafi ashafi@kth.se
#NOTES by ashafi:
#You can pass the branch name as the command line argument
#make clone branch=RPM
branch = RPM
clone:
	git clone git@gits-15.sys.kth.se:csd-group-4-space-y/sdn_monitoring.git
	mv sdn_monitoring $(branch)
	cd $(branch);git checkout -b $(branch) origin/$(branch)

# Notes:
# Each line below is passed to sh and executed irresepective of the other line
# So to define a variable and make it avaialble across other executions we want to knit all lines below into a one line command
# and that is done by using \ plus since its a shell variable not a makefile varaible so we use syntax $$
# source: http://stackoverflow.com/questions/1909188/define-make-variable-at-rule-execution-time

dmclone:
	branch=DM;echo branch is $$branch;\
	git clone git@gits-15.sys.kth.se:csd-group-4-space-y/sdn_monitoring.git;\
	mv sdn_monitoring $$branch;\
	cd $$branch;git checkout -b $$branch origin/"$$branch";\


