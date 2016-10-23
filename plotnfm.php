<?php // content="text/plain; charset=utf-8"
//Library
require_once('jpgraph/src/jpgraph.php');
require_once('jpgraph/src/jpgraph_line.php');

//Receive data via GET
$var_value = $_GET['data'];
$title=$_GET['title'];
$b = explode(":",urldecode($var_value));
foreach ($b as &$value) {
    $value = floatval($value);
}
$y_axis = $b;

// Create the graph. These two calls are always required
$graph = new Graph(350,250);
$graph->SetScale('textlin');
$graph->title->Set("Link ".$title);
$graph->title->SetFont(FF_DV_SANSSERIF, FS_BOLD, 14);
//$graph->xaxis->SetTickLabels($x_axis);

// Create the linear plot
$lineplot=new LinePlot($y_axis);
$lineplot->SetColor('blue');

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
