powerAVGchartData=0,hourEnergyData=[],dailyEnergyData=[];var refreshGraphs=0,cnt=60;function update_ints_count(){$.ajax({url:"/updateData"}).done(function(e){$("#updateData").html(e.datalayer),dailyEnergyData=e.E_Daily,document.getElementById("RUN_TIME").textContent=e.RUN_TIME,document.getElementById("WATTMETER_TIME").textContent=e.WATTMETER_TIME;var t=e.U1,n=e.U2,a=e.U3;document.getElementById("U1").textContent=t,document.getElementById("U2").textContent=n,document.getElementById("U3").textContent=a;var r=((e.I1>32767?e.I1-65535:e.I1)/100).toFixed(2),o=((e.I2>32767?e.I2-65535:e.I2)/100).toFixed(2),d=((e.I3>32767?e.I3-65535:e.I3)/100).toFixed(2);document.getElementById("I1").textContent=r,document.getElementById("I2").textContent=o,document.getElementById("I3").textContent=d;var i=((e.P1>32767?e.P1-65535:e.P1)/1e3).toFixed(2),l=((e.P2>32767?e.P2-65535:e.P2)/1e3).toFixed(2),s=((e.P3>32767?e.P3-65535:e.P3)/1e3).toFixed(2);document.getElementById("P1").textContent=i,document.getElementById("P2").textContent=l,document.getElementById("P3").textContent=s;var y=((e.S1>32767?e.S1-65535:e.S1)/1e3).toFixed(2),u=((e.S2>32767?e.S2-65535:e.S2)/1e3).toFixed(2),g=((e.S3>32767?e.S3-65535:e.S3)/1e3).toFixed(2);document.getElementById("S1").textContent=y,document.getElementById("S2").textContent=u,document.getElementById("S3").textContent=g,e.HDO>0?(document.getElementById("HDO").textContent="ON",document.getElementById("HDO").style.color="#74DF00"):(document.getElementById("HDO").textContent="OFF",document.getElementById("HDO").style.color="#FF0000"),document.getElementById("PF1").textContent=(e.PF1/100).toFixed(2),document.getElementById("PF2").textContent=(e.PF2/100).toFixed(2),document.getElementById("PF3").textContent=(e.PF3/100).toFixed(2),document.getElementById("PP1_peak").textContent=(e.PP1_peak/1e3).toFixed(2),document.getElementById("PP2_peak").textContent=(e.PP2_peak/1e3).toFixed(2),document.getElementById("PP3_peak").textContent=(e.PP3_peak/1e3).toFixed(2),document.getElementById("PN1_peak").textContent=(e.PN1_peak/1e3).toFixed(2),document.getElementById("PN2_peak").textContent=(e.PN2_peak/1e3).toFixed(2),document.getElementById("PN3_peak").textContent=(e.PN3_peak/1e3).toFixed(2),document.getElementById("Total_Energy_positive").textContent=(e.E_previousDay_positive/100).toFixed(2),document.getElementById("Total_Energy_negative").textContent=e.E_previousDay_negative>0?((65535-e.E_previousDay_negative)/100).toFixed(2):(0).toFixed(2),document.getElementById("Previous_Energy_positive").textContent=(e.E_previousDay_positive/100).toFixed(2),document.getElementById("Previous_Energy_negative").textContent=(e.E_previousDay_negative/100).toFixed(2),document.getElementById("Current_Energy_positive").textContent=(e.E_currentDay_positive/100).toFixed(2),document.getElementById("Current_Energy_negative").textContent=(e.E_currentDay_negative/100).toFixed(2),document.getElementById("Total_Energy_positive").textContent=((e.E1_total_positive+e.E2_total_positive+e.E3_total_positive)/100).toFixed(2),document.getElementById("Total_Energy_negative").textContent=((e.E1_total_negative+e.E2_total_negative+e.E3_total_negative)/100).toFixed(2),powerAVGchartData=e.P_minuten,hourEnergyData=e.E_hour,document.getElementById("ACTUAL_CONFIG_CURRENT").textContent=e.ACTUAL_CONFIG_CURRENT,document.getElementById("ACTUAL_OUTPUT_CURRENT").textContent=e.ACTUAL_OUTPUT_CURRENT,document.getElementById("EV_STATE").textContent=e.EV_STATE,cnt>=60?(refreshEnergyChartHourly(),cnt=0):cnt++,"green"==document.getElementById("refresh").style.backgroundColor?document.getElementById("refresh").style.backgroundColor="":document.getElementById("refresh").style.backgroundColor="green",timer=setTimeout(update_ints_count,1e3)})}function stop(){timer&&(console.log("stopTimer"),clearTimeout(timer),timer=0)}function loadPowerChart(){len=powerAVGchartData[0];for(var e=1;e<61-len;e++)powerGraph.config.data.datasets.forEach(function(t){t.data.push({x:Date.now()-1e3*(61-e)*60,y:0})});for(e=1;e<len;e++){var t=0;t=null!=powerAVGchartData[e]?powerAVGchartData[e]:0,powerGraph.config.data.datasets.forEach(function(n){n.data.push({x:Date.now()-1e3*(len-e)*60,y:t})})}powerGraph.update()}function refreshPowerChart(){len=powerAVGchartData[0],powerGraph.config.data.datasets.forEach(function(e){e.data.push({x:Date.now(),y:powerAVGchartData[len-1]})})}function refreshEnergyChartHourly(){len=hourEnergyData[0];for(var e=0,t=0,n=0,a=0,r=0;r<24;r++)null!=hourEnergyData[2*r+3]?(e=hourEnergyData[2*r+1],dataP=hourEnergyData[2*r+2],dataN=hourEnergyData[2*r+3],console.log("EnergyData: ",hourEnergyData),n=n+dataP-dataN,a+=1,energyGraphHourly.data.labels[24-((len-1)/3-r)]=e+1<10?"0"+e+"-0"+(e+1):e+1==10?"09-10":e+"-"+(e+1),energyGraphHourly.data.datasets[0].data[24-((len-1)/3-r)]=dataP,energyGraphHourly.data.datasets[1].data[24-((len-1)/3-r)]=-dataN):(e<23?(e+=1,energyGraphHourly.data.labels[t]=e+1<10?"0"+e+"-0"+(e+1):e+1==10?"09-10":e+"-"+(e+1),energyGraphHourly.data.datasets[0].data[t]=0,energyGraphHourly.data.datasets[1].data[t]=0,t++):(e=0,energyGraphHourly.data.labels[t]="0"+e+"-0"+(e+1),energyGraphHourly.data.datasets[0].data[t]=0,energyGraphHourly.data.datasets[1].data[t]=0,t++),t>23&&(t=0));for(r=0;r<24;r++)energyGraphHourly.data.datasets[2].data[23-r]=(n/a).toFixed(1);energyGraphHourly.update()}function refreshEnergyChartDaily(){var e=0,t=1;null!=dailyEnergyData&&(t=dailyEnergyData.length-1);var n=0,a=0;days=Last31Days();for(var r=0;r<31;r++)null!=dailyEnergyData&&null!=dailyEnergyData[t-r]?(arr=dailyEnergyData[t-r].split(":"),console.log("ARR: ",arr),e=arr[0],dat=JSON.parse(arr[1]),dataP=dat[0],dataN=dat[1],energyGraphDaily.data.labels[30-r]=e,n=n+parseFloat(dataP/100)-parseFloat(dataN/100),a+=1,energyGraphDaily.data.datasets[0].data[30-r]=parseFloat(dataP/100).toFixed(1),energyGraphDaily.data.datasets[1].data[30-r]=-parseFloat(dataN/100).toFixed(1)):(energyGraphDaily.data.labels[30-r]=days[r],energyGraphDaily.data.datasets[0].data[30-r]=0,energyGraphDaily.data.datasets[1].data[30-r]=0);for(r=0;r<31;r++){var o=(n/a).toFixed(1);energyGraphDaily.data.datasets[2].data[30-r]=o}energyGraphDaily.update()}function Last31Days(){for(var e=[],t=1;t<32;t++){var n=new Date;n.setDate(n.getDate()-t),e.push(formatDate(n))}return e}function formatDate(e){var t=e.getDate(),n=e.getMonth()+1,a=e.getFullYear().toString().substr(-2);return t<10&&(t="0"+t),n<10&&(n="0"+n),e=(n+"/"+t+"/"+a).toString()}$(function(){$("div.mainContainer").load("datatable",function(){$(".loader").hide(100);let e=new energyChart("Hourly E [Wh]","Wh"),t=new energyChart("Daily E [kWh]","kWh"),n=new powerChart(refreshPowerChart),a=document.getElementById("powerGraph"),r=n.getConfig();powerGraph=new Chart(a,r);let o=document.getElementById("energyGraph_hourly"),d=e.getConfig(24);energyGraphHourly=new Chart(o,d);let i=document.getElementById("energyGraph_daily"),l=t.getConfig(31);energyGraphDaily=new Chart(i,l),update_ints_count(),setTimeout(function(){loadPowerChart()},2e3),setTimeout(function(){refreshEnergyChartHourly()},2e3),setTimeout(function(){refreshEnergyChartDaily()},2e3)}),$(".menu a").click(function(e){"main"==$(this).attr("id")?(stop(timer),$("div.mainContainer").load("datatable",function(){let e=new powerChart(refreshPowerChart),t=document.getElementById("powerGraph"),n=e.getConfig();powerGraph=new Chart(t,n);let a=new energyChart("Hourly E [Wh]","Wh"),r=document.getElementById("energyGraph_hourly"),o=a.getConfig(24);energyGraphHourly=new Chart(r,o);let d=new energyChart("Daily  E [kWh]","kWh"),i=document.getElementById("energyGraph_daily"),l=d.getConfig(31);energyGraphDaily=new Chart(i,l),update_ints_count(),setTimeout(function(){loadPowerChart()},500),setTimeout(function(){refreshEnergyChartHourly()},500),setTimeout(function(){refreshEnergyChartDaily()},500)})):"settings"==$(this).attr("id")&&(stop(timer),$("div.mainContainer").load("settings",function(){$("#refreshSSID").append('<span class="spinner-border spinner-border-sm"></span>'),setting=new Setting,setting.refreshSetting(),setTimeout(function(){setting.refreshWifiClient()},500),powerGraph.destroy(),energyGraphHourly.destroy(),energyGraphDaily.destroy()})),$(".menu a").removeClass("active"),$(this).addClass("active")}),$(document).on("click","#setSSID",function(){$("#setSSID").append('<span class="spinner-border spinner-border-sm"></span>'),password=document.getElementById("passwordField").value;var e=$("input[name='ssid']:checked").val();return e?$.ajax({type:"POST",url:"/updateWificlient",async:!0,data:JSON.stringify({ssid:e,password:password}),success:function(t){$("#updateWificlient").html(t.datalayer),console.log(t),$("#setSSID").find("span").remove(),1==t.process?(document.getElementById("wifiStatus").innerHTML="Success connection to: "+e,document.getElementById("wifiStatus").style.color="#74DF00"):(document.getElementById("wifiStatus").innerHTML="Error during connection to: "+e,document.getElementById("wifiStatus").style.color="#FF0000")}}):(document.getElementById("wifiStatus").innerHTML="Please choose ssid client first!",document.getElementById("wifiStatus").style.color="#FF0000"),0}),$(document).on("click","#readReg",function(){return register=document.getElementById("modbusReg").value,document.getElementById("modbusIO").value="waiting ...",register>0?$.ajax({type:"POST",url:"/readRegister",async:!0,data:JSON.stringify({register:register}),success:function(e){$("#readRegister").html(e.datalayer),$(this).parent("span").remove(),document.getElementById("modbusIO").value=e.data}}):(alert("Please choose register betwean 1-10000"),$(this).parent("span").remove()),0}),$(document).on("click","#refreshSSID",function(){for(;document.getElementById("ssid").firstChild;)document.getElementById("ssid").removeChild(document.getElementById("ssid").firstChild);document.getElementById("wifiStatus").innerHTML="",$("#refreshSSID").append('<span class="spinner-border spinner-border-sm"></span>'),setting.refreshWifiClient()})});
