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
            var e1 =  (data['E1'] != undefined ?  ((hexToFloat("0x"+data['E1'].toString(16)))/1000): 0.0 )
            var e2 =  (data['E2'] != undefined ?  ((hexToFloat("0x"+data['E2'].toString(16)))/1000): 0.0 )
            var e3 =  (data['E3'] != undefined ?  ((hexToFloat("0x"+data['E3'].toString(16)))/1000): 0.0 )
            var energy = parseFloat(e1) + parseFloat(e2)+ parseFloat(e3)
            console.log(energy)
            document.getElementById("Energy").textContent = energy.toFixed(3)
            document.getElementById("EVSE1").textContent = data['EVSE1']
            document.getElementById("EVSE2").textContent = data['EVSE2']
            document.getElementById("EVSE3").textContent = data['EVSE3']
            
            var Power = (data['P1'] > 32767 ?  data['P1'] - 65535 : data['P1'] ) + (data['P2'] > 32767 ?  data['P2'] - 65535 : data['P2'] ) +   (data['P3'] > 32767 ?  data['P3'] - 65535 : data['P3'] )
            document.getElementById("Power").textContent = Power

            chartData = Power
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
    var time = dt.getHours() + " : " + dt.getMinutes() + " : "+ dt.getSeconds();
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


function hexToFloat(hex) {
  var s = hex >> 31 ? -1 : 1;
  var e = (hex >> 23) & 0xFF;
  return s * (hex & 0x7fffff | 0x800000) * 1.0 / Math.pow(2, 23) * Math.pow(2, (e - 127))
}
