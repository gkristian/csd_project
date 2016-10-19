//Main file to visualize NFM table and graph
<?php
require_once ('connection.php');
$q1 = "SELECT * FROM nfm";
$result = $con	->query($q1);

	if ($result->num_rows > 0) {
?>
		<html>
			<h1>NFM Data</h1>
			<table border=1>
			<tr>
				<th>id</th>
				<th>flow</th>
				<th>delay</th>
			</tr>

<?php
		// output data of each row
    	while($row = $result->fetch_assoc()) {
			echo "<tr>";
			echo "<td>" . $row['id'] . "</td>";
			echo "<td>" . $row['flow'] . "</td>";
			echo "<td>" . $row['delay'] . "</td>";
			echo "</tr>";
    	}
	} else {
    	echo "0 results";
	}
	//DON'T FORGET TO CLOSE
	$con->close();
?>
</table>

<img src="plotnfm.php"> 
</html>
