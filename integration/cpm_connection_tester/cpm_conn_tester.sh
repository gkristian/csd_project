
while true
do
iperf3 -c $1 -u -b 128K -t 5;sleep 3;iperf3 -c $1 -u -b 128K -t 5
done
