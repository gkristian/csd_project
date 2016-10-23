<?php
//PHP file to visualize NFM table and graph
//Purwidi 2016
error_reporting(E_ALL);
ini_set('display_errors', 1);
//Connection establishment
require('connection.php');

//Get all nfm data
$q1 = "SELECT * FROM nfm";
if ($res1 = $con->query($q1)) {
    printf("NFM table fetched<br>");
} else {
    printf("No data from NFM table<br>");
}

//Get NFM's number of keys (#links)
$q2 = "SELECT count FROM keycount WHERE module='nfm'";
if ($res2 = $con->query($q2)) {
	printf("NFM keycount fetched. #links :");
	$row2 = $res2->fetch_assoc();
	$nfmkeycount = intval($row2['count']); //Convert result string to int
	echo $nfmkeycount . gettype($nfmkeycount);
} else {
	printf("No data from keycount<br>");
}

//Get link names
$q3 = "SELECT link FROM nfm LIMIT $nfmkeycount";
if ($res3 = $con->query($q3)) {
    printf("<br>Link names fetched");
} else {
    printf("<br>Failed to fetch link names<br>");
}

echo "<html>";
//Make 3 big columns for 2 data and graph
echo "<table><tr><td>";

//Construct RAW NFM table=================================
if ($res3->num_rows > 0) {
	echo "<h2>RAW NFM Table</h2>";
	//HEADER
	echo "<table border=1><tr><th>timestamp</th><th>link</th><th>utilization</th></tr>";
    while($row1 = $res1->fetch_assoc()) {//Data for each row
		echo "<tr>";
		echo "<td>" . $row1['timestamp'] . "</td>";
		echo "<td>" . $row1['link'] . "</td>";
		echo "<td>" . $row1['util'] . "</td>";
		echo "</tr>";
	}
	echo "</table>";
} else {
   	echo "Error : Construct table";
}

echo "</td><td valign='top'>";
//Construct table of link utilization=====================
echo "<h2>Processed NFM table</h2>";

if ($res3->num_rows > 0) {
    echo "<table border=1><tr><th>timestamp</th>"; //HEADER
    while($row3 = $res3->fetch_assoc()) {
        echo "<th>" .$row3['link']. "</th>";
    }
    echo "</tr>";/*
    while($row1 = $res1->fetch_assoc()) {//Data for each row
        echo "<tr>";
        echo "<td>" . $row1['timestamp'] . "</td>";
        echo "<td>" . $row1['link'] . "</td>";
        echo "<td>" . $row1['util'] . "</td>";
        echo "</tr>";
    }*/
	echo "</table>";
} else {
    echo "Error : Construct table";
}


echo "</td><td valign='top'>";
//Data visualization====================================
echo "<h2>Graphs</h2>";
echo "<img src='plotnfm.php'>";

//End of main table
echo "</td></tr></table></html>";
$con->close(); //DON'T FORGET TO CLOSE
?>
