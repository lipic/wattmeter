class powerChart{ 
    constructor(refreshFunction) {
        this.refresher = refreshFunction
    }
    
    getConfig(){
        var color = Chart.helpers.color;
        var chartColors = { 
            red: 'rgb(255, 0, 0)',
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
                label: 'Power [W]',
                color: '#FFFFFF',
                backgroundColor: color(chartColors.red).alpha(0.6).rgbString(),
                borderColor: chartColors.red,
                fill: true,
                lineTension: 0,
                borderDash: [8, 4],
                data: []
            }]
        },
        options: {
            legend: {
                labels: {
                    fontColor: "white",
                    fontSize: 14
                }
            },
            title: {
                display: true
            }, 
            scales: {
                xAxes: [{ 
                    type: 'realtime',
                    fontColor: '#FFFFFF',
                    realtime: {
                        duration: 180000,
                        refresh: 2500,
                        delay: 2000,
                        onRefresh: this.refresher
                    },
                    ticks: {
                            fontColor: '#FFFFFF',
                            fontSize: 14
                    }
                }],
                yAxes: [{

                    scaleLabel: {
                        display: true,
                        labelString: 'W',
                        fontColor: '#FFFFFF'
                    },
                  gridLines: {
                      color: "#FFFFFF"
                     },
                        ticks: {
                                  fontColor: '#FFFFFF',
                                  fontSize: 14
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