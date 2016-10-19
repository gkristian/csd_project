<?php // content="text/plain; charset=utf-8"
require_once('jpgraph/src/jpgraph.php');
require_once('jpgraph/src/jpgraph_line.php');
require_once ('connection.php');

$x_axis = array();
$y_axis = array();
$i = 0;

$result = mysqli_query($con,"SELECT * FROM nfm"); 
while($row = mysqli_fetch_array($result)) {
	$x_axis[$i] = $row["id"];
	$y_axis[$i] = $row["delay"];
    $i++;
}
mysqli_close($con);

// Create the graph. These two calls are always required
$graph = new Graph(350,250);
$graph->SetScale('textlin');
$graph->xaxis->SetTickLabels($x_axis);

// Create the linear plot
$lineplot=new LinePlot($y_axis);
$lineplot->SetColor('blue');

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
