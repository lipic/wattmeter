class energyChart{ 
    constructor() {
        this.refresher = 0

    }
 getConfig(){
        var color = Chart.helpers.color;
        var chartColors = { 
            red: 'rgb(255, 0, 0)',
            orange: 'rgb(255, 159, 64)',
            yellow: 'rgb(255, 205, 86)',
            green: 'rgb(75, 192, 192)',
            blue: 'rgb(0, 255, 235)',
            purple: 'rgb(153, 102, 255)',
            grey: 'rgb(201, 203, 207)'
        }; 
        var config = {
        type: 'bar', 
        data: {
            labels: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            datasets: [{
                label: 'Energy [kWh]',
                backgroundColor: color(chartColors.blue).alpha(0.9).rgbString(),
                borderColor: chartColors.red,
                borderWidth: 1,
                hoverBackgroundColor:chartColors.yellow,
                hoverBorderColor:chartColors.blue,
                hoverborderWidth: 2,
                fill: true,
                lineTension: 0,
                data: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            }]
        },
        options: {
            legend: {
                labels: {
                    fontColor: "white",
                    fontSize: 14
                }
            },
            scales: {
                xAxes:[{
                    ticks: {
                        fontColor: '#FFFFFF',
                        fontSize: 14
                        }
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'kWh',
                        fontColor: '#FFFFFF'
                    },
                    ticks: {
                        fontColor: '#FFFFFF',
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