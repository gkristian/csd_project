<?php // content="text/plain; charset=utf-8"
require_once ('jpgraph/src/jpgraph.php');
require_once ('jpgraph/src/jpgraph_line.php');

//Receive data via GET
$var_value = $_GET['data'];

//Explode it and convert from string to float
$b = explode(":",$var_value);
foreach ($b as &$value) {
    $value = floatval($value);
}
$ydata = $b;

// Size of the overall graph
$width=420;
$height=280;

//Define x axis for 20 latest data
$x_axis = array(-20,-19,-18,-17,-16,-15,-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,0);

// Create the graph and set a scale.
// These two calls are always required
$graph = new Graph($width,$height);

//subtitle
$graph->subtitle->Set("Memory Usage");
$graph->subtitle->SetFont(FF_DV_SANSSERIF, FS_BOLD, 12);

//SCALING AND AXIS LABELLING
$graph->SetScale('intint',0,100);
$ypos = array(0,10,20,30,40,50,60,70,80,90,100);
$ylabels = array("0%","10%","20%","30%","40%","50%","60%","70%","80%","90%","100%");
$graph->yaxis->SetMajTickPositions($ypos,$ylabels);
$xpos = array(0,6,12,17);
$xlabels = array("3 min","2 min","1 min","current");
$graph->xaxis->SetMajTickPositions($xpos,$xlabels);

// Create the linear plot
$lineplot=new LinePlot($ydata);

// Add the plot to the graph
$graph->Add($lineplot);

// Display the graph
$graph->Stroke();
?>
