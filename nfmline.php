<?php // content="text/plain; charset=utf-8"
require_once('jpgraph/src/jpgraph.php');
require_once('jpgraph/src/jpgraph_line.php');

require_once ('connection.php');
open_connection();

//$lbl=array();

$q1 = "SELECT * FROM nfm";
$result = $conn ->query($q1);
$datay=array();
while($row = mysql_fetch_array($result)) {
	//array_push($lbl,$row['id']);
	array_push($datay,$row['delay']);
}


$datay=array(12,8,19,3,10,5);
// Create the graph. These two calls are always required
$graph = new Graph(350,250);
$graph->SetScale('textlin');

// Create the linear plot
$lineplot=new LinePlot($datay);
$lineplot->SetColor('blue');

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
