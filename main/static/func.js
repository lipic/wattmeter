var timer;

chartData = 0
var cnt = 100
function update_ints_count() {
    
    $.ajax({ 
            url: '/updateData' 
        })
        .done(function(data) {
            var ms = 1000
            $('#updateData').html(data.datalayer);
            console.log(data['log'])
            document.getElementById("U1").textContent = data['U1'] 
            document.getElementById("U2").textContent = data['U2']
            document.getElementById("U3").textContent = data['U3']
            document.getElementById("I1").textContent = (data['I1'] > 32767 ?  data['I1'] - 65535 : data['I1'] )
            document.getElementById("I2").textContent = (data['I2'] > 32767 ?  data['I2'] - 65535 : data['I2'] )
            document.getElementById("I3").textContent = (data['I3'] > 32767 ?  data['I3'] - 65535 : data['I3'] )
            //console.log(data['E1'].toString(16))
            console.log(data['E1'] != undefined ?  hexToFloat("0x"+data['E1'].toString(16)).toFixed(3): 0 )
           document.getElementById("E1").textContent = (data['E1'] != undefined ?  hexToFloat("0x"+data['E1'].toString(16)).toFixed(3): 0 )   
            document.getElementById("E2").textContent =(data['E2'] != undefined ?  hexToFloat("0x"+data['E2'].toString(16)).toFixed(3): 0 ) 
            document.getElementById("E3").textContent = (data['E3']!= undefined ?  hexToFloat("0x"+data['E3'].toString(16)).toFixed(3): 0 ) 
            document.getElementById("EVSE1").textContent = data['EVSE1']
            document.getElementById("EVSE2").textContent = data['EVSE2']
            document.getElementById("EVSE3").textContent = data['EVSE3']
            
            var P1 = (data['P1'] > 32767 ?  data['P1'] - 65535 : data['P1'] )
            document.getElementById("P1").textContent = P1
            var P2 =(data['P2'] > 32767 ?  data['P2'] - 65535 : data['P2'] )
            document.getElementById("P2").textContent = P2
            var P3 = (data['P3'] > 32767 ?  data['P3'] - 65535 : data['P3'] )
            document.getElementById("P3").textContent = P3
            chartData =10 //(P1+P2+P3)
             if(cnt == 100){
                refreshEnergyChart()
                cnt = 0
            }else{
                cnt = cnt + 1    
            }
            document.getElementById("time").textContent = getTime();
    
            timer = setTimeout(update_ints_count, ms); 
        });  
}     
$(document).ready(function() 
 {
  $('div.mainContainer').load('datatable',function(){
        $('.loading').hide();
        
        let energyBarChart  = new energyChart()
        let powerLineChart  = new powerChart(refreshPowerChart)
        
        
        let powerChartCtx = document.getElementById('powerGraph').getContext('2d');
        let powerChartConfig = powerLineChart.getConfig()
        powerGraph = new Chart(powerChartCtx, powerChartConfig);
        
        let energyChartCtx = document.getElementById('energyGraph').getContext('2d');
        let energyChartConfig = energyBarChart.getConfig()
        energyGraph = new Chart(energyChartCtx,energyChartConfig)
        
        update_ints_count();
               
    })   
    
    $('.menu a').click(function(e)
    {
        if($(this).attr('id') == 'main'){
            stop(timer);
            $('div.mainContainer').load('datatable', function(){
                let powerLineChart  = new powerChart(refreshPowerChart)
                let powerChartCtx = document.getElementById('powerGraph').getContext('2d');
                let powerChartConfig = powerLineChart.getConfig()
                powerGraph = new Chart(powerChartCtx, powerChartConfig);
                
                let energyBarChart  = new energyChart()        
                let energyChartCtx = document.getElementById('energyGraph').getContext('2d');
                let energyChartConfig = energyBarChart.getConfig()
                energyGraph = new Chart(energyChartCtx,energyChartConfig)

                 update_ints_count();  
            });          
            
         }else if($(this).attr('id') == 'settings'){
             stop(timer);
             $('div.mainContainer').load('settings',function(){
                $('#refreshSSID').append('<span class="spinner-border spinner-border-sm"></span>');
                setting = new Setting()
                setting.refreshWifiClient()
                setting.refreshSetting()
                powerGraph.destroy()
                energyGraph.destroy() 
                      
             
             }); 
            } 
        $('.menu a').removeClass('active');
        $(this).addClass('active');
         
    });  
      
    $(document).on('click','#setSSID',function(){
        $('#setSSID').append('<span class="spinner-border spinner-border-sm"></span>');
        password = document.getElementById("passwordField").value;
        var ssid = $("input[name='ssid']:checked").val();
        if(ssid){
            alert("I will try to connect wifi with ssid: " + ssid);
            $.ajax({
                type: "POST", 
                //the url where you want to sent the userName and password to
                url: '/updateWificlient',
                async: true,
                data: JSON.stringify({"ssid": ssid, "password" :  password }),
                success: function (data) {
                    $('#updateWificlient').html(data.datalayer);
                    if(data["process"] == true){
                        alert("Process was success, Your new IP address is: "+data["ip"])
                    }else{ 
                        alert("Process was unsuccess")   
                    }
                } 
                
            }).success(function() {
                $(this).parent('span').remove();
            });
        }else{ 
            alert("Please choose ssid client first!");
        }
       return 0 
     });
  
    $(document).on('click','#refreshSSID',function(){
        $('div.mainContainer').load('settings',function(){
            $('#refreshSSID').append('<span class="spinner-border spinner-border-sm"></span>');
            setting.refreshWifiClient();
            setting.refreshSetting()
        });
    });
  

 }); 


 function stop() { 
        if (timer) {
            console.log("stopTimer")
            clearTimeout(timer);
            timer = 0;
        }
    } 
 
function getTime(){
    var dt = new Date();
    var time = dt.getHours() + ":" + dt.getMinutes();
    return time;
    }


function refreshPowerChart() {
    powerGraph.config.data.datasets.forEach(function(dataset) {
        dataset.data.push({
            x: Date.now(),
            y: chartData
        });
    });
}
function refreshEnergyChart() {
    
    let dates = [];
    const NUM_OF_DAYS = 31; // get last 31 dates.
 
    for (let i = 0; i < NUM_OF_DAYS; i++) {
          let date = moment();
          date.subtract(i, 'day').format('DD-MM-YYYY');
          dates.push(date.format('YYYY-MM-DD'));
    }
     let data = [11,20,20,20,20,33,30,33,58,52,11,20,20,20,20,33,30,33,58,52,11,20,20,20,20,33,30,33,58,52,23]
    

    for(var i = 0; i<31;i++){
        energyGraph.data.labels[i] = dates[30-i];
        energyGraph.data.datasets[0].data[i] =  data[i];
        energyGraph.update()
    }
    
}

function parseFloat(stri, len) {

  var floatr = 0, sign, order, mantiss,exp,
      intr = 0, multi = 1; 
  if (/^0x/.exec(stri)) {
    intr = parseInt(stri,16);
  }else{
    for (var i = len -1; i >=0; i -= 1) {
      if (stri.charCodeAt(i)>255) {
        console.log('Wrong string parametr'); 
        return false;
      }
      intr += stri.charCodeAt(i) * multi;
      multi *= 256;
    }
  }
  sign = (intr>>>31)?-1:1;
  exp = (intr >>> 23 & 0xff) - 127;
  mantissa = ((intr & 0x7fffff) + 0x800000).toString(2);
  for (i=0; i<mantissa.length; i+=1){
    floatr += parseInt(mantissa[i])? Math.pow(2,exp):0;
    exp--;
  }
  return floatr*sign;
}


function flipHexString(hexValue, hexDigits) {
  var h = hexValue.substr(0, 2);
  for (var i = 0; i < hexDigits; ++i) {
    h += hexValue.substr(2 + (hexDigits - 1 - i) * 2, 2);
  }
  return h;
}


function hexToFloat(hex) {
  var s = hex >> 31 ? -1 : 1;
  var e = (hex >> 23) & 0xFF;
  return s * (hex & 0x7fffff | 0x800000) * 1.0 / Math.pow(2, 23) * Math.pow(2, (e - 127))
}
