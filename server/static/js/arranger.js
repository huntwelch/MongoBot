var A = {
  active: '',
  init: function() {
    $('province').draggable();
    this.binder();
  },
  binder: function() {
    var that = this;
    $('province').on('mousedown', function(item) {
      that.active = $(this);
    });

    $('body').on('keydown', function(e) {
      switch( e.which ) {
        case 37:
          axis = 'left';
          adjust = -1;
          break;
        case 39:
          axis = 'left';
          adjust = 1;
          break;
        case 38:
          axis = 'top';
          adjust = -1;
          break;
        case 40:
          axis = 'top';
          adjust = 1;
          break;
        case 13: 
          e = that.active;
          line = "provice#" + e.attr('id') + " { left: " + e.position().left + "px; top: " + e.position().top + "px; }";
          console.log(line);

        default:
          return
      }
      e.preventDefault();
      var base = parseInt(that.active.css(axis));
      base += adjust;
      that.active.css(axis, base);
    });
  }
}; 

$(function() {
  
  A.init();
});
