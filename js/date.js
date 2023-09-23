function getTrainDate(dateStr) {
    var date = new Date(dateStr)
    return new Date(date.getFullYear(), date.getMonth(), date.getDate()).toString().replace('China Standard Time', '中国标准时间');
}

function getDatetime() {
    return new Date().getTime()
}