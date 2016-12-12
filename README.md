Now one can run the whole project through just one command. 

#Environment

1. cd to your home directory and  clone all git branches for the modules in a certain directory say "spacey" . This means below would be all valid directories containing the code:
	spacey/DM
	spacey/HUM
	spacey/RPM
	spacey/NFM
	spacey/mergingTestBranch
2. cd spacey/mergingTestBranch
3. Now run below commands which will use the cloned repositories ../ to mergetestbranch except NFM since NFM recent commit fails to work for some simple reason so it will use the nfm code inside the mergetestbranch.

#To run the project
make startall
#To stop the project
make stopall
#To check process status
make show
#To look at the logs
make dmlog
make mlog



