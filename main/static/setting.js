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
                   
                    var radioBtn = $('<input type="radio" style="text-align:left;" name="ssid" value='+key+'>'+key+": "+quality+"%"+"<br>");
                    radioBtn.appendTo('#ssid'); 
                }
            }
            $('#refreshSSID').find("span").remove();
        });
    }
    
    
    
    this.refreshSetting = function() {
        var intSeconds = 1;
        var refreshId;
        var slideId;

        $.ajax({
            
            url: '/updateSetting' 
        })
        .done(function(data) {
            $('#updateSetting').html(data.datalayer);
            for(var key in data) {
               if (data.hasOwnProperty(key)) {
                    key = key.split(",")
                    if(key[0] == "sw"){
                        var settingArray = $('<div class="row  mt-3">  <div class="col" >  <p>'+key[1]+'</p> </div>  <div class="col">  <input id="'+key[1]+'"  type="checkbox" name="btn-checkbox" data-toggle="witchbutton"> </div> </div>');
                        settingArray.appendTo('#settingTable');
                    
                        if((data[key[0]+","+ key[1]])=="True"){        
                            document.getElementById(key[1]).switchButton('on', true);
                        }else{
                            document.getElementById(key[1]).switchButton('off', false);           
                        }
                    }
                }
            }
            for(var key in data) {
               if (data.hasOwnProperty(key)) {
                    key = key.split(",")
                    if(key[0] == "sl"){
                        var settingArray = $('<div class="row  mt-3" >  <div class="col" >  <p id="'+key[0]+key[1]+'">'+key[1]+":"+(data[key[0]+","+ key[1]])+' A</p> </div>  <div class="col">  <input id="'+key[1]+'" data-slider-id="'+key[1]+'" type="text" data-slider-min="6" data-slider-max="80" data-slider-step="1" style="display: none;" data-slider-value="'+(data[key[0]+","+ key[1]])+'"/> </div> </div>');
                        settingArray.appendTo('#settingTable');
                        $('#'+key[1]).slider(
                        {
                            formatter: function(value) {
                                slideStart = false;
                                slideId = $(this).attr("id")
                                document.getElementById("sl"+$(this).attr("id")).innerHTML = $(this).attr("id")+":"+value+" A"
                                if(refreshId != undefined){
                                    clearTimeout(refreshId);
                                }
                                refreshId = setInterval(function () { // saving the timeout
                                    sTimeout("sl,"+slideId,value);
                                 }, intSeconds * 3000);    
                            }
                        });
                    }
                }
            }
           
                            
            //Change the sTimeout function to allow interception of div content replacement
            function sTimeout(id,value) {
                console.log(id,value)
                self.saveSetting(id,value ); 
                clearTimeout(refreshId);  
            }
            
            $('.switch input[type="checkbox"]').on('change', function() {
                self.saveSetting("sw,"+$(this).attr("id"),$(this).prop('checked') );
            });
        });
    }
    
    

       this.saveSetting = function(id,value){
           console.log("variable",id, "value" , value )
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
    
    
   
   /*
   
                          //set a flag so we know if we're sliding 
                        slideStart = false;
                        $($(this).attr("id")).slider({
                            formatter: function(value) {
                            document.getElementById("slMain breaker").innerHTML = "Main breaker: "+value+" A"
                            self.saveSetting("sl,"+$(this).attr("id"),value );       
                            }
                        });
                            
                        $($(this).attr("id")).on('slideStart', function () {
                            // Set a flag to indicate slide in progress
                            slideStart = true;
                            // Clear the timeout
                            clearInterval(refreshId);
                        });

                            $($(this).attr("id")).on('slideStop', function () {
                                // Set a flag to indicate slide not in progress
                                slideStart = false;
                                // start the timeout
                                refreshId = setInterval(function () { // saving the timeout
                                sTimeout();
                            }, intSeconds * 3000);
                });
                            
                                        //Change the sTimeout function to allow interception of div content replacement
            function sTimeout() {
   
                    if (slideStart) {
                        console.log("Not Ready")
                        return;
                    } else {
                        console.log("Ready")
                    }
            }


        refreshId = setInterval(function () { // saving the timeout
            sTimeout();
        }, intSeconds * 3000);
                

*/