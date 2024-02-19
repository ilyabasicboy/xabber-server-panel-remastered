$(function () {
    $('.submit-form-js').on('submit', function(e){
        $('.step.active').removeClass('active');
        $('.content.active').removeClass('active');

        $('.step[data-target="#installation"]').addClass('active');
        $('#installation').addClass('active');
    });
});