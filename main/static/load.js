var lib = ["https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js","main/static/WifiManager.js","main/static/func.js","https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.2/Chart.min.js"]
function loadLibrary(){

    for(var i in lib){
        var head = document.getElementsByTagName('head')[0];
        var script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = lib[i];
        head.appendChild(script);
    }
} 