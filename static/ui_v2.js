function GraphMaker(dataJson) {
  this.data_ = dataJson;
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
  var self = this;
  var barElem = $('<span class="bar" />');
  var keyData = self.data_[key];
  if (keyData) {
    var cssData = {
      'background-color': keyData.rgb,
      'height': keyData.avg + '%'
    };
    $('<span class="value"/>').css(cssData).html(keyData.avg + ' &deg;F').appendTo(barElem);
    if (keyData.label) {
    $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if (keyData.children || opt_zoomKey) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(self, self.graphForKey)
      barElem.click(function() {
        $('.bar .value').each(function(index) {
          if (this != barElem.children('.value').get(0)) {
            $(this).css({'height': 1});
          }
        });
        var newContent = boundGraphFn(zoomKey);
        var titleElem = $('.bargraph.title .bar');
        var curLeft = barElem.position().left;
        var targetLeft = titleElem.position().left;
        barElem.css({'z-index': 5});
        if (curLeft != targetLeft) {
          barElem.animate({
            'left': '-=' + (curLeft - targetLeft),
            'width': titleElem.css('width'),
          }, 1000, function() {
            $('#graph').replaceWith(newContent)
          });
        } else {
          var parentData = self.data_[keyData.parent];
          var childIndex = $.inArray(key, parentData.children);
          var numChildren = parentData.children.length;
          targetLeft = barElem.outerWidth(true) + (300 / numChildren) * childIndex;
          barElem.animate({
            'left': '+=' + (targetLeft - curLeft),
            'width': 300 / numChildren,
          }, 1000, function() {
            $('#graph').replaceWith(newContent)
          });
        }
      });
    }
  }
  return barElem;
};

GraphMaker.prototype.graphForKey = function(key) {
  var topLevelElem = $('<div id="content"/>');
  var graphElem = $('<div id="graph"/>');
  var titleElem = $('<div class="bargraph title"/>');
  var childElem = $('<div class="bargraph"/>');
  var keyData = this.data_[key];
  if (keyData) {
    var parentKey = keyData.parent;
    this.barForKey(key, parentKey, true).appendTo(titleElem);
    var subKeys = keyData.children;
    var len = subKeys.length;
    for (var i = 0; i < len; ++i) {
      var bar = this.barForKey(subKeys[i]);
      bar.css({'width': 300 / len});
      bar.appendTo(childElem);
    }
  }
  titleElem.appendTo(graphElem);
  childElem.appendTo(graphElem);
  graphElem.appendTo(topLevelElem);
  return topLevelElem;
};
