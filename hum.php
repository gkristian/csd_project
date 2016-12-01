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

//Get all hum data
$q1 = "SELECT * FROM hum";
if ($all = $con->query($q1)) {
    printf("HUM table fetched<br>");
} else {
    printf("No data from HUM table<br>");
}

//SECTION FOR MEMORY GRAPHS==============================================$
echo "<center>";
echo "<font face='calibri' size='6'><b>HUM Graphs</font><br>";
echo "data for the past 3 minutes</b><br>";
$data=array();
while($row1 = $all->fetch_assoc()) {
    array_push($data,$row1['memory']);
}
$tobesend = array_slice($data, -19); //Take the latest 20 data
$imploded=implode(":",$tobesend);
echo "<img src=humplotmem.php?data=".urlencode($imploded).">";
echo "<br><br>";

//SECTION FOR RAW HUM table====================================================$
echo "<h2>RAW HUM Table</h2>";
//HEADER
echo "<table border=1><tr><th>timestamp</th><th>core</th><th>memory</th>";
while($row2 = $all->fetch_assoc()) {//Data for each row
	echo "<tr>";
    echo "<td>" . $row1['timestamp'] . "</td>";
    echo "<td>" . $row1['core'] . "</td>";
    echo "<td>" . $row1['memory'] . "</td>";
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




