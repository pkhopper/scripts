

function update_tabledata(url, tb, tp, callback){
    if (tb[0] != '#'){
        tb = '#' + tb;
    }
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
                // retrieve: true,
                "aaData": result["data"],
                "aoColumns": col
        };
        if (tp == 0) {
            data['ordering'] = false;
        }
        if (callback) {
            callback(tb, data);
        } else {
            $(tb).DataTable(data);
        }
        console.log(data);
    });
}


/**
 * Function : dump()
 * Arguments: The data - array,hash(associative array),object
 *    The level - OPTIONAL
 * Returns  : The textual representation of the array.
 * This function was inspired by the print_r function of PHP.
 * This will accept some data as the argument and return a
 * text that will be a more readable version of the
 * array/hash/object that is given.
 * Docs: http://www.openjs.com/scripts/others/dump_function_php_print_r.php
 */
function dump(arr,level) {
	var dumped_text = "";
	if(!level) level = 0;

	//The padding given at the beginning of the line.
	var level_padding = "";
	for(var j=0;j<level+1;j++) level_padding += "    ";

	if(typeof(arr) == 'object') { //Array/Hashes/Objects
		for(var item in arr) {
			var value = arr[item];

			if(typeof(value) == 'object') { //If it is an array,
				dumped_text += level_padding + "'" + item + "' ...\n";
				dumped_text += dump(value,level+1);
			} else {
				dumped_text += level_padding + "'" + item + "' => \"" + value + "\"\n";
			}
		}
	} else { //Stings/Chars/Numbers etc.
		dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
	}
	return dumped_text;
}