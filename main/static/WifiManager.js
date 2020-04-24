function Setting(){
    self = this;
    this.refreshWifiClient = function() {
    
    $.ajax({
            url: '/updateWificlient' 
        })
        .done(function(data) {
            $('#updateWificlient').html(data.datalayer);
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
            $('#refreshSSID').find("span").remove();
        });
    }
    
    
    
    this.refreshSetting = function() {
        $.ajax({
            url: '/updateSetting' 
        })
        .done(function(data) {
            $('#updateSetting').html(data.datalayer);
            for(var key in data) {
               if (data.hasOwnProperty(key)) {
                    var settingArray = $('<div class="row">  <div class="col" >  <p>'+key+'</p> </div>  <div class="col">  <input id="'+key+'"  type="checkbox" name="btn-checkbox" onclick="alert('+key+')" data-toggle="witchbutton"> </div> </div>');
                    settingArray.appendTo('#settingTable');
                    
                    if((data[key])=="True"){        
                        document.getElementById(key).switchButton('on', true);
                    }else{
                        document.getElementById(key).switchButton('off', false);           
                    }
                }
            }
            $('.switch input[type="checkbox"]').on('change', function() {
                self.saveSetting($(this).attr("id"),$(this).prop('checked') );
            });
    
        });
    }

       this.saveSetting = function(id,value){
           console.log(id)
            $.ajax({
                type: "POST", 
                url: '/updateSetting',
                async: true,
                data: JSON.stringify({"variable": id, "value" :  value }),
                success: function (data) {
                    $('#updateSetting').html(data.datalayer);
                    if(data["process"] == true){
                        console.log("save success")
                    }else{ 
                        console.log("error during saving")   
                    }
                } 
                 
            })
        }
}
    
   
                

