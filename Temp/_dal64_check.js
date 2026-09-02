
var CHART = {"band": [{"bk": "35-40", "n": 151, "maxg": 7.05, "fwd": 1.7, "er": 0.22, "ex": -0.05, "win": 57.0}, {"bk": "30-35", "n": 112, "maxg": 6.26, "fwd": 0.89, "er": 0.18, "ex": -0.93, "win": 53.6}, {"bk": "<30", "n": 69, "maxg": 6.68, "fwd": 2.42, "er": 0.19, "ex": -0.82, "win": 59.4}], "cd10": [{"bk": "35-40", "all_fwd": 1.7, "cd10_fwd": 1.37, "all_win": 57.0, "cd10_win": 56.6, "all_ex": -0.05, "cd10_ex": -0.52}, {"bk": "30-35", "all_fwd": 0.89, "cd10_fwd": 0.72, "all_win": 53.6, "cd10_win": 55.2, "all_ex": -0.93, "cd10_ex": -1.04}, {"bk": "<30", "all_fwd": 2.42, "cd10_fwd": -5.34, "all_win": 59.4, "cd10_win": 40.0, "all_ex": -0.82, "cd10_ex": -4.47}], "year": [{"y": "2007", "n": 21}, {"y": "2008", "n": 24}, {"y": "2009", "n": 13}, {"y": "2010", "n": 20}, {"y": "2011", "n": 33}, {"y": "2012", "n": 12}, {"y": "2013", "n": 2}, {"y": "2014", "n": 10}, {"y": "2015", "n": 17}, {"y": "2016", "n": 19}, {"y": "2017", "n": 19}, {"y": "2018", "n": 15}, {"y": "2019", "n": 14}, {"y": "2020", "n": 17}, {"y": "2021", "n": 24}, {"y": "2022", "n": 19}, {"y": "2023", "n": 17}, {"y": "2024", "n": 17}, {"y": "2025", "n": 13}, {"y": "2026", "n": 6}], "deep": [{"label": "rsi<24", "n": 2, "fwd": 20.8, "ex": 12.87, "win": 100.0, "maxg": 23.95}, {"label": "rsi24-26", "n": 6, "fwd": 7.62, "ex": 2.23, "win": 66.7, "maxg": 11.21}, {"label": "rsi26-28", "n": 18, "fwd": 3.75, "ex": -2.12, "win": 61.1, "maxg": 6.31}, {"label": "rsi28-30", "n": 40, "fwd": 0.78, "ex": -0.52, "win": 52.5, "maxg": 6.34}], "deep2": [{"label": "dd60 -20~-10", "n": 24, "fwd": 3.04, "ex": -0.83, "win": 70.8, "maxg": 5.95}, {"label": "dd60 -30~-20", "n": 22, "fwd": 3.7, "ex": -1.5, "win": 54.5, "maxg": 7.94}, {"label": "dd60<=-30", "n": 23, "fwd": 1.47, "ex": 1.56, "win": 52.2, "maxg": 11.11}, {"label": "dd250>-20", "n": 16, "fwd": 2.35, "ex": -0.83, "win": 62.5, "maxg": 5.5}, {"label": "dd250 -35~-20", "n": 30, "fwd": 2.79, "ex": -1.23, "win": 60.0, "maxg": 7.29}, {"label": "dd250<=-35", "n": 23, "fwd": 2.42, "ex": 4.86, "win": 56.5, "maxg": 11.13}], "n_total": 332, "n_cd10": 138, "base_fwd": 1.29, "base_maxg": 6.5, "sub_base_fwd": 1.29, "sub_base_ex": -0.03};
var C = {blue:"#0072B2", orange:"#E69F00", sky:"#56B4E9", purple:"#9467bd", verm:"#D55E00", teal:"#009E73", sub:"#6b7280", ink:"#1f2329"};
function showTab(id, btn){
  document.querySelectorAll(".pane").forEach(function(p){p.classList.remove("on");});
  document.querySelectorAll(".tabbar button").forEach(function(b){b.classList.remove("on");});
  document.getElementById(id).classList.add("on");
  btn.classList.add("on");
  setTimeout(function(){window.dispatchEvent(new Event("resize"));},60);
}
function filterEvents(v){
  var rows = document.querySelectorAll("#eventBody tr");
  var show = 0;
  rows.forEach(function(r){
    var hit = (v === "all" || r.getAttribute("data-band") === v);
    r.style.display = hit ? "" : "none";
    if (hit) show++;
  });
  var note = document.getElementById("filterNote");
  if (note) note.textContent = "当前显示 " + show + " / " + rows.length + " 条";
}
function barChart(id, dd, labels){
  var ch = echarts.init(document.getElementById(id));
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:120,right:55,top:16,bottom:24},
    xAxis:{type:"value",name:"fwd20 中位 %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    yAxis:{type:"category",data:labels,axisLabel:{color:"#4b5563",fontSize:10.5}},
    series:[{type:"bar",barWidth:13,data:dd.map(function(x){
        return {value:x.fwd,itemStyle:{color:x.fwd>=0?C.verm:C.teal}};
      }),label:{show:true,position:"right",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
}
(function(){
  var ch = echarts.init(document.getElementById("ch_band"));
  var b = CHART.band;
  ch.setOption({
    animation:false,
    legend:{data:["maxG 中位","fwd20 中位","ER 中位"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:55,right:55,top:38,bottom:30},
    xAxis:{type:"category",data:b.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:[
      {type:"value",name:"%",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
      {type:"value",name:"ER",min:0,max:0.35,axisLabel:{formatter:function(v){return v.toFixed(2);},color:"#9aa1ab"},splitLine:{show:false}}
    ],
    series:[
      {name:"maxG 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.maxg;}),itemStyle:{color:C.verm},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"fwd20 中位",type:"bar",barWidth:16,data:b.map(function(x){return x.fwd;}),itemStyle:{color:C.teal},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"ER 中位",type:"line",yAxisIndex:1,data:b.map(function(x){return x.er;}),lineStyle:{color:C.blue,width:1.6},symbol:"circle",symbolSize:6,itemStyle:{color:C.blue}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_cd10"));
  var d = CHART.cd10;
  ch.setOption({
    animation:false,
    legend:{data:["全量 fwd20","cd10 fwd20"],top:2,textStyle:{fontSize:11,color:"#374151"}},
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:50,right:20,top:36,bottom:30},
    xAxis:{type:"category",data:d.map(function(x){return "RSI "+x.bk;}),axisLabel:{color:"#4b5563",fontSize:11}},
    yAxis:{type:"value",name:"fwd20 中位 %",axisLabel:{formatter:"{value}%",color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[
      {name:"全量 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.all_fwd;}),itemStyle:{color:C.sky},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}},
      {name:"cd10 fwd20",type:"bar",barWidth:14,data:d.map(function(x){return x.cd10_fwd;}),itemStyle:{color:C.blue},label:{show:true,position:"top",fontSize:9,formatter:function(p){return p.value.toFixed(2)+"%";}}}
    ]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
(function(){
  var ch = echarts.init(document.getElementById("ch_year"));
  var y = CHART.year;
  ch.setOption({
    animation:false,
    tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},
    grid:{left:40,right:15,top:20,bottom:24},
    xAxis:{type:"category",data:y.map(function(x){return x.y;}),axisLabel:{color:"#4b5563",fontSize:10,interval:2}},
    yAxis:{type:"value",name:"事件数",minInterval:1,axisLabel:{color:"#4b5563"},splitLine:{lineStyle:{color:"#eef0f3"}}},
    series:[{type:"bar",data:y.map(function(x){return x.n;}),itemStyle:{color:C.orange,opacity:0.9},barWidth:"55%",
      label:{show:true,position:"top",fontSize:8,formatter:function(p){return p.value>0?p.value:"";}}}]
  });
  window.addEventListener("resize",function(){ch.resize();});
})();
barChart("ch_deep", CHART.deep, CHART.deep.map(function(x){return x.label;}));
barChart("ch_deep2", CHART.deep2, CHART.deep2.map(function(x){return x.label;}));
