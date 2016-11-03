<?php
//PHP file to visualize NFM table and graph
//Purwidi 2016

//Set error reporting parameter
error_reporting(E_ALL);
ini_set('display_errors', 1);

//Timer. Credit : https://www.phpjabbers.com/measuring-php-page-load-time-php17.html
$time = microtime();
$time = explode(' ', $time);
$time = $time[1] + $time[0];
$start = $time;

//Connection establishment
require('connection.php');
echo "<html>";
echo "<meta http-equiv='refresh' content='10'>";
//echo "<b>Debug Message :</b><br>";

//Get all nfm data
$q1 = "SELECT * FROM nfm";
if ($res1 = $con->query($q1)) {
    //printf("NFM table fetched<br>");
} else {
    printf("No data from NFM table<br>");
}

//Get NFM's number of keys (#links)
$q2 = "SELECT count FROM keycount WHERE module='nfm'";
if ($res2 = $con->query($q2)) {
	//printf("NFM keycount fetched. #links :");
	$row2 = $res2->fetch_assoc();
	$nfmkeycount = intval($row2['count']); //Convert result string to int
	//echo $nfmkeycount;
} else {
	printf("No data from keycount<br>");
}

//Get link names
$q3 = "SELECT link FROM nfm LIMIT $nfmkeycount";
if ($res3 = $con->query($q3)) {
    //printf("<br>Link names fetched");
} else {
    printf("<br>Failed to fetch link names<br>");
}

//CONSTRUCT array of linkname and array of everything
if ($res3->num_rows > 0) { //Means data exist
	//ARRAY OF LINKNAME
	$i=0;
	$arrlinkname=array();
	while($row3 = $res3->fetch_assoc()) { //Fetch link names
		array_push($arrlinkname,$row3['link']);
		$i=$i+1;
    }

	/*ARRAY OF DATA for every link. Work as follow :
	1. Get data for each link from raw nfm table
	2. Assign data to correct structure in $arrall. Try print_r to understand
	$arrall[$link][$timestamp][$column] -> $column=0 is time and $column=1 is utilization
	*/
	$arrall=array(); //The main array
	$linkindex=0;
	foreach ($arrlinkname as &$currentlink) {
		$timeindex=0;
		if ($res4 = $con->query("SELECT * FROM nfm WHERE link='$currentlink'")) {
		    while($row4 = $res4->fetch_assoc()) {//Data for each row
				$arrall[$linkindex][$timeindex]=array(
					$row4['timestamp'],
					$row4['util']
				);
				$timeindex=$timeindex+1;
			}
		} else {
			echo "Error xx";
		}
		$linkindex=$linkindex+1;
	}
	//print_r($arrall);
	$linkcount = count($arrall);
	$timecount = count($arrall[0]);
	//echo "<br><b>Result of arrall creation : </b>";
	//echo "<br>#timestamp : " . $timecount;
	//echo "<br>#links : " . $linkcount;
} else {
    echo "Error : Failed to create $arrlinkname and $arrall";
}

//CODE TO SHOW TABLE AND GRAPHS=====================================================================
echo "<table border=0>";

//SECTION FOR GRAPHS================================================================================
echo "<tr><td colspan=2><center>";
echo "<font face='calibri' size='6'><b>Link Utilization Graphs</font><br>";
echo "data for the past 3 minutes</b><br>";
$data=array();
for($link=0;$link<$linkcount;$link++){
	$data=array();
	for($time=0;$time<$timecount;$time++){
		array_push($data,$arrall[$link][$time][1]);
	}
	$tobesend = array_slice($data, -19); //Take the latest 20 data
	//Multiply the value to percental scale
	foreach ($tobesend as &$value) {
 	   $value = $value * 100;
	}
	$title=explode("-",$arrlinkname[$link]);
	if($title[1]>$title[0]){ //Remove duplicate
		$imploded=implode(":",$tobesend);
		echo "<img src=plotnfm.php?title=".$arrlinkname[$link]."&data=".urlencode($imploded).">";
	}
}
echo "<br><br>";
echo "</td></tr>";

//SECTION FOR RAW NFM table=========================================================================
echo "<tr><td valign='top'>";
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
   	echo "Error : Construct raw table";
}
echo "</td>";

//SECTION FOR SEPARATED TABLE FOR EACH LINK=====================================================
echo "<td valign='top'>";
echo "<h2>Processed table</h2>";
if ($res3->num_rows > 0) {
	$i=0;
    echo "<table border=1><tr><th>timestamp</th>"; //HEADER
	//Fetch link names and assign as table header
	for($i=0;$i<$linkcount;$i++) {
		echo "<th>" .$arrlinkname[$i]. "</th>";		
    }
    echo "</tr>";

	$linkindex=0;
	//Create rows for data
	for($time=0;$time<$timecount;$time++){
		echo "<tr>";
		echo "<td>" . $arrall[0][$time][0] ."</td>";
		for($link=0;$link<$linkcount;$link++){
			echo "<td>" . $arrall[$link][$time][1] ."</td>";
		}
		echo "</tr>";
	}
	echo "</table>";
} else {
    echo "Error : Construct table";
}
echo "</td></tr>";


//End of main table
echo "</table>";
$con->close(); //DON'T FORGET TO CLOSE

//End timer
$time = microtime();
$time = explode(' ', $time);
$time = $time[1] + $time[0];
$finish = $time;
$total_time = round(($finish - $start), 4);
echo "<center><b>Page generated in ".$total_time." seconds.</b></center>";
echo "</html>";
?>
