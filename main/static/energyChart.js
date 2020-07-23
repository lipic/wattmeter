class energyChart{ 
    constructor(label, dim) {
        this.label = label
        this.dim = dim

    }
 getConfig(num){
        var color = Chart.helpers.color;
        var arrLabel = [];
        var arrData = [];
        var arrDataN = [];
        var arrDataH = [];
        var startNum = 0
        while(startNum < num){
          arrLabel.push(startNum++);
          arrData.push(0)
          arrDataH.push(0)
          arrDataN.push(0)
        }
        var chartColors = { 
            red: 'rgb(255, 0, 0)',
            orange: 'rgb(255, 128, 0 )',
            yellow: 'rgb(255, 255, 0)',
            green: 'rgb(75, 192, 192)',
            blue: 'rgb(0, 191, 235)',
            purple: 'rgb(153, 102, 255)',
            grey: 'rgb(201, 203, 207)'
        }; 
        var config = { 
        type: 'bar', 
        data: {
            datasets: [
            {
                label: "+"+this.label, 
                color: '#DCDCDC',
                backgroundColor: color(chartColors.blue).alpha(0.6).rgbString(),
                borderColor: chartColors.blue,
                borderWidth: 1,
                hoverBackgroundColor:color(chartColors.red).alpha(0.5).rgbString(),
                hoverBorderColor:chartColors.red,
                hoverborderWidth: 2,
                fill: true,
                lineTension: 0,
                data: arrDataH
                
            },
            {label: "-"+this.label, 
                color: '#DCDCDC',
                backgroundColor: color(chartColors.purple).alpha(0.6).rgbString(),
                borderColor: chartColors.purple,
                borderWidth: 1,
                hoverBackgroundColor:color(chartColors.red).alpha(0.5).rgbString(),
                hoverBorderColor:chartColors.red,
                hoverborderWidth: 2,
                fill: true,
                lineTension: 0,
                data: arrDataN
                
            },{
                type: 'line',
                yAxesGroup: "2",
                label: 'Eavg ['+ this.dim+']',
                backgroundColor: color(chartColors.yellow).alpha(0.1).rgbString(),
                borderColor: chartColors.yellow,
                borderWidth: 1,
                fill: false,
                order: 1,
                data: arrData
            }],
            labels: arrLabel            
        },
        options: {
            elements: {
                point:{
                radius: 0
                }
            },
            legend: {
                labels: {
                    fontColor: "#DCDCDC",
                    fontSize: 14 //nadpis
                }
            },

            scales: {
                xAxes:[{
                    stacked: true,
                    ticks: {
                        fontColor: '#DCDCDC',
                        fontSize: 13
                        }
                }],
                yAxes: [{
                    stacked: true,
                    scaleLabel: {
                        display: true,
                        labelString: this.dim,
                        fontColor: '#DCDCDC'
                    },
                    gridLines: {
                      color: "#DCDCDC",
                      lineWidth: 0.2
                     },
                    ticks: {
                        fontColor: '#DCDCDC',
                        fontSize: 14,
                        beginAtZero: true
                    }
                }]
            },
            tooltips: {
                mode: 'nearest',
                intersect: false
            },
            hover: {
                mode: 'nearest',
                intersect: false
                }
            }
        };
        return config
    } 

} 