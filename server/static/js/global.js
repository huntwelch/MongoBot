$(function() {

  var hidemodal = function(e) {
    if( e.type == "keydown" && e.keyCode != 27 ) return;
    $('modal, #overlay').hide(); 
  };

  $('body').on('keydown', hidemodal); 
  $('#overlay').on('click', hidemodal); 
  $(document).ajaxStart(function() {
    $("loader").show();
  });
  $(document).ajaxComplete(function() {
    $("loader").hide();
  });
});

