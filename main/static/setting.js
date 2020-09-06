function Setting() {
    ((self = this).refreshSetting = function () {
        var t, e;
        $.ajax({ url: "/updateSetting" }).done(function (n) {
            for (var i in n)
                n.hasOwnProperty(i) &&
                    "txt" == (i = i.split(","))[0] &&
                    $('<div class="row  mt-3" >  <div class="col" >  <p id="' + i[1] + '">' + i[1] + '</p> </div>  <div class="col">  <p> ' + n[i[0] + "," + i[1]] + "</p> </div> </div>").appendTo("#settingTable");
            for (var i in ($("#updateSetting").html(n.datalayer), n))
                n.hasOwnProperty(i) &&
                    "sw" == (i = i.split(","))[0] &&
                    ($('<div class="row  mt-3">  <div class="col" >  <p>' + i[1] + '</p> </div>  <div class="col">  <input id="' + i[1] + '"  type="checkbox" name="btn-checkbox" data-toggle="witchbutton"> </div> </div>').appendTo(
                        "#settingTable"
                    ),
                    "1" == n[i[0] + "," + i[1]] ? document.getElementById(i[1]).switchButton("on", !0) : document.getElementById(i[1]).switchButton("off", !1));
            for (var i in ($("#updateSetting").html(n.datalayer), n))
                n.hasOwnProperty(i) &&
                    "in" == (i = i.split(","))[0] &&
                    $(
                        '<div class="row  mt-3">  <div class="col" >  <p>' +
                            i[1] +
                            '</p> </div>  <div class="col">  <div class="input-group"><span class="input-group-btn"><button class="btn btn-primary btn-minuse" type="button">-</button></span> <input type="text" class="form-control no-padding add-color text-center height-25" maxlength="2" value="' +
                            n[i[0] + "," + i[1]] +
                            '"><span class="input-group-btn"><button class="btn btn-primary btn-plus" type="button">+</button> </span></div></div> </div>'
                    ).appendTo("#settingTable");
            $input = $('input[type="text"]');
            $(".btn").on("click", function () {
                $val = $input.val();
                hodnota = 0;
                if ($(this).hasClass("btn-minuse")) {
                    if (parseInt($val) - 1 < 0) {
                        hodnota = 0;
                        $input.val(0);
                    } else {
                        hodnota = parseInt($val) - 1;
                        $input.val(hodnota);
                    }
                     self.saveSetting("in,EVSE-NUMBER", hodnota);
                } else if($(this).hasClass("btn-plus")) {
                    if (parseInt($val) + 1 > 99) {
                        hodnota = 99;
                        $input.val(99); 
                    } else {
                        hodnota = parseInt($val) + 1;
                        $input.val(hodnota);
                    }
                     self.saveSetting("in,EVSE-NUMBER", hodnota);
                }
            });
            for (var i in n)
                n.hasOwnProperty(i) &&
                    "sl" == (i = i.split(","))[0] &&
                    (console.log(n[i[0] + "," + i[1]]),
                    $(
                        ' <div class="container text-center mt-3"> <p id="' +
                            i[0] +
                            i[1] +
                            '">' +
                            i[1] +
                            ": " +
                            n[i[0] + "," + i[1]] +
                            ' A</p> </div>  <div class="container text-center">  <input id="' +
                            i[1] +
                            '" data-slider-id="' +
                            i[1] +
                            '" type="text" data-slider-min="' +
                            ("TIME-ZONE" == i[1] ? "-12" : "0") +
                            '" data-slider-max="' +
                            ("TIME-ZONE" == i[1] ? "12" : "80") +
                            '" data-slider-step="1" style="display: none;" data-slider-value="' +
                            n[i[0] + "," + i[1]] +
                            '"/> </div> '
                    ).appendTo("#settingTable"),
                    $("#" + i[1]).slider({
                        formatter: function (n) {
                            (slideStart = !1),
                                (e = $(this).attr("id")),
                                (value = "TIME-ZONE" == e ? "UTC" + (n >= 0 ? "+" + ("0" + n).slice(-2) : "-" + ("0" + n).slice(-2)) : n + " A"),
                                (document.getElementById("sl" + $(this).attr("id")).innerHTML = e + ": " + value),
                                null != t && clearTimeout(t),
                                (t = setInterval(function () {
                                    var i, s;
                                    (i = "sl," + e), (s = n), console.log(i, s), self.saveSetting(i, s), clearTimeout(t);
                                }, 3e3));
                        },
                    }));
            for (var i in n)
                n.hasOwnProperty(i) &&
                    "bt" == (i = i.split(","))[0] &&
                    $(
                        '<div class="row  mt-4 mb-3" >  <div class="col" >  <p id="' + i[1] + '">' + i[1] + '</p> </div>  <div class="col"> <button  id="resetEsp" type="button" class="btn btn-primary ">RESET</button>  </div> </div>'
                    ).appendTo("#settingTable");
            $('.switch input[type="checkbox"]').on("change", function () {
                self.saveSetting("sw," + $(this).attr("id"), 1 == $(this).prop("checked") ? 1 : 0);
            });
            var s = 25;
            $(document).on("click", "#resetEsp", function (t) {
                setInterval(resetCounter, 1e3),
                    setTimeout(function () {
                        location.reload(!0), (s = 0), (document.getElementById("resetEsp").innerText = "FINISHING");
                    }, 25e3),
                    self.saveSetting("bt,RESET WATTMETER", 1);
            }),
                (resetCounter = function () {
                    0 != s && ((document.getElementById("resetEsp").innerText = "WAITING " + s + "s"), (s -= 1));
                });
        });
    }),
        (this.refreshWifiClient = function () {
            $.ajax({ url: "/updateWificlient" }).done(function (t) {
                for (var e in ($("#updateWificlient").html(t.datalayer), t)) {
                    var n;
                    if ("connectSSID" == e)
                        "None" == t[e]
                            ? ((document.getElementById("wifiStatus").innerHTML = "Not connected to wifi"), (document.getElementById("wifiStatus").style.color = "#FF0000"))
                            : ((document.getElementById("wifiStatus").innerHTML = "Currently connected to: " + t[e]), (document.getElementById("wifiStatus").style.color = "#74DF00"));
                    else t.hasOwnProperty(e) && (0, (n = t[e] <= -100 ? 0 : -50 <= t[e] ? 100 : 2 * (t[e] + 100)), $('<input type="radio" style="text-align:left;" name="ssid" value=' + e + ">" + e + ": " + n + "%<br>").appendTo("#ssid"));
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
