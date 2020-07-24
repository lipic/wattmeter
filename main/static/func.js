powerAVGchartData = 0
hourEnergyData = []
dailyEnergyData = []
var refreshGraphs = 0
var cnt = 60
function update_ints_count() {
    
    $.ajax({ 
            url: '/updateData' 
        })
        .done(function(data) {
            var ms = 1000
            $('#updateData').html(data.datalayer);
            
            dailyEnergyData = data['E_Daily']            
            document.getElementById("RUN_TIME").textContent = data['RUN_TIME'] 
            document.getElementById("WATTMETER_TIME").textContent = data['WATTMETER_TIME']
            
            var U1 = data['U1'] 
            var U2 = data['U2']
            var U3 = data['U3']
            document.getElementById("U1").textContent = U1
            document.getElementById("U2").textContent = U2
            document.getElementById("U3").textContent = U3
            
            var I1 =((data['I1'] > 32767 ?  data['I1'] - 65535 : data['I1'] )/100).toFixed(2)
            var I2 = ((data['I2'] > 32767 ?  data['I2'] - 65535 : data['I2'] )/100).toFixed(2)
            var I3 = ((data['I3'] > 32767 ?  data['I3'] - 65535 : data['I3'] )/100).toFixed(2)
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
            
            
            var S1 =  ((data['S1'] > 32767 ?  data['S1'] - 65535 : data['S1'] )/1000).toFixed(2)
            var S2 =  ((data['S2'] > 32767 ?  data['S2'] - 65535 : data['S2'] )/1000).toFixed(2)
            var S3 = ((data['S3'] > 32767 ?  data['S3'] - 65535 : data['S3'] )/1000).toFixed(2)
            
             var PowerS = S1 + S2 +S3
            document.getElementById("S1").textContent = S1 
            document.getElementById("S2").textContent = S2
            document.getElementById("S3").textContent = S3

            if(data['HDO'] > 0){
                document.getElementById("HDO").textContent = "ON"
                document.getElementById("HDO").style.color =  "#74DF00"
            }else{
                document.getElementById("HDO").textContent = "OFF"
                document.getElementById("HDO").style.color = "#FF0000"
            }    
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
                refreshEnergyChartHourly()
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
$(function() 
 {
  $('div.mainContainer').load('datatable',function(){
        $('.loader').hide(100);
        let energyBarChartHourly  = new energyChart('Hourly E [Wh]','Wh')
        let energyBarChartDaily  = new energyChart('Daily E [kWh]','kWh')
        let powerLineChart  = new powerChart(refreshPowerChart)
        
        let powerChartCtx = document.getElementById('powerGraph');
        let powerChartConfig = powerLineChart.getConfig()
        powerGraph = new Chart(powerChartCtx, powerChartConfig);
        
        let energyChartCtxHourly = document.getElementById('energyGraph_hourly');
        let energyChartConfigHourly = energyBarChartHourly.getConfig(24)
        energyGraphHourly = new Chart(energyChartCtxHourly,energyChartConfigHourly)
        
        let energyChartCtxDaily = document.getElementById('energyGraph_daily');
        let energyChartConfigDaily  = energyBarChartDaily.getConfig(31)
        energyGraphDaily  = new Chart(energyChartCtxDaily,energyChartConfigDaily)
                
        update_ints_count(); 
        setTimeout(function(){loadPowerChart()}, 2000);
        setTimeout(function(){refreshEnergyChartHourly()}, 2000); 
        setTimeout(function(){refreshEnergyChartDaily()}, 2000);
               
    })   
    
    $('.menu a').click(function(e)
    { 
        if($(this).attr('id') == 'main'){
            stop(timer);
            $('div.mainContainer').load('datatable', function(){
                let powerLineChart  = new powerChart(refreshPowerChart)
                let powerChartCtx = document.getElementById('powerGraph');
                let powerChartConfig = powerLineChart.getConfig()
                powerGraph = new Chart(powerChartCtx, powerChartConfig);
                
                let energyBarChartHourly  = new energyChart('Hourly E [Wh]','Wh')        
                let energyChartCtxHourly = document.getElementById('energyGraph_hourly');
                let energyChartConfigHourly = energyBarChartHourly.getConfig(24)
                energyGraphHourly = new Chart(energyChartCtxHourly,energyChartConfigHourly)
                
                let energyBarChartDaily   = new energyChart('Daily  E [kWh]','kWh')        
                let energyChartCtxDaily  = document.getElementById('energyGraph_daily');
                let energyChartConfigDaily  = energyBarChartDaily .getConfig(31)
                energyGraphDaily  = new Chart(energyChartCtxDaily ,energyChartConfigDaily )
                
                 update_ints_count();
                 setTimeout(function(){loadPowerChart()}, 500);
                 setTimeout(function(){refreshEnergyChartHourly()}, 500);
                setTimeout(function(){refreshEnergyChartDaily()}, 500);
            });          
            
         }else if($(this).attr('id') == 'settings'){
             stop(timer);
             $('div.mainContainer').load('settings',function(){
                $('#refreshSSID').append('<span class="spinner-border spinner-border-sm"></span>');
                setting = new Setting()
                setting.refreshSetting()
                setTimeout(function(){setting.refreshWifiClient()}, 500);
                powerGraph.destroy()
                energyGraphHourly.destroy()
                energyGraphDaily.destroy()

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
            $.ajax({
                type: "POST", 
                url: '/updateWificlient',
                async: true,
                data: JSON.stringify({"ssid": ssid, "password" :  password }),
                success: function (data) {
                    $('#updateWificlient').html(data.datalayer);
                    console.log(data)
                    $('#setSSID').find('span').remove();
                    if(data["process"] == true){
                        document.getElementById("wifiStatus").innerHTML = "Success connection to: "+ssid
                        document.getElementById("wifiStatus").style.color = "#74DF00"
                    }else{ 
                        document.getElementById("wifiStatus").innerHTML = "Error during connection to: "+ ssid
                        document.getElementById("wifiStatus").style.color = "#FF0000"
                    }
                } 
            })
        }else{
            document.getElementById("wifiStatus").innerHTML = "Please choose ssid client first!"
            document.getElementById("wifiStatus").style.color = "#FF0000"
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
            while (document.getElementById("ssid").firstChild) {
                document.getElementById("ssid").removeChild(document.getElementById("ssid").firstChild);
            }
            document.getElementById('wifiStatus').innerHTML = ""
            $('#refreshSSID').append('<span class="spinner-border spinner-border-sm"></span>');
            setting.refreshWifiClient();
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

function refreshEnergyChartHourly() {
    len = hourEnergyData[0]
    var data = 0
    var hour = 0
    var startH = 0
    var energyAvg = 0
    var numb = 0
    
    for(var i = 0; i<24;i++){
        if(hourEnergyData[(2*i)+3] != undefined){
            hour =  hourEnergyData[(2*i)+1];
            dataP = hourEnergyData[(2*i)+2];
            dataN = hourEnergyData[(2*i)+3];
            console.log("EnergyData: ",hourEnergyData)
            energyAvg = energyAvg + dataP - dataN;
            numb = numb + 1;
            energyGraphHourly.data.labels[24 - (((len-1)/3)-i)] = (((hour+1)<10)?("0"+(hour)+"-"+"0"+(hour+1)):(((hour+1)==10)?"09-10":(hour)+"-"+(hour+1)));
            energyGraphHourly.data.datasets[0].data[24 - (((len-1)/3) - i)] =  dataP;
            energyGraphHourly.data.datasets[1].data[24 - (((len-1)/3) -i)] =  -dataN;
        }else{
            if(hour<23){
                hour = hour +1;
                energyGraphHourly.data.labels[startH] = (((hour+1)<10)?("0"+(hour)+"-"+"0"+(hour+1)):(((hour+1)==10)?"09-10":(hour)+"-"+(hour+1)));
                energyGraphHourly.data.datasets[0].data[startH] =  0;
                energyGraphHourly.data.datasets[1].data[startH] =  0;
                startH++;
            }else{
                hour=0;
                energyGraphHourly.data.labels[startH] = "0"+(hour) + "-0"+(hour+1);
                energyGraphHourly.data.datasets[0].data[startH] =  0;
                energyGraphHourly.data.datasets[1].data[startH] =  0;
                startH++;
            }
            if(startH > 23){
                startH = 0    
            }
        }
    }
    for(var i = 0; i<24;i++){
        energyGraphHourly.data.datasets[2].data[23-i] = (energyAvg/numb).toFixed(1)
    }
    energyGraphHourly.update()
}

function refreshEnergyChartDaily() {
    var data = 0
    var day = 0
    var len  = 1
    if(dailyEnergyData != null){
        len = dailyEnergyData.length-1
    }
    var energyAvgD = 0
    var numb = 0
    days = Last31Days ()
    for(var i = 0; i<31;i++){
        if(dailyEnergyData != null){
            if(dailyEnergyData[len - i] != undefined){
                arr = dailyEnergyData[len-i].split(':')
                console.log("ARR: ",arr)
                day  = arr [0]
                dat = JSON.parse(arr[1])
                dataP= dat[0]
                dataN= dat[1]
                energyGraphDaily.data.labels[30-i] = day;
                energyAvgD = energyAvgD + parseFloat(dataP/100)- parseFloat(dataN/100)
                numb = numb + 1
                energyGraphDaily.data.datasets[0].data[30-i] =  parseFloat(dataP/100).toFixed(1)
                energyGraphDaily.data.datasets[1].data[30-i] =  -parseFloat(dataN/100).toFixed(1)
            }else{
                energyGraphDaily.data.labels[30-i] = days[i];
                energyGraphDaily.data.datasets[0].data[30-i] =  0
                energyGraphDaily.data.datasets[1].data[30-i] =  0
            }
        }
        else{
            energyGraphDaily.data.labels[30-i] = days[i];
            energyGraphDaily.data.datasets[0].data[30-i] =  0
            energyGraphDaily.data.datasets[1].data[30-i] =  0
        }
    }
    
        for(var i = 0; i<31;i++){
            var resultAvg =  (energyAvgD/numb).toFixed(1)
            energyGraphDaily.data.datasets[2].data[30-i] = resultAvg
        }
    
    energyGraphDaily.update()

}

function Last31Days () {
    var result = [];
    for (var i=1; i<32; i++) {
        var d = new Date();
        d.setDate(d.getDate() - i);
        result.push(formatDate(d))
    }

    return(result);
}
function formatDate(date){

    var dd = date.getDate();
    var mm = date.getMonth()+1;
    var yy = date.getFullYear().toString().substr(-2);
    if(dd<10) {dd='0'+dd}
    if(mm<10) {mm='0'+mm}
    date = (mm+'/'+dd+'/'+yy).toString();
    return date
 }