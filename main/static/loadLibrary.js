function loadLibrary(){if(null==isMobile.any()){requireScript("jquery","3.5.1","https://code.jquery.com/jquery-3.5.1.min.js"),requireScript("moment","1.0.0","https://momentjs.com/downloads/moment.js"),requireScript("Chart","2.9.3","https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.3/Chart.min.js"),requireScript("chartjs_plugin","3.5.1","https://unpkg.com/chartjs-plugin-streaming@latest/dist/chartjs-plugin-streaming.min.js"),requireScript("bootstrap_switch_button","1.1.0","https://cdn.jsdelivr.net/gh/gitbrent/bootstrap-switch-button@1.1.0/dist/bootstrap-switch-button.min.js"),requireScript("bootstrap_slider","11.0.2","https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/bootstrap-slider.min.js"),requireScript("energyChart","0.0.0","main/static/energyChart.js"),requireScript("powerChart","0.0.0","main/static/powerChart.js"),requireScript("evse","0.0.1","main/static/evse.js"),requireScript("setting","0.0.0","main/static/setting.js"),requireScript("func","0.0.0","main/static/func.js");var t=["https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css","https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/css/bootstrap-slider.min.css","https://cdn.jsdelivr.net/gh/gitbrent/bootstrap-switch-button@1.1.0/css/bootstrap-switch-button.min.css"];for(var r in t){var e=r;if(!document.getElementById(e)){var i=document.getElementsByTagName("head")[0],s=document.createElement("link");s.id=e,s.rel="stylesheet",s.type="text/css",s.href=t[r],s.media="all",i.appendChild(s)}}}else{requireScript("energyChart","2.0.0","main/static/energyChart.js"),requireScript("powerChart","2.0.0","main/static/powerChart.js"),requireScript("evse","0.0.0","main/static/evse.js"),requireScript("setting","2.0.0","main/static/setting.js");var n=document.getElementsByTagName("head")[0],a=document.createElement("script");a.type="text/javascript",a.src="main/static/func.js",n.appendChild(a)}}var isMobile={Android:function(){return navigator.userAgent.match(/Android/i)},BlackBerry:function(){return navigator.userAgent.match(/BlackBerry/i)},iOS:function(){return navigator.userAgent.match(/iPhone|iPad|iPod/i)},Opera:function(){return navigator.userAgent.match(/Opera Mini/i)},Windows:function(){return navigator.userAgent.match(/IEMobile/i)||navigator.userAgent.match(/WPDesktop/i)},any:function(){return isMobile.Android()||isMobile.BlackBerry()||isMobile.iOS()||isMobile.Opera()||isMobile.Windows()}};
