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
                color: '#DCDCDC',
                backgroundColor: color(chartColors.red).alpha(0.6).rgbString(),
                borderColor: chartColors.red,
                fill: true,
                lineTension: 0,
                borderDash: [4 ,2],
                data: []
            }]
        },
        options: {
            legend: {
                labels: {
                    fontColor: "#DCDCDC",
                    fontSize: 14
                }
            },
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
                    },
                    ticks: {
                            fontColor: '#DCDCDC',
                            fontSize: 14
                    }
                }],
                yAxes: [{

                    scaleLabel: {
                        display: true,
                        labelString: 'W',
                        fontColor: '#DCDCDC'
                    },
                  gridLines: {
                      color: "#DCDCDC"
                     },
                        ticks: {
                                  fontColor: '#DCDCDC',
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