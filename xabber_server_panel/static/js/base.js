$(function () {

    let url, page, updateChange, updateTooltip;
    function ajax_send(url, page='', updateChange=false, updateTooltip=false) {
        let ajax_url = url + page;

        //Create the data objec`t with query parameters
        let data = {};

        $.get(ajax_url, data, function(data) {
            $('.list-js').html(data['html']);
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
        $(this).parents('.form-host-js').trigger('submit');
    });

    //Loader block
    let loader = '<div class="d-flex align-items-center justify-content-center position-absolute top-0 start-0 w-100 h-100 bg-body bg-opacity-75 z-3"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';

    $('.list-js').on('click', '.pagination a', function(e) {
        e.preventDefault();

        let url = $(this).parents('.list-js').data('url');

        //Add Loader
        $(this).parents('.list-js').find('.table-adaptive').append(loader);

        ajax_send(url, $(this).attr('href'));
    });

    //Check dns records ajax
    function checkHost() {
        $('.check-records-js, .check-cert-js').on('click', function(e) {
            e.preventDefault();
            let $this = $(this);
            let url = $this.data('url');

            if ($this.hasClass('check-records-js')) {
                $this.find('.spinner-border').removeClass('d-none');
                $this.attr('disabled', true);
            }

            if ($this.hasClass('check-cert-js')) {
                $this.parents('.host-list-js').find('.table-adaptive').append(loader);
            }

            $.get(url, {}, function(data) {
                if ($this.hasClass('check-records-js')) {
                    $this.find('.spinner-border').addClass('d-none');
                    $this.attr('disabled', false);
                }

                $('.host-list-js').html(data);

                //Reset check change
                checkChange();
                checkHost();
            });
        });
    }
    checkHost();

    //Separate logic for search
    let target, object;
    function search_ajax(url, $target=$('.search-list-js'), object='', page='') {
        let ajax_url = url + page;
        let query = $('.search-list-js').data('querystring');

        //Parse the query string into an object
        let queryParams = {};
        query.split('&').forEach(function (param) {
            var keyValue = param.split('=');
            if (keyValue[0] != 'page'){
                queryParams[keyValue[0]] = keyValue[1];
            }
        });

        //Create the data objec`t with query parameters
        let data = {
            'object': object,
            ...queryParams
        };

        $.get(ajax_url, data, function(data){
            $target.html(data['html']);
            setCurrentUrl();
            searchPagination();
        });
    };

    function searchPagination() {
        $('.search-pagination-js').on('click', '.pagination a', function(e){
            e.preventDefault();

            //Add Loader
            $(this).parents('.search-pagination-js').find('.table-adaptive').append(loader);

            search_ajax(
                $('.search-list-js').data('url'),
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

    //Reset form checkbox in modal
    const resetCheckboxModal = document.querySelectorAll('.reset-checkbox-modal-js');
    resetCheckboxModal.forEach((modal) => {
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

    //Reset form select multiple in modal
    const resetSelectmModal = document.querySelectorAll('.reset-selectm-modal-js');
    resetSelectmModal.forEach((modal) => {
        modal.addEventListener('hidden.bs.modal', event => {
            $(modal).find('form')[0].reset();

            let formSelectm = $(modal).find('form').find('select');
            $(formSelectm).find('option').prop('selected', false).trigger('chosen:updated');

            //Update for members
            $('#id_members_to option:not([data-selected])').appendTo('#id_members_from');
            $('#id_members_from option[data-selected]').appendTo('#id_members_to');
            updateHiddenFields(); //Update hidden fields after removing all
        })
    });

    //Add delete link to modal
    $(document).on('click', '[data-delete-href]', function() {
        let deleteName = $(this).data('delete-name');
        let deleteTarget = $(this).data('delete-target');
        let deleteHref = $(this).data('delete-href');
        let deleteTitle = deleteName + ' \"' + deleteTarget + '\"';

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

    //Start server loading
    let startserverForm = $('.form-startserver-js');
    let startserverLoader = $('.loader-startserver-js');
    let startserverModal = new bootstrap.Modal(document.querySelector('#start_server'), {});
    $(startserverForm).on('submit', function() {
        startserverModal.hide();
        startserverLoader.find('.spinner-border').removeClass('d-none');
    });

    //Selector widget
    //Function to update hidden fields with selected members
    function updateHiddenFields() {
        var selectedOptions = $('#id_members_to option');
        var values = selectedOptions.map(function() {
            return this.value;
        }).get();
        $('#id_members_to_hidden').val(values.join(','));
        $('#id_members_to_hidden').trigger('change');
    }

    //Filter avaliable members
    $('#id_members_input').on('input', function() {
        var filter = $(this).val().toLowerCase();
        $('#id_members_from option').each(function() {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(filter));
        });
    });

    //Add selected members
    $('#id_members_add_link').on('click', function(e) {
        e.preventDefault();
        $('#id_members_from option:selected').appendTo('#id_members_to');
        updateHiddenFields(); //Update hidden fields after adding
    });

    //Remove selected members
    $('#id_members_remove_link').on('click', function(e) {
        e.preventDefault();
        $('#id_members_to option:selected').appendTo('#id_members_from');
        updateHiddenFields(); //Update hidden fields after removal
    });

    //Choose all members at once
    $('#id_members_add_all_link').on('click', function(e) {
        e.preventDefault();
        $('#id_members_from option').appendTo('#id_members_to');
        updateHiddenFields(); //Update hidden fields after adding all
    });

    //Remove all members at once
    $('#id_members_remove_all_link').on('click', function(e) {
        e.preventDefault();
        $('#id_members_to option').appendTo('#id_members_from');
        updateHiddenFields(); //Update hidden fields after removing all
    });

    //Double-click for quick adding and removing of members
    $('#id_members_from').on('dblclick', 'option', function() {
        $(this).appendTo('#id_members_to');
        updateHiddenFields(); //Update hidden fields after double-click
    });

    $('#id_members_to').on('dblclick', 'option', function() {
        $(this).appendTo('#id_members_from');
        updateHiddenFields(); //Update hidden fields after double-click
    });

    //Double-click for mobile
    $('#id_members_from, #id_members_to').on('touchstart', 'option', function(event) {
        let now = new Date().getTime();
        let lastTouch = $(this).data('lastTouch') || now + 1;
        let delta = now - lastTouch;
            if (delta < 500 && delta > 0) {
                $(this).trigger('dblclick');
                $(this).data('lastTouch', null);
            } else {
            $(this).data('lastTouch', now);
        }
    });

});