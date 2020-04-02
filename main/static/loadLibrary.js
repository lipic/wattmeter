
function loadLibrary(){
    
    
    requireScript('jquery', '3.4.1', "main/static/jquery-3.4.1.min.js")
    requireScript('moment', '1.0.1', "https://momentjs.com/downloads/moment.js")
    requireScript('chart', '2.7.3', "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.2/Chart.min.js")
    requireScript('chartjs-plugin-streaming', '1.8.1', "https://cdn.jsdelivr.net/npm/chartjs-plugin-streaming@latest/dist/chartjs-plugin-streaming.min.js")
  //  requireScript('energyChart', '1.0.0', "main/static/energyChart.js")
   // requireScript('powerChart', '1.0.0', "main/static/powerChart.js")
   // requireScript('WifiManager', '1.0.0', "main/static/WifiManager.js")
  //  requireScript('func', '1.0.0', "main/static/func.js")
    
    var lib = [  "main/static/energyChart.js",
                 "main/static/powerChart.js",
                 "main/static/WifiManager.js",
                 "main/static/func.js"
        ]
    for(var i in lib){
        var head = document.getElementsByTagName('head')[0];
        var script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = lib[i];
        head.appendChild(script);
    }
}


function loadLibraryFromINTERNET(){
    console.log("load library from INTENET")
      var lib = ["https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js",
                 "https://momentjs.com/downloads/moment.js",
                 "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.2/Chart.min.js",
                 "https://cdn.jsdelivr.net/npm/chartjs-plugin-streaming@latest/dist/chartjs-plugin-streaming.min.js",
                 "main/static/energyChart.js",
                 "main/static/powerChart.js",
                 "main/static/WifiManager.js",
                 "main/static/func.js"
           ]
        for(var i in lib){
            var head = document.getElementsByTagName('head')[0];
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = lib[i];
            head.appendChild(script);
    }
}
