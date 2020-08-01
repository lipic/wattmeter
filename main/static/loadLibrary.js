function loadLibrary() {
    if(isMobile.any() == null){
             requireScript('jquery', '3.5.1', 'https://code.jquery.com/jquery-3.5.1.min.js');
            requireScript('moment', '1.0.0', 'https://momentjs.com/downloads/moment.js');
            requireScript('Chart', '2.9.3', 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.3/Chart.min.js');
             requireScript('chartjs_plugin', '3.5.1', 'https://unpkg.com/chartjs-plugin-streaming@latest/dist/chartjs-plugin-streaming.min.js');
            requireScript('bootstrap_switch_button', '1.1.0', 'https://cdn.jsdelivr.net/gh/gitbrent/bootstrap-switch-button@1.1.0/dist/bootstrap-switch-button.min.js');
            requireScript('bootstrap_slider', '11.0.2', 'https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/bootstrap-slider.min.js');
        var e = ["main/static/energyChart.js", "main/static/powerChart.js", "main/static/setting.js", "main/static/func.js"];
        for (var t in e) {
            var i = document.getElementsByTagName("head")[0],
            n = document.createElement("script");
            (n.type = "text/javascript"), (n.src = e[t]), i.appendChild(n);
        }
        var g = ["https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
                     "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/css/bootstrap-slider.min.css",
                     "https://cdn.jsdelivr.net/gh/gitbrent/bootstrap-switch-button@1.1.0/css/bootstrap-switch-button.min.css",
                    "main/static/style.css"]
        for (var f in g){
            var cssId = f
            if (!document.getElementById(cssId))
            {
                var head  = document.getElementsByTagName('head')[0];
                var link  = document.createElement('link');
                link.id   = cssId;
                link.rel  = 'stylesheet';
                link.type = 'text/css';
                link.href = g[f];
                link.media = 'all';
                head.appendChild(link);
            }
        }
    }else{
                var e = ["main/static/energyChart.js", "main/static/powerChart.js", "main/static/setting.js", "main/static/func.js"
                 ];
        for (var t in e) {
            var i = document.getElementsByTagName("head")[0],
            n = document.createElement("script");
            (n.type = "text/javascript"), (n.src = e[t]), i.appendChild(n);
        }
        
    
    }
}

var isMobile = {
    Android: function () {
        return navigator.userAgent.match(/Android/i);
    },
    BlackBerry: function () {
        return navigator.userAgent.match(/BlackBerry/i);
    },
    iOS: function () {
        return navigator.userAgent.match(/iPhone|iPad|iPod/i);
    },
    Opera: function () {
        return navigator.userAgent.match(/Opera Mini/i);
    },
    Windows: function () {
        return navigator.userAgent.match(/IEMobile/i) || navigator.userAgent.match(/WPDesktop/i);
    },
    any: function () {
        return isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows();
    },
};
