
function init_modal_alert() {
    var ss = "<div class='modal' id='modal_alert' style='margin-top:100px!important ;' >\
                <div class='modal-dialog'>\
                    <div class='modal-content'>\
                        <div class='modal-body'>\
                            <p id='modal_alert_text'></p>\
                        </div>\
                    </div>\
                </div>\
            </div>";
    document.body.insertAdjacentHTML( 'beforeend', ss );
}

function modal_alert() {
    var s = "";
    for (i=0; i < arguments.length; ++i) {
        s += arguments[i];
    }
    $("#modal_alert_text").text(s);
    $("#modal_alert").modal("toggle");
}

function modal_alert_json() {
    var s = "";
    for (i=1; i < arguments.length; ++i) {
        s += arguments[i];
    }
    $("#modal_alert_text").JSONView(arguments[0], { collapsed: true });
    $("#modal_alert").modal("toggle");
}

function modal_alert_and_reload() {
    $("#modal_alert").on('hidden.bs.modal', function () {
        location.reload();
    })
    modal_alert.apply(this, arguments);
}

function modal_alert_json_and_reload() {
    $("#modal_alert").on('hidden.bs.modal', function () {
        location.reload();
    })
    modal_alert_json.apply(this, arguments);
}

// post 方法请求一个 ajax 数据
function server_post(url, data, call) {
    var req = $.post(url, data,
        function(ret) {
            if (ret['rst'] == 'ok') {
                if (call != undefined) {
                    call(ret['data']);
                }
            } else {
                alert('操作不成功, ' + ret['rst']);
            }
        });
    req.error(function(err) {
        alert('有错误发生[' + err['rst'] + ']');
    });
}

// get 方法请求一个 ajax 数据
function server_get(url, data, call) {
    var req = $.post(url, data,
        function(ret) {
            if (ret['rst'] == 'ok') {
                if (call != undefined) {
                    call(ret['data']);
                }
            } else {
                alert('操作不成功, ' + ret['rst']);
            }
        });
    req.error(function(err) {
        alert('有错误发生[' + err['rst'] + ']');
    });
}

function syntaxHighlight(json) {
    if (typeof json != 'string') {
         json = JSON.stringify(json, undefined, 2);
    }
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'key';
            } else {
                cls = 'string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'boolean';
        } else if (/null/.test(match)) {
            cls = 'null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}
