# Autogenerated file
def render(*a, **d):
    yield """<!DOCTYPE html>
<html lang=\"cs-cz\">
<div class=\"container-sm mt-3\">
<table class=\"table  table-dark rounded\" >
    <thead>
        <tr><th>Name</th><th>Status/Value</th><th>Unit</th></tr>
    </thead>   
    <tbody> 
        <tr><td>Time:</td><td><span id=\"time\">0</span></td><td><span> </span></td></tr>
        <tr><td>Actual configured amps value :</td><td><span id=\"ACTUAL_CONFIG_CURRENT\">0</span></td><td><span> A</span></td></tr>
        <tr><td>Actual amps value output:</td><td><span id=\"ACTUAL_OUTPUT_CURRENT\">0</span></td><td><span> A</span></td></tr>
        <tr><td>Vehicle state:</td><td><span id=\"EV_STATE\">0</span></td><td><span> - </span></td></tr>
        <tr><td>U1 value:</td><td><span id=\"U1\">0</span></td><td><span> V</span></td></tr>
        <tr><td>U2 value:</td><td><span id=\"U2\">0</span></td><td><span> V</span></td></tr>
        <tr><td>U3 value:</td><td><span id=\"U3\">0</span></td><td><span> V</span></td></tr>
        <tr><td>I1 value:</td><td><span id=\"I1\">0</span></td><td><span> mA</span></td></tr>
        <tr><td>I2 value:</td><td><span id=\"I2\">0</span></td><td><span> mA</span></td></tr>
        <tr><td>I3 value:</td><td><span id=\"I3\">0</span></td><td><span> mA</span></td></tr>
        <tr><td>Power value:</td><td><span id=\"Power\">0</span></td><td><span> kW</span></td></tr>
        <tr><td>Energy value:</td><td><span id=\"Energy\">0</span></td><td><span> kWh</span></td></tr>
        <tr><td>E1 value:</td><td><span id=\"E1_P\">0</span></td><td><span> Wh</span></td></tr>
    </tbody>  
</table>  

        <canvas id=\"powerGraph\" height =\"250px\">
            <p>Your browser does not support the canvas element.</p>
        </canvas>

        <canvas id=\"energyGraph\" height =\"250px\">
            <p>Your browser does not support the canvas element.</p>
        </canvas>
     </div>
</html>
                     """
