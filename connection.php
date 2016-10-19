<?php
    $servername = "localhost";
    $username = "root";
    $password = "12345678";
    $dbname = "testdb";

	$con=mysqli_connect($servername,$username,$password,$dbname);
	// Check connection
	if (mysqli_connect_errno()) {
		echo "Failed to connect to MySQL: " . mysqli_connect_error();
	}
?>
