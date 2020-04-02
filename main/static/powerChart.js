class powerChart{ 
    constructor(refreshFunction) {
        this.refresher = refreshFunction
    }
    
    getConfig(){
        var color = Chart.helpers.color;
        var chartColors = { 
            red: 'rgb(255, 99, 132)',
            orange: 'rgb(255, 159, 64)',
            yellow: 'rgb(255, 205, 86)',
            green: 'rgb(75, 192, 192)',
            blue: 'rgb(54, 162, 235)',
            purple: 'rgb(153, 102, 255)',
            grey: 'rgb(201, 203, 207)'
        }; 
        var config = {
        type: 'line',
        data: {
            datasets: [{
                label: 'Power [kw]',
                backgroundColor: color(chartColors.red).alpha(0.5).rgbString(),
                borderColor: chartColors.red,
                fill: true,
                lineTension: 0,
                borderDash: [8, 4],
                data: []
            }]
        },
        options: {
            title: {
                display: true
            }, 
            scales: {
                xAxes: [{ 
                    type: 'realtime',
                    realtime: {
                        duration: 180000,
                        refresh: 2500,
                        delay: 2000,
                        onRefresh: this.refresher
                    } 
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'kW'
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