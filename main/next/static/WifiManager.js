class WifiManager{
    
    refreshWifiClient() {
    
    $.ajax({
            url: '/updateWificlient' 
        })
        .done(function(data) {
            $('#updateWificlient').html(data.datalayer);
            console.log(data)
            $('.loader').hide();
            for(var key in data) {
               if (data.hasOwnProperty(key)) {
                   var quality = 0
                    if(data[key] <= -100)
                        quality = 0;
                    else if(data[key] >= -50)
                        quality = 100;
                    else 
                        quality = 2 * (data[key] + 100);
                   
                    var radioBtn = $('<input type="radio" name="ssid" value='+key+'>'+key+": "+quality+"%"+"<br>");
                    radioBtn.appendTo('#ssid'); 
                }
            }
        });
    }
       
}