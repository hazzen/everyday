function GraphMaker(dataJson) {
  this.data_ = dataJson;
};

GraphMaker.prototype.shrinkBars = function(exclude, opt_doneFn) {
  var counter = 0;
  $('.bar').each(function() {
    if (this != exclude) {
      ++counter;
      var valElem = $(this).children('.value');
      var labelElem = $(this).children('.label');
      labelElem.hide();
      valElem.animate({'height': 0}, 1000, function() {
        --counter;
        if (counter == 0) {
          opt_doneFn();
        }
      });
    }
  });
};

GraphMaker.prototype.slideBar = function(
    barElem, amount, opt_doneFn, opt_newWidth) {
  barElem.css({'z-index': 5});
  var cssAnim = {'left': '+=' + amount};
  if (opt_newWidth) {
    cssAnim['width'] = opt_newWidth;
  }
  barElem.animate(cssAnim, 1000, opt_doneFn);
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
  var self = this;
  var barElem = $('<span class="bar" />');
  var keyData = self.data_[key];
  if (keyData) {
    var cssData = {
      'background-color': keyData.rgb,
      'height': (keyData.avg - 32) * 2 + '%'
    };
    $('<span class="value"/>').css(cssData).html(keyData.avg + ' &deg;F').appendTo(barElem);
    if (keyData.label) {
    $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if (keyData.parent || opt_zoomKey) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(self, self.graphForKey)
      barElem.click(function() {
        var newContent = boundGraphFn(zoomKey);

        var titleElem = $('.bargraph.title .bar');
        var curLeft = barElem.position().left;
        var targetLeft = titleElem.position().left;
        var doneFn = null;
        if (curLeft != targetLeft) {
          doneFn = bind(self, self.slideBar,
            barElem,
            targetLeft - curLeft,
            function() { $('#content').replaceWith(newContent); },
            titleElem.css('width'));
        } else {
          var parentData = self.data_[keyData.parent];
          var childIndex = $.inArray(key, parentData.children);
          var numChildren = parentData.children.length;
          targetLeft = barElem.outerWidth(true) + (8 + 300 / numChildren) * childIndex;
          doneFn = bind(self, self.slideBar,
            barElem,
            targetLeft - curLeft,
            function() { $('#content').replaceWith(newContent); },
            300 / numChildren);
        }
        self.shrinkBars(barElem.get(0), doneFn);
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
