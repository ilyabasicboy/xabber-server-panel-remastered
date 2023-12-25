$(function () {

    let url, page;
    function ajax_send(url, page='') {
        let ajax_url = url + page;
        let data = {
            'host': $('#host').val(),
        };

        $.get(ajax_url, data, function(data){
            $('.list-js').html(data['html']);
            $('.items-count-js span').html(data['items_count'])
            setCurrentUrl();
        });
    };

    $('#host').on('change', function(e){
        ajax_send($(this).data('url'));
    });

    $('.list-js').on('click', '.pagination a', function(e){
        e.preventDefault();
        let url = $(this).parents('.list-js').data('url');
        ajax_send(url, $(this).attr('href'));
    });

    function setCurrentUrl() {
        //Get the current URL
        let currentUrl = window.location.href;

        //Create a URL object
        let urlObject = new URL(currentUrl);

        //Construct the URL with only the scheme and host
        let schemeAndHost = urlObject.origin;

        //Check if the content of the span tag is empty
        if ($('.current-url-js').text().trim() === '') {
            //If it's empty, insert the current URL
            $('.current-url-js').text(schemeAndHost);
        }
    };
    setCurrentUrl();

    //Generate password on click
    function generatePassword() {
        let length = 10,
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        res = '';
        for (let i = 0, n = charset.length; i < length; ++i) {
            res += charset.charAt(Math.floor(Math.random() * n));
        }
        return res;
    };
    $('.generate-password-js').on('click', function() {
        $(this).prev().val(generatePassword());
        return false;
    });

});