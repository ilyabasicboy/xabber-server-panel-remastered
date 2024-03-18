$(function () {

    let url, page, updateChange, updateTooltip;
    function ajax_send(url, page='', updateChange=false, updateTooltip=false) {
        let ajax_url = url + page;

        //Create the data objec`t with `the host value and query parameters
        let data = {
            'host': $('#host').val(),
        };

        $.get(ajax_url, data, function(data) {
            $('.list-js').html(data['html']);
            $('.items-count-js span').html(data['items_count']);
            setCurrentUrl();

            //Reinit functions
            if (updateChange) {
                checkChange();
            }
            if (updateTooltip) {
                initTooltip();
            }
        });
    };

    $('#host').on('change', function() {
        if ($(this).parents('.check-change-js').length > 0) {
            ajax_send($(this).data('url'), page='', updateChange=true, updateTooltip=true);
        } else {
            ajax_send($(this).data('url'), page='', updateChange=true);
        }
    });

    $('.list-js').on('click', '.pagination a', function(e) {
        e.preventDefault();

        let url = $(this).parents('.list-js').data('url');

        let loader = '<div class="d-flex align-items-center justify-content-center position-absolute top-0 start-0 w-100 h-100 bg-body bg-opacity-75 z-3"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        $(this).parents('.list-js').find('.table-adaptive').append(loader);

        ajax_send(url, $(this).attr('href'));
    });

    //Check dns records ajax
    $('.check-records-js').on('click', function(e) {
        e.preventDefault();
        let $this = $(this);
        let url = $this.data('url');
        $this.find('.spinner-border').removeClass('d-none');
        $this.attr('disabled', true);
        $.get(url, {}, function(data) {
            $this.find('.spinner-border').addClass('d-none');
            $this.attr('disabled', false);
            $('.host-list-js').html(data);
        });
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
        $(this).parent().find('input').val(generatePassword());
        $(this).parent().find('input').trigger('change');
        return false;
    });

    //Init tooltips
    function initTooltip() {
        const tooltipTriggerItem = document.querySelector('[data-bs-toggle="tooltip"]');
        if ($(tooltipTriggerItem).length > 0) {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    };
    initTooltip();

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

    //Check change in form
    function checkChange() {
        let form = $('.check-change-js');
        form.each(function(index, item) {
            let origFormTextInputs = $(item).find(':input:not(:file):not(.nocheck-change-js)').serialize();
            let origFormFileInputs = $(item).find(':file').map(function() {
                return this.value;
            }).get().join(',');

            // Check for change in text inputs
            $(item).find(':input:not(:file)').on('change input', function() {
                if ($(item).find(':input:not(:file):not(.nocheck-change-js)').serialize() !== origFormTextInputs || $(item).find(':file').map(function() {
                    return this.value;
                }).get().join(',') !== origFormFileInputs) {
                    $(item).find('button[name="save"]').prop('disabled', false).removeClass('btn-secondary');
                } else {
                    $(item).find('button[name="save"]').prop('disabled', true).addClass('btn-secondary');
                }
            });

            // Check for change in file inputs
            $(item).find(':file').on('change', function() {
                let currentFormFileInputs = $(item).find(':file').map(function() {
                    return this.value;
                }).get().join(',');

                if ($(item).find(':input:not(:file)').serialize() !== origFormTextInputs || currentFormFileInputs !== origFormFileInputs) {
                    $(item).find('button[name="save"]').prop('disabled', false).removeClass('btn-secondary');
                } else {
                    $(item).find('button[name="save"]').prop('disabled', true).addClass('btn-secondary');
                }
            });
        });
    };
    checkChange();

    //Check change date/time input
    let input = $('.check-date-js');
    input.each(function(index, item) {
        let inputDate = $(item).find('input[type="date"]');
        let inputTime = $(item).find('input[type="time"]');
        if (inputDate.val().length != 0) {
            inputTime.prop('disabled', false).removeClass('text-body-tertiary');
            inputDate.removeClass('text-body-tertiary');
        }
        inputDate.on('change input', function() {
            if ($(this).val().length != 0) {
                inputTime.prop('disabled', false).removeClass('text-body-tertiary');
                $(this).removeClass('text-body-tertiary');
            } else {
                inputTime.prop('disabled', true).addClass('text-body-tertiary');
                $(this).addClass('text-body-tertiary');
            }
        });
    });

    //Reset form in modal
    const resetModal = document.querySelectorAll('.reset-modal-js');
    resetModal.forEach((modal) => {
        modal.addEventListener('hidden.bs.modal', event => {
            let formCheckbox = $(modal).find('form').find('input[type="checkbox"]');
            formCheckbox.each(function(index, checkbox) {
                if (typeof $(checkbox).attr('data-checked') === "undefined") {
                    $(this).prop('checked', false);
                } else {
                    $(this).prop('checked', true);
                }
            });
            //Fix submit disabled
            formCheckbox.first().trigger('change');
        })
    });

    //Add delete link to modal
    $(document).on('click', '[data-delete-href]', function() {
        let deleteName = $(this).data('delete-name');
        let deleteTarget = $(this).data('delete-target');
        let deleteHref = $(this).data('delete-href');
        let deleteTitle = deleteName + ' ' + deleteTarget;

        $('#delete_modal .modal-header .modal-title').find('span').text(deleteTitle);
        $('#delete_modal .modal-footer a').attr('href', deleteHref).find('span').text(deleteName);
    });

    //Add block link to form
    $(document).on('click', '[data-block-href]', function() {
        let blockHref = $(this).data('block-href');
        $('#block_user').find('form').attr('action', blockHref);
    });

    //Show/hidden password
    let password = $('.password');
    password.each(function(index, item) {
        let input = $(item).find('.password-input');
        let btn = $(item).find('.password-btn');
        $(input).on('change input', function() {
            if ($(this).val().length === 0) {
                $(item).removeClass('active');
            } else {
                $(item).addClass('active');
            }
        });
        $(btn).on('click', function() {
            if (!$(this).hasClass('active-show')) {
                $(input).prop("type", "text");
                $(this).addClass('active-show');
            } else {
                $(input).prop("type", "password");
                $(this).removeClass('active-show');
            }
        });
    });

});