
function loadLibrary(){
    if( isMobile.any() == null){
        /*
        requireScript('jquery', '3.4.1', "https://code.jquery.com/jquery-3.5.1.min.js")
        requireScript('bootstrap-switch','3.3.4',"https://cdnjs.cloudflare.com/ajax/libs/bootstrap-switch/3.3.4/js/bootstrap-switch.min.js")
        requireScript('moment', '1.0.1', "https://momentjs.com/downloads/moment.js")
        requireScript('chart', '2.7.3', "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.2/Chart.min.js")
        requireScript('chartjs-plugin-streaming', '1.8.1', "https://cdn.jsdelivr.net/npm/chartjs-plugin-streaming@latest/dist/chartjs-plugin-streaming.min.js")

        addCss("https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css")
        addCss("https://cdnjs.cloudflare.com/ajax/libs/bootstrap-switch/3.3.4/css/bootstrap3/bootstrap-switch.min.css")*/
    }
    var lib = [  "main/static/energyChart.js",
                 "main/static/powerChart.js",
                 "main/static/setting.js",
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

function addCss(fileName) {

  var head = document.head;
  var link = document.createElement("link");

  link.type = "text/css";
  link.rel = "stylesheet";
  link.href = fileName;

  head.appendChild(link);
}


var isMobile = {
    Android: function() {
        return navigator.userAgent.match(/Android/i);
    },
    BlackBerry: function() {
        return navigator.userAgent.match(/BlackBerry/i);
    },
    iOS: function() {
        return navigator.userAgent.match(/iPhone|iPad|iPod/i);
    },
    Opera: function() {
        return navigator.userAgent.match(/Opera Mini/i);
    },
    Windows: function() {
        return navigator.userAgent.match(/IEMobile/i) || navigator.userAgent.match(/WPDesktop/i);
    },
    any: function() {
        return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
    }
};
