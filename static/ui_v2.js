function GraphMaker(dataJson) {
  this.data_ = dataJson;
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey, opt_isBig) {
  var barElem = $('<span class="bar" />');
  var keyData = this.data_[key];
  if (keyData) {
    var cssData = {
      'background-color': keyData.rgb,
      'height': keyData.avg + '%'
    };
    $('<span class="value"/>').css(cssData).html(keyData.avg + ' &deg;F').appendTo(barElem);
    if (keyData.label) {
    $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if (opt_isBig) {
      barElem.addClass('big-bar');
    }
    if (keyData.children || opt_zoomKey) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(this, this.graphForKey)
      barElem.click(function() {
        var newContent = boundGraphFn(zoomKey);
        $('.bargraph').replaceWith(newContent)
      });
    }
  }
  return barElem;
};

GraphMaker.prototype.graphForKey = function(key) {
  var graphElem = $('<div class="bargraph" />');
  var keyData = this.data_[key];
  if (keyData) {
    var parentKey = keyData.parent;
    this.barForKey(key, parentKey, true).appendTo(graphElem);
    var subKeys = keyData.children;
    var len = subKeys.length;
    for (var i = 0; i < len; ++i) {
      this.barForKey(subKeys[i]).appendTo(graphElem);
    }
  }
  return graphElem;
};
