(function(){
var C={blue:'#0072B2',orange:'#E69F00',sky:'#56B4E9',purple:'#9467bd',verm:'#D55E00',teal:'#009E73',amber:'#b45309',ink:'#374151',sub:'#6b7280',grid:'#eef0f3'};
function ex(a,b){for(var k in b)a[k]=b[k];return a;}
var $={extend:ex};
function base(grid){
  return {animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    grid:grid||{left:52,right:18,top:30,bottom:28},
    legend:{top:2,textStyle:{fontSize:11,color:C.ink}},
    xAxis:{type:'category',axisLabel:{color:'#4b5563',fontSize:10.5},axisLine:{lineStyle:{color:'#d1d5db'}}},
    yAxis:{type:'value',axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}}};
}
// 近500日 价格+均线+RSI 双panel
(function(){
  var el=document.getElementById('ch_px'); if(!el)return;
  var ch=echarts.init(el); var d=CHART.px500;
  ch.setOption({animation:false,textStyle:{color:C.ink},
    tooltip:{trigger:'axis',backgroundColor:'#fff',borderColor:'#e5e7eb',textStyle:{color:'#1f2329',fontSize:12}},
    legend:{data:['收盘价','EMA20','EMA50','SMA200'],top:0,textStyle:{fontSize:11,color:C.ink}},
    axisPointer:{link:[{xAxisIndex:'all'}]},
    grid:[{left:52,right:18,top:28,height:'52%'},{left:52,right:18,top:'78%',height:'16%'}],
    xAxis:[{type:'category',data:d.d,axisLabel:{show:false},axisLine:{lineStyle:{color:'#d1d5db'}}},
           {type:'category',data:d.d,gridIndex:1,axisLabel:{color:'#4b5563',fontSize:9.5,interval:40}}],
    yAxis:[{type:'value',scale:true,axisLabel:{color:'#4b5563',fontSize:10.5},splitLine:{lineStyle:{color:C.grid}}},
           {type:'value',gridIndex:1,min:0,max:100,axisLabel:{color:'#4b5563',fontSize:10.5,formatter:'{value}'},splitLine:{show:false}}],
    series:[
      {name:'收盘价',type:'line',data:d.px,symbol:'none',lineStyle:{color:C.blue,width:1.8},itemStyle:{color:C.blue}},
      {name:'EMA20',type:'line',data:d.e20,symbol:'none',lineStyle:{color:C.orange,width:1.2}},
      {name:'EMA50',type:'line',data:d.e50,symbol:'none',lineStyle:{color:C.purple,width:1.2}},
      {name:'SMA200',type:'line',data:d.s200,symbol:'none',lineStyle:{color:C.teal,width:1.2}},
      {name:'RSI14',type:'line',xAxisIndex:1,yAxisIndex:1,data:d.rsi,symbol:'none',lineStyle:{color:C.sky,width:1.3},areaStyle:{color:'rgba(86,180,233,.12)'}}
    ]});
  window.addEventListener('resize',function(){ch.resize();});
})();