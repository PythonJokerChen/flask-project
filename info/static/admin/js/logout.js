function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout1() {
    $.ajax({
        url: "/admin/logout",
        type: "post",
        contentType: "application/json",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        success: function (resp) {
            // 刷新当前界面
            alert(resp.errmsg);
            location.reload()
        }
    })
}
