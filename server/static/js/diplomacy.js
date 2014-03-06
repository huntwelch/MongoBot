var diplomacy = {
  
  init: function()
  {
    this.update(); 
  },

  update: function()
  {
    var that = this;
    $.ajax(
      '/api/diplomacy/state',
      {
        method: "get",
        dataType: "json",
        success: function(response) { that.display(response) }
      }
    );
  },

  display: function(countries)
  {
    for( country in countries ) {
      info = countries[country];
      color = info['color'];
      provinces = info['opening_positions'];

      console.log(info);
      for( province in provinces ) {
        _p = $('province#' + province);
        _p.addClass(provinces[province]); 
        _p.html('<img src="/static/img/diplomacy/' + province + '/' + color +'.html.png" />')
        _p.show()
      }
    }
  }
};


$(function() {
  diplomacy.init();
});
