class CreateOverView{constructor(){this.createOverView()}createOverView(){$('<div class="text-center" ><div class="gaugeContainer"><canvas id="power" class="gaugeElem" width="250" height="250"></canvas><span class="value gaugeElem" id="powerTxt" style="top: 20%; font-size: 65px;">-,-</span><span class="unit gaugeElem" style="top: 50%;">kW</span><span class="dim gaugeElem" style="top: 65%;" data-i18n-key="power">POWER [kWh]</span></div></div><div class="container" style="width:90%;"><div class="row justify-content-center"><div class="col-" style="width:49%;"><div class="card" id="tCard"><div class="card-body"><div class="card-title  text-center" style="color:#828389; font-weight: bold;" data-i18n-key="today">TODAY [kWh]</div><h3 class="card-text text-white text-center" style="font-weight: bold;" id="todayEnergy">-,-</h3></div></div></div><div class="col-" style="width:2%;"></div><div class="col-" style="width:49%;"><div class="card" id="tCard"><div class="card-body"><div class="card-title text-center" style="color:#828389; font-weight: bold;" data-i18n-key="yesterday">YESTERDAY [kWh]</div><h3 class="card-text text-white text-center" style="font-weight: bold;" id="yesterdayEnergy">-,- kWh</h3></div></div></div></div></div><div class="mt-2 md-2"></div><div class="container" style="width:90%;"><div class="row justify-content-center"><div class="col-" style="width:100%;"><div class="card" id="tCard"><div class="card-body"><div class="card-title  text-center" style="color:#828389; font-weight: bold;" data-i18n-key="total">TOTAL</div><h3 class="card-text text-white text-center" style="font-weight: bold;" id="totalEnergy">-,- kWh</h3></div></div></div></div></div><div id="evseGauge"></div><div class="md-4"></div>').appendTo("#overviewContainer")}}