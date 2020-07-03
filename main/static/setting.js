function Setting() {
    ((self = this).refreshSetting = function () {
        var a, s;
        $.ajax({ url: "/updateSetting" }).done(function (t) {
            for (var e in t) {
                t.hasOwnProperty(e) &&
                    "txt" == (e = e.split(","))[0] &&
                    $('<div class="row  mt-3" >  <div class="col" >  <p id="' + e[1] + '">' + e[1] + '</p> </div>  <div class="col">  <p> ' + t[e[0] + "," + e[1]] + "</p> </div> </div>").appendTo("#settingTable");
            }
            for (var e in ($("#updateSetting").html(t.datalayer), t)) {
                t.hasOwnProperty(e) &&
                    "sw" == (e = e.split(","))[0] &&
                    ($('<div class="row  mt-3">  <div class="col" >  <p>' + e[1] + '</p> </div>  <div class="col">  <input id="' + e[1] + '"  type="checkbox" name="btn-checkbox" data-toggle="witchbutton"> </div> </div>').appendTo(
                        "#settingTable"
                    ),
                    "1" == t[e[0] + "," + e[1]] ? document.getElementById(e[1]).switchButton("on", !0) : document.getElementById(e[1]).switchButton("off", !1));
            }
            for (var e in t) {
                t.hasOwnProperty(e) &&
                    "sl" == (e = e.split(","))[0] &&
                    (console.log(t[e[0] + "," + e[1]]),
                    $(
                        '<div class="row  mt-3" >  <div class="col" >  <p id="' +
                            e[0] +
                            e[1] +
                            '">' +
                            e[1] +
                            ":" +
                            t[e[0] + "," + e[1]] +
                            ' A</p> </div>  <div class="col">  <input id="' +
                            e[1] +
                            '" data-slider-id="' +
                            e[1] +
                            '" type="text" data-slider-min="6" data-slider-max="80" data-slider-step="1" style="display: none;" data-slider-value="' +
                            t[e[0] + "," + e[1]] +
                            '"/> </div> </div>'
                    ).appendTo("#settingTable"),
                    $("#" + e[1]).slider({
                        formatter: function (i) {
                            (slideStart = !1),
                                (s = $(this).attr("id")),
                                (document.getElementById("sl" + $(this).attr("id")).innerHTML = $(this).attr("id") + ":" + i + " A"),
                                null != a && clearTimeout(a),
                                (a = setInterval(function () {
                                    var t, e;
                                    (t = "sl," + s), (e = i), console.log(t, e), self.saveSetting(t, e), clearTimeout(a);
                                }, 3e3));
                        },
                    }));
            }

            for (var e in t) {
                t.hasOwnProperty(e) &&
                    "bt" == (e = e.split(","))[0] &&
                    $(
                        '<div class="row  mt-3 mb-3 " >  <div class="col" >  <p id="' + e[1] + '">' + e[1] + '</p> </div>  <div class="col"> <button  id="resetEsp" type="button" class="btn btn-primary ">RESET</button>  </div> </div>'
                    ).appendTo("#settingTable");
            }
            $('.switch input[type="checkbox"]').on("change", function () {
                self.saveSetting("sw," + $(this).attr("id"), ($(this).prop("checked")==true)? 1: 0);
            });
            
           $(document).on("click", "#resetEsp", function(event) {
                console.log("Resetujuu")
                //setTimeout(resetCounter, 1000); 
                document.getElementById('resetEsp').innerText = 'WAITING ..'
                $('#resetEsp').append('<span class="spinner-border spinner-border-sm"></span>');
                setTimeout(function(){
                location.reload(true)} ,25000)
                self.saveSetting("bt,RESET WATTMETER", 1);
            });
            resetCounter = function(){
                console.log("Vuii")
            }
        });
    }),
        (this.refreshWifiClient = function () {
            $.ajax({ url: "/updateWificlient" }).done(function (t) {
                for (var e in ($("#updateWificlient").html(t.datalayer), t)) {
                    var i;
                    t.hasOwnProperty(e) && ((i = 0), (i = t[e] <= -100 ? 0 : -50 <= t[e] ? 100 : 2 * (t[e] + 100)), $('<input type="radio" style="text-align:left;" name="ssid" value=' + e + ">" + e + ": " + i + "%<br>").appendTo("#ssid"));
                }
                $("#refreshSSID").find("span").remove();
            });
        }),
        (this.saveSetting = function (t, e) {
            console.log("variable", t, "value", e),
                $.ajax({
                    type: "POST",
                    url: "/updateSetting",
                    async: !0,
                    data: JSON.stringify({ variable: t, value: e }),
                    success: function (t) {
                        $("#updateSetting").html(t.datalayer), 1 == t.process ? console.log("save success") : console.log("error during saving");
                    },
                });
        });
}
