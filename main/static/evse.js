class evse{constructor(numEvse){this.numEvse=numEvse;}
createEvseAPI(){for(var i=1;i<=this.numEvse;i++){($('<div id="evseTxt" class="container-fluid text-white pt-2 text-center">'+
' <h4>EVSE: '+i+' </span> <span class="dot" ></h4>'+
'</div>'+
'<table class="table  table-dark rounded" >'+
'<thead> <tr style="background-color: #282828;"> <th>Name</th> <th colspan="2">Status/Value</th> </tr> </thead> '+
'<tbody> <tr> <td>Actual configured amps value :</td> <td><span id="ACTUAL_CONFIG_CURRENT'+i+'">0</span></td></tr>'+
'<tr> <td>Actual amps value output:</td> <td><span id="ACTUAL_OUTPUT_CURRENT'+i+'">0</span></td> </tr>'+
'<tr> <td>Vehicle state:</td> <td><span id="EV_STATE'+i+'">0</span></td> </tr> </tbody>  </table>').appendTo("#evseContainer"));}}}
