<?php 
// content="text/plain; charset=utf-8"
//Purwidi 2016
//Created using JPGraph. This code is based on one of the JPGraph example

//Library
require_once('jpgraph/src/jpgraph.php');
require_once('jpgraph/src/jpgraph_line.php');

//Receive data via GET
$var_value = $_GET['data'];
$title=$_GET['title'];
//Explode it and convert from string to float
$b = explode(":",urldecode($var_value));
foreach ($b as &$value) {
    $value = floatval($value);
}
$y_axis = $b;

//Define x axis for 20 latest data
$x_axis = array(-20,-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0);

// Create the graph. These two calls are always required
$graph = new Graph(420,250);
$graph->SetScale('textlin');
$graph->title->Set("Link ".$title);
$graph->title->SetFont(FF_DV_SANSSERIF, FS_BOLD, 14);
$graph->xaxis->SetTickLabels($x_axis);
$graph->footer->right->Set('Last 20 data');

// Create the linear plot
$lineplot=new LinePlot($y_axis);
$lineplot->SetColor('blue');

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
