function GraphMaker(dataJson) {
  this.data_ = dataJson;
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
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
    if (keyData.children || opt_zoomKey) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(this, this.graphForKey)
      barElem.click(function() {
        var newContent = boundGraphFn(zoomKey);
        $('#graph').replaceWith(newContent)
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
