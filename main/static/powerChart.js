class powerChart{constructor(a){this.refresher=a}getConfig(){var a="#828389",b="#34ECE1";return{type:"line",data:{labels:[],datasets:[{pointRadius:0,label:translate("power")+" [W]",color:a,backgroundColor:(0,Chart.helpers.color)(b).alpha(0).rgbString(),borderColor:b,fill:0,lineTension:0,data:[]}]},options:{legend:{position:"top",labels:{boxWidth:0,fontColor:a,fontSize:16}},maintainAspectRatio:!1,responsive:!0,scales:{xAxes:[{type:"realtime",realtime:{duration:36e5,refresh:6e4,delay:2e3,onRefresh:this.refresher},ticks:{fontColor:a,fontSize:16},gridLines:{display:!1}}],yAxes:[{scaleLabel:{display:!0,fontColor:a},gridLines:{display:!1},ticks:{fontColor:a,fontSize:16,suggestedMax:500}}]},tooltips:{mode:"nearest",intersect:!1},hover:{mode:"nearest",intersect:!1}}}}}