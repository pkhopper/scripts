
function update_tabledata(url, tb, tp, callback){
    tb = '#'+tb;
    $.getJSON(url,function(result){
        if (tp == null){
            for (i in result["data"]) {
                x = result["data"][i];
                x[0] = '<a href="/www/ip_info.html?'+x[1]+'">'+x[0]+'</a>';
                x[1] = '<a href="http://'+x[1]+'">'+x[1]+'</a>';
            }
        }
        col = [];
        for (i in result["columns"]){
            col.push({"sTitle": result["columns"][i]});
        }
        data = {
                retrieve: true,
                "data": result["data"],
                "aoColumns": col
            };
        if (tp == 0) {
            data['ordering'] = false;
        }
        $(tb).DataTable(data);
        if (callback) {
            callback();
        }
    });
}
