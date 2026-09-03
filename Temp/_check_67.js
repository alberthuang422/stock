
(function(){
  var B='#0072B2',O='#E69F00',S='#56B4E9',V='#D55E00',P='#CC79A7',G='#009E73',K='#555555',Y='#F0E442';
  var FONT={fontFamily:'"Microsoft YaHei","PingFang SC",sans-serif'};

  var seg=echarts.init(document.getElementById('c_seg'));
  seg.setOption({
    tooltip:{trigger:'item',formatter:'{b}: {d}%'},
    legend:{bottom:0,textStyle:FONT,itemWidth:12,itemHeight:12},
    series:[{
      type:'pie',radius:['42%','68%'],center:['50%','44%'],
      label:{formatter:'{b}\n{d}%',fontSize:11},
      data:[
        {name:'织物与家居护理 35%',value:35,itemStyle:{color:B}},
        {name:'婴/女/家庭护理 24%',value:24,itemStyle:{color:O}},
        {name:'美容 19%',value:19,itemStyle:{color:S}},
        {name:'健康护理 14%',value:14,itemStyle:{color:V}},
        {name:'理容 8%',value:8,itemStyle:{color:P}}
      ]
    }]
  });

  var geo=echarts.init(document.getElementById('c_geo'));
  geo.setOption({
    tooltip:{trigger:'item',formatter:'{b}: {d}%'},
    legend:{bottom:0,textStyle:FONT,itemWidth:12,itemHeight:12},
    series:[{
      type:'pie',radius:['42%','68%'],center:['50%','44%'],
      label:{formatter:'{b}\n{d}%',fontSize:11},
      data:[
        {name:'北美 51%',value:51,itemStyle:{color:B}},
        {name:'欧洲 23%',value:23,itemStyle:{color:O}},
        {name:'拉美 7%',value:7,itemStyle:{color:S}},
        {name:'大中华区 7%',value:7,itemStyle:{color:V}},
        {name:'亚太 7%',value:7,itemStyle:{color:P}},
        {name:'印中东非 5%',value:5,itemStyle:{color:G}}
      ]
    }]
  });

  var gr=echarts.init(document.getElementById('c_growth'));
  gr.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:['净销售额($B)','Core EPS($)','摊薄 EPS($)'],textStyle:FONT},
    grid:{left:50,right:55,top:40,bottom:30},
    xAxis:{type:'category',data:['FY2022','FY2023','FY2024','FY2025','FY2026']},
    yAxis:[
      {type:'value',name:'净销售额($B)',min:70,max:92},
      {type:'value',name:'EPS($)',min:4,max:8}
    ],
    series:[
      {name:'净销售额($B)',type:'bar',data:[80.2,82.0,84.0,84.3,87.0],itemStyle:{color:B},barWidth:'38%'},
      {name:'Core EPS($)',type:'line',yAxisIndex:1,data:[5.81,5.90,6.59,6.83,6.89],itemStyle:{color:O},lineStyle:{width:3},symbolSize:8},
      {name:'摊薄 EPS($)',type:'line',yAxisIndex:1,data:[5.81,5.90,6.02,6.51,6.62],itemStyle:{color:P},lineStyle:{width:2,type:'dashed'},symbolSize:7}
    ]
  });

  var og=echarts.init(document.getElementById('c_organic'));
  og.setOption({
    tooltip:{trigger:'axis',formatter:'{b}: {c}%'},
    grid:{left:40,right:20,top:20,bottom:30},
    xAxis:{type:'category',data:['FY2022','FY2023','FY2024','FY2025','FY2026']},
    yAxis:{type:'value',name:'有机增速(%)',max:8},
    series:[{
      type:'bar',data:[7,7,4,2,1],barWidth:'45%',
      itemStyle:{color:function(p){return ['#0072B2','#56B4E9','#E69F00','#D55E00','#B2182B'][p.dataIndex];}},
      label:{show:true,position:'top',formatter:'{c}%'}
    }]
  });

  var tg=document.getElementById('tg1'),bc=document.getElementById('box_chart1'),bt=document.getElementById('box_table1');
  tg.addEventListener('click',function(){
    var tHidden=bt.className.indexOf('hidden')>=0;
    if(tHidden){bt.className='';bc.className='hidden';tg.innerHTML='［切换回图表］';}
    else{bt.className='hidden';bc.className='';tg.innerHTML='［切换查看数据表］';}
  });
})();
