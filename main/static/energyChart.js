class energyChart{ 
    constructor() {
        this.refresher = 0

    }
 getConfig(){
        var color = Chart.helpers.color;
        var chartColors = { 
            red: 'rgb(255, 0, 0)',
            orange: 'rgb(255, 159, 64)',
            yellow: 'rgb(255, 255, 86)',
            green: 'rgb(75, 192, 192)',
            blue: 'rgb(0, 191, 235)',
            purple: 'rgb(153, 102, 255)',
            grey: 'rgb(201, 203, 207)'
        }; 
        var config = {
        type: 'bar', 
        data: {
            labels: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            datasets: [{
                label: 'Energy [kWh]',
                color: '#DCDCDC',
                backgroundColor: color(chartColors.blue).alpha(0.5).rgbString(),
                borderColor: chartColors.blue,
                borderWidth: 1,
                hoverBackgroundColor:color(chartColors.red).alpha(0.5).rgbString(),
                hoverBorderColor:chartColors.red,
                hoverborderWidth: 2,
                fill: true,
                lineTension: 0,
                data: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            }]
        },
        options: {
            legend: {
                labels: {
                    fontColor: "#DCDCDC",
                    fontSize: 14
                }
            },
            scales: {
                xAxes:[{
                    ticks: {
                        fontColor: '#DCDCDC',
                        fontSize: 14
                        }
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'kWh',
                        fontColor: '#DCDCDC'
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