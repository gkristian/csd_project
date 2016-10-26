<?php 
// content="text/plain; charset=utf-8"
//Purwidi 2016
//Created using JPGraph. This code is based on one of the JPGraph example

//Library
require_once('jpgraph/src/jpgraph.php');
require_once('jpgraph/src/jpgraph_line.php');

//Receive data via GET
$var_value = $_GET['data'];
$var_value2=$_GET['title'];

//Explode it and convert from string to float
$b = explode(":",urldecode($var_value));
foreach ($b as &$value) {
    $value = floatval($value);
}
$data = $b;

//Explode title
$title=explode("-",urldecode($var_value2));

//Define x axis for 20 latest data
$x_axis = array(-20,-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0);
//$x_axis = array(300,200,100,0);


// Create the graph. These two calls are always required
$graph = new Graph(420,280);
$graph->SetScale('textlin');

//COSMETICS
$graph->SetFrame(true,'black',0);
//$graph->title->Set("Link Utilization for past 300sec");
//$graph->title->SetFont(FF_DV_SANSSERIF, FS_BOLD, 12);
$graph->subtitle->Set("Sw". $title[0] ."-Sw". $title[1]);
$graph->subtitle->SetFont(FF_DV_SANSSERIF, FS_BOLD, 12);

//SCALING AND AXIS LABELLING
//100% scale
/*
$graph->SetScale('intint',0,100);
$ypos = array(0,10,20,30,40,50,60,70,80,90,100);
$ylabels = array("0%","10%","20%","30%","40%","50%","60%","70%","80%","90%","100%");
*/
//50% SCALE
$graph->SetScale('intint',0,50);
$ypos = array(0,10,20,30,40,50);
$ylabels = array("0%","10%","20%","30%","40%","50%");
$graph->yaxis->SetMajTickPositions($ypos,$ylabels);
//$graph->yscale->ticks->Set(0.2,0.01);
//$graph->yaxis->SetTickLabels(array('0%','40%','40%','60%','80%','100%'));
$xpos = array(0,6,12,17);
$xlabels = array("3 min","2 min","1 min","current");
$graph->xaxis->SetMajTickPositions($xpos,$xlabels);

// Create the linear plot
$lineplot=new LinePlot($data);
$lineplot->SetColor('blue');

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
