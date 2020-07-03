var timer;

powerAVGchartData = 0
hourEnergyData = 0
var refreshGraphs = 0
var cnt = 60
var dataCnt = 0
function update_ints_count() {
    
    $.ajax({ 
            url: '/updateData' 
        })
        .done(function(data) {
            var ms = 1000
            $('#updateData').html(data.datalayer);
            
            var U1 = data['U1'] 
            var U2 = data['U2']
            var U3 = data['U3']
            document.getElementById("U1").textContent = U1
            document.getElementById("U2").textContent = U2
            document.getElementById("U3").textContent = U3
            
            var I1 =((data['I1'] > 32767 ?  data['I1'] - 65535 : data['I1'] )/1000).toFixed(1)
            var I2 = ((data['I2'] > 32767 ?  data['I2'] - 65535 : data['I2'] )/1000).toFixed(1)
            var I3 = ((data['I3'] > 32767 ?  data['I3'] - 65535 : data['I3'] )/1000).toFixed(1)
            document.getElementById("I1").textContent = I1
            document.getElementById("I2").textContent = I2
            document.getElementById("I3").textContent = I3
            
            var P1 =  ((data['P1'] > 32767 ?  data['P1'] - 65535 : data['P1'] )/1000).toFixed(2)
            var P2 =  ((data['P2'] > 32767 ?  data['P2'] - 65535 : data['P2'] )/1000).toFixed(2)
            var P3 = ((data['P3'] > 32767 ?  data['P3'] - 65535 : data['P3'] )/1000).toFixed(2)
            
             var Power = P1 + P2 +P3
            document.getElementById("P1").textContent = P1
            document.getElementById("P2").textContent = P2
            document.getElementById("P3").textContent = P3

            document.getElementById("PF1").textContent = (data['PF1']/100).toFixed(2)
            document.getElementById("PF2").textContent = (data['PF2']/100).toFixed(2)
            document.getElementById("PF3").textContent = (data['PF3']/100).toFixed(2)
            
            document.getElementById("PP1_peak").textContent = (data['PP1_peak']/1000).toFixed(2)
            document.getElementById("PP2_peak").textContent = (data['PP2_peak']/1000).toFixed(2)
            document.getElementById("PP3_peak").textContent = (data['PP3_peak']/1000).toFixed(2)
            
            document.getElementById("PN1_peak").textContent = (data['PN1_peak']/1000).toFixed(2)
            document.getElementById("PN2_peak").textContent = (data['PN2_peak']/1000).toFixed(2)
            document.getElementById("PN3_peak").textContent = (data['PN3_peak']/1000).toFixed(2)
            
            document.getElementById("Total_Energy_positive").textContent = (data["E_previousDay_positive"]/100).toFixed(2)
            document.getElementById("Total_Energy_negative").textContent = ((data["E_previousDay_negative"] > 0) ? ((65535-data["E_previousDay_negative"])/100).toFixed(2): 0.0.toFixed(2))

            document.getElementById("Previous_Energy_positive").textContent  = (data["E_previousDay_positive"]/100).toFixed(2)
            document.getElementById("Previous_Energy_negative").textContent  = (data["E_previousDay_negative"]/100).toFixed(2)
            
            document.getElementById("Current_Energy_positive").textContent  = (data["E_currentDay_positive"]/100).toFixed(2)
            document.getElementById("Current_Energy_negative").textContent  = (data["E_currentDay_negative"]/100).toFixed(2)
            
            
            document.getElementById("Total_Energy_positive").textContent = (((data['E1_total_positive']) + (data['E2_total_positive']) + (data['E3_total_positive']))/100).toFixed(2)
            document.getElementById("Total_Energy_negative").textContent =(((data['E1_total_negative']) + (data['E2_total_negative']) + (data['E3_total_negative']))/100).toFixed(2)
            
            powerAVGchartData = data["P_minuten"]
            hourEnergyData = data['E_hour']
            
           
            document.getElementById("ACTUAL_CONFIG_CURRENT").textContent = data['ACTUAL_CONFIG_CURRENT']
            document.getElementById("ACTUAL_OUTPUT_CURRENT").textContent = data['ACTUAL_OUTPUT_CURRENT']
            document.getElementById("EV_STATE").textContent = data['EV_STATE']
            

          if(cnt >= 60){
                refreshEnergyChart()
                cnt = 0
            }else{
                cnt++;    
            }
            
            if(document.getElementById("refresh").style.backgroundColor == 'green'){
                document.getElementById("refresh").style.backgroundColor = ''
            }else{
                document.getElementById("refresh").style.backgroundColor = 'green'
            }
            timer = setTimeout(update_ints_count, ms); 
        });  
}     
$(document).ready(function() 
 {
  $('div.mainContainer').load('datatable',function(){
        $('.loader').hide(300);
        
        let energyBarChart  = new energyChart('Hourly energy consumption [Wh]','Wh')
        let powerLineChart  = new powerChart(refreshPowerChart)
        
        
        let powerChartCtx = document.getElementById('powerGraph').getContext('2d');
        let powerChartConfig = powerLineChart.getConfig()
        powerGraph = new Chart(powerChartCtx, powerChartConfig);
        
        let energyChartCtx = document.getElementById('energyGraph').getContext('2d');
        let energyChartConfig = energyBarChart.getConfig()
        energyGraph = new Chart(energyChartCtx,energyChartConfig)
        
        update_ints_count();
        setTimeout(function(){loadPowerChart()}, 2000);
        setTimeout(function(){refreshEnergyChart()}, 2000);
               
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
                
                let energyBarChart  = new energyChart('Hourly energy consumption [Wh]','Wh')        
                let energyChartCtx = document.getElementById('energyGraph').getContext('2d');
                let energyChartConfig = energyBarChart.getConfig()
                energyGraph = new Chart(energyChartCtx,energyChartConfig)
                 update_ints_count();
                 setTimeout(function(){loadPowerChart()}, 1000);
                 setTimeout(function(){refreshEnergyChart()}, 1000);
            });          
            
         }else if($(this).attr('id') == 'settings'){
             stop(timer);
             $('div.mainContainer').load('settings',function(){
                $('#refreshSSID').append('<span class="spinner-border spinner-border-sm"></span>');
                setting = new Setting()
                setting.refreshSetting()
                setTimeout(function(){setting.refreshWifiClient()}, 500);
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
  
  
      $(document).on('click','#readReg',function(){
        register = document.getElementById("modbusReg").value;
        document.getElementById("modbusIO").value = "waiting ..."
        if(register>0){
            $.ajax({
                type: "POST", 
                url: '/readRegister',
                async: true,
                data: JSON.stringify({"register": register}),
                success: function (data) {
                    
                    $('#readRegister').html(data.datalayer);
                    $(this).parent('span').remove();
                    document.getElementById("modbusIO").value =  data["data"] 
                    
                } 
                
            })
        }else{ 
            alert("Please choose register betwean 1-10000");
             $(this).parent('span').remove();
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

function loadPowerChart(){
    len = powerAVGchartData[0]
    
    for(var i = 1; i<(61-len);i++){
        powerGraph.config.data.datasets.forEach(function(dataset) {
            dataset.data.push({
                x: (Date.now() - (1000*(61-i)*60)),
                y: 0
            });
        });
    }
    
    for(var i = 1; i<len;i++){
        var data = 0 
        if(powerAVGchartData[i] != undefined){ 
            data = powerAVGchartData[i];
        }else{
            data = 0;
        }
        powerGraph.config.data.datasets.forEach(function(dataset) {
            dataset.data.push({
                x: (Date.now() - (1000*(len-i)*60)),
                y: data
            });
        });
    }
    powerGraph.update()
} 

function refreshPowerChart() {

    
    len = powerAVGchartData[0]
    
    powerGraph.config.data.datasets.forEach(function(dataset) {
        dataset.data.push({
            x: Date.now(),
            y: (powerAVGchartData[len-1])
        });
    });
}

function refreshEnergyChart() {
    len = hourEnergyData[0]
    console.log("Delka:"+len)
    console.log("Data:"+hourEnergyData)
    var data = 0
    var hour = 0
    var startH = 0
    for(var i = 0; i<24;i++){
        if(hourEnergyData[(2*i)+2] != undefined){
            hour =  hourEnergyData[(2*i)+1];
            data = hourEnergyData[(2*i)+2];
            energyGraph.data.labels[24 - (((len-1)/2)-i)] = (hour)+"h";
            energyGraph.data.datasets[0].data[24 - (((len-1)/2)-i)] =  data;
        }else{
            if(hour<23){
                hour = hour +1;
                energyGraph.data.labels[startH] = (hour)+"h";
                energyGraph.data.datasets[0].data[startH] =  0;
                startH++;
            }else{
                hour=0;
                energyGraph.data.labels[startH] = (hour)+"h";
                energyGraph.data.datasets[0].data[startH] =  0;
                startH++;
            }
            if(startH > 23){
                startH = 0    
            }
        }
    }
    energyGraph.update()
}

