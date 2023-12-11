$(document).ready(function(){

    function ajax_send(url, page='') {
        let ajax_url = url + page;
        let data = {
            'host': $('#host').val(),
        };

        $.get(ajax_url, data, function(data){
            $('.list-js').html(data);
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

    function setCurrentUrl(){
        // Get the current URL
        var currentUrl = window.location.href;

        // Create a URL object
        var urlObject = new URL(currentUrl);

        // Construct the URL with only the scheme and host
        var schemeAndHost = urlObject.origin;

        // Check if the content of the span tag is empty
        if ($('.current-url-js').text().trim() === '') {
            // If it's empty, insert the current URL
            $('.current-url-js').text(schemeAndHost);
        }
    }
    setCurrentUrl()
});