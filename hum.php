<?php
//PHP file to visualize HUM table and graph
//Purwidi 2016

//Set error reporting parameter
error_reporting(E_ALL);
ini_set('display_errors', 1);

//Timer. Credit : https://www.phpjabbers.com/measuring-php-page-load-time-php17$
$time = microtime();
$time = explode(' ', $time);
$time = $time[1] + $time[0];
$start = $time;

//Connection establishment
require('connection.php');
echo "<html>";
echo "<meta http-equiv='refresh' content='10'>";
echo "<b>Debug Message :</b><br>";

//Get all hum data and save them into array=============================
$data = array();
$q1 = "SELECT * FROM hum";
if ($all = $con->query($q1)) {
    printf("HUM table fetched<br>");
    while($row1 = $all->fetch_assoc()) {
        array_push($data,$row1);
    }
} else {
    printf("No data from HUM table<br>");
}
//Convert cpu usage data from json format to php array
for ($j=0;$j<19;$j++) {
    $data[$j]['core']=json_decode($data[$j]['core'],True);
}
//Take the latest 19 data
$sliced = array_slice($data, -19);
//Get number of cpu
$cpucount=count($data[0]['core']);

//SECTION FOR MEMORY GRAPHS=============================================
$arraymem=array();
for ($i=0;$i<19;$i++) {
    array_push($arraymem,$sliced[$i]['memory']);
}
$imploded=implode(":",$arraymem);
echo "<center>";
echo "<font face='calibri' size='6'><b>HUM Graphs</font><br>";
echo "data for the past 3 minutes</b><br>";
echo "<img src=humplotmem.php?data=".urlencode($imploded).">";
echo "<br><br>";

//SECTION FOR CPU GRAPHS===============================================


//SECTION FOR RAW HUM table=============================================
echo "<h2>CPU and Memory Usage Table</h2>";
//Tale header
echo "<table border=1><tr>";
echo "<th width='250px'>Timestamp</th>";
echo "<th width='90px'>Memory(%)</th>";
for ($i=0;$i<$cpucount;$i++){
    echo "<th width='80px'>Core " . $i . " (%)</th>";
}
//Table body
for ($k=0;$k<count($data);$k++){
    echo "<tr>";
    echo "<td>" . $data[$k]['timestamp'] . "</td>";
    echo "<td>" . $data[$k]['memory'] . "</td>";
    for ($l=0;$l<count($data[0]['core']);$l++){
        echo "<td>" . $data[$k]['core'][$l] . "</td>";
    }
    echo "</tr>";
}
echo "</table>";
	
//End timer
$time = microtime();
$time = explode(' ', $time);
$time = $time[1] + $time[0];
$finish = $time;
$total_time = round(($finish - $start), 4);
echo "<center><b>Page generated in ".$total_time." seconds.</b></center>";
echo "</html>";
?>




