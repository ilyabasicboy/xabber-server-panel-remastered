$(function () {

    let url, page;
    function ajax_send(url, page='') {
        let ajax_url = url + page;

        //Create the data objec`t with `the host value and query parameters
        let data = {
            'host': $('#host').val(),
        };

        $.get(ajax_url, data, function(data){
            $('.list-js').html(data['html']);
            $('.items-count-js span').html(data['items_count']);
            setCurrentUrl();
        });
    };

    $('#host').on('change', function(e){
        ajax_send($(this).data('url'));
    });

    $('.list-js').on('click', '.pagination a', function(e) {
        e.preventDefault();

        let url = $(this).parents('.list-js').data('url');
        ajax_send(url, $(this).attr('href'));
    });

    //Separate logic for search
    let target, object;
    function search_ajax(url, $target=$('.search-list-js'), object='', page='') {
        let ajax_url = url + page;
        let query = $('#search-host').data('querystring');

        //Parse the query string into an object
        let queryParams = {};
        query.split('&').forEach(function (param) {
            var keyValue = param.split('=');
            if (keyValue[0] != 'page'){
                queryParams[keyValue[0]] = keyValue[1];
            }
        });

        //Create the data objec`t with `the host value and query parameters
        let data = {
            'host': $('#search-host').val(),
            'object': object,
            ...queryParams
        };

        $.get(ajax_url, data, function(data){
            $target.html(data['html']);
            setCurrentUrl();
            searchPagination();
        });
    };

    $('#search-host').on('change', function(e) {
        search_ajax($(this).data('url'));
    });

    function searchPagination() {
        $('.search-pagination-js').on('click', '.pagination a', function(e){
            e.preventDefault();
            search_ajax(
                $('#search-host').data('url'),
                target=$(this).parents('.search-pagination-js'),
                object=$(this).parents('.search-pagination-js').data('object'),
                $(this).attr('href')
            );
        });
    }
    searchPagination()

    function setCurrentUrl() {
        //Get the current URL
        let currentUrl = window.location.href;

        //Create a URL object
        let urlObject = new URL(currentUrl);

        //Construct the URL with only the scheme and host
        let schemeAndHost = urlObject.origin;

        //Check if the content of the span tag is empty
        if ($('.current-url-js').length != 0) {
            if ($('.current-url-js').text().trim() === ''){
                //If it's empty, insert the current URL
                $('.current-url-js').text(schemeAndHost);
            }
        }

        //Check if the content of the span tag is empty
        if ($('.show-url-js').length != 0 ) {
            if ($('.show-url-js').data('link').trim() === ''){
                //If it's empty, insert the current URL
                $('.show-url-js').data('link', schemeAndHost);
            }
        }
    };
    setCurrentUrl();

    //Add url to title
    $(document).on('click', '.show-url-js', function() {
        let url = $(this).data('link');
        let key = $(this).data('key');
        let fullLink = url + '/?rkey=' + key;

        $('.title-url-js').attr('href', fullLink).text(fullLink);
    });

    //Copy url
    $(document).on('click', '.copy-url-js', function() {
        let $temp = $("<div>");
        $("body").append($temp);
        $temp.attr("contenteditable", true)
            .html($('.title-url-js').html()).select()
            .on("focus", function() { document.execCommand('selectAll', false, null); })
            .focus();
        document.execCommand("copy");
        $temp.remove();
    });

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
    $(document).on('click', '.generate-password-js', function() {
        $(this).prev().val(generatePassword());
        return false;
    });

    //Init tooltips
    const tooltipTriggerItem = document.querySelector('[data-bs-toggle="tooltip"]');
    if ($(tooltipTriggerItem).length > 0) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    //Show/hide reason with change user status
    $('#user_status').on('change', function() {
        let optionVal = $(this).val();
        if (optionVal == "BLOCKED") {
            $(this).parent().next().addClass('show');
        } else {
            $(this).parent().next().removeClass('show');
        }
    });

    //Change radio input with admin checkbox
    $('#is_admin').on('change', function() {
        if ($(this).prop('checked')) {
            $(this).parents('form').find('.list-group-item').each(function(index, item) {
                $(item).find('input[type="radio"]').first().prop('checked', true);
                $(item).find('input[type="radio"]').attr('disabled', true);
            });
        } else {
            $(this).parents('form').find('input[type="radio"]').attr('disabled', false);
        }
    });

    //Show/hide modal messages
    const messagesItem = document.querySelector('#messages');
    if ($(messagesItem).length > 0) {
        let messages = new bootstrap.Modal(document.getElementById('messages'), {})
        messages.show();
        setTimeout(function() {
             messages.hide();
        }, 4000);
    }

    //Set Cookie
    function setCookie(name, value, options = {}) {
        options = {
            path: '/',
        };

        if (options.expires instanceof Date) {
            options.expires = options.expires.toUTCString();
        }

        let updatedCookie = encodeURIComponent(name) + "=" + encodeURIComponent(value);

        for (let optionKey in options) {
            updatedCookie += "; " + optionKey;
            let optionValue = options[optionKey];
            if (optionValue !== true) {
                updatedCookie += "=" + optionValue;
            }
        }

        document.cookie = updatedCookie;
    };

    //Switch theme
    const themeSwitch = document.getElementById('theme_switch');
    if ($(themeSwitch).length > 0) {
        themeSwitch.addEventListener('change', function () {
            if (themeSwitch.checked) {
                document.documentElement.setAttribute('data-bs-theme', 'dark');
                setCookie('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-bs-theme', 'light');
                setCookie('theme', 'light');
            }
        });
    };

});