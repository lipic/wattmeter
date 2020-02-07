var timer;
var chart;
var canvas;
var ctx;
var counter = 0;

const wifiManager = new WifiManager()

function update_ints_count() {
    
    $.ajax({
            url: '/updateData' 
        })
        .done(function(data) {
            var ms = 1000
            $('#updateData').html(data.datalayer);
            document.getElementById("U1").textContent = data['U1']
            document.getElementById("U2").textContent = data['U2']
            document.getElementById("U3").textContent = data['U3']
            document.getElementById("I1").textContent = data['I1']
            document.getElementById("I2").textContent = data['I2']
            document.getElementById("I3").textContent = data['I3']
            document.getElementById("P1").textContent = data['P1']
            document.getElementById("P2").textContent = data['P2'] 
            document.getElementById("P3").textContent = data['P3']
            document.getElementById("E1").textContent = Math.round(data['E1']/10000)/100
            document.getElementById("E2").textContent = Math.round(data['E2']/10000)/100
            document.getElementById("E3").textContent = Math.round(data['E3']/10000)/100
            
            document.getElementById("time").textContent = getTime();

            if(counter>59){
                for(var i=0; i<60;i++){ 
                    chart.data.datasets[0].data[i]=undefined;
                    chart.data.datasets[1].data[i]=undefined;
                }
                counter = 0;
            }
            chart.data.datasets[0].data[counter] = (data['P1']+data['P2']+data['P3']);
            chart.data.datasets[1].data[counter] = Math.round((data['I1']+data['I2']+data['I3'])/10)/100;
            chart.update();
            counter = counter +1;
            
            timer = setTimeout(update_ints_count, ms);
        });
}

$(document).ready(function() 
 {
    $('div.mainContainer').load('datatable');
    window.addEventListener('load', function () {
        window.setTimeout(function(){
        setChart(); 
        update_ints_count();
        },1000); 
    })
    
    $('.menu a').click(function(e)
    {
        if($(this).attr('id') == 'main'){
            stop(timer);
            $('div.mainContainer').load('datatable');
             window.setTimeout(function(){
                 counter = 0;
                 setChart(); 
                 update_ints_count();
              },1000)
            
         }else if($(this).attr('id') == 'settings'){
             stop(timer);
             $('div.mainContainer').load('settings');
             $(canvas).remove();
             wifiManager.refreshWifiClient();
            } 
        $('.menu a').removeClass('active');
        $(this).addClass('active');
            
    }); 
     
    $(document).on('click','#setSSID',function(){
        $('.loader').show();
        $.when(showSomeProcess()).then(function(){
            //$('.loader').hide();
        })
    }); 
            
   var showSomeProcess = function(){
       var password = document.getElementById("passwordField").value;
        var ssid = $("input[name='ssid']:checked").val();
        if(ssid){
            alert("I will try to connect wifi with ssid: " + ssid);
            $.ajax({
                type: "POST", 
                //the url where you want to sent the userName and password to
                url: '/updateWificlient',
                async: true,
                data: JSON.stringify({"ssid": ssid, "password" :  password }),
                success: function (data) {
                    $('#updateWificlient').html(data.datalayer);
                    if(data["process"] == true){
                        alert("Process was success, Your new IP address is: "+data["ip"])
                    }else{ 
                        alert("Process was unsuccess")   
                    }
                } 
                 
            }).success(function() {
                $('.loader').hide();
            }); 
        }else{ 
            alert("Please choose ssid client first!");
        }
       return 0
    }
 
    $(document).on('click','#refreshSSID',function(){
        $('div.mainContainer').load('settings');
        wifiManager.refreshWifiClient();    
    });
 });
 


 function stop() {
        if (timer) {
            console.log("stopTimer")
            clearTimeout(timer);
            timer = 0;
        }
    }
 
function setChart(){
    canvas = document.getElementById('chart');
    ctx = canvas.getContext('2d');
    chart = new Chart(ctx, {
                type: 'line',
                 data: {
                    labels: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
                    datasets: [{
                        label: "Power [W]",
                        borderColor: 'rgb(255, 99, 132)',
                        data: [],
                    },{
                        label: "Current [A]",
                        borderColor: 'rgb(3, 57, 252)',
                        data: [],
                    },]
                },
 
                // Configuration options go here
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    }
                }
            });

}

function getTime(){
    var dt = new Date();
    var time = dt.getHours() + ":" + dt.getMinutes();
    return time;
    }