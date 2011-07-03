function GraphMaker(dataJson) {
  this.data_ = dataJson;
};

GraphMaker.prototype.shrinkBars = function(exclude, opt_doneFn) {
  var cb = new BarrierCallback(opt_doneFn);
  $('.bar').each(function() {
    if (this != exclude) {
      var valElem = $(this).children('.value');
      var labelElem = $(this).children('.label');
      labelElem.hide();
      valElem.animate({'height': 0}, 1000, cb.callback());
    } else {
      var valElem = $(this).children('.value');
      valElem.animate({'height': 1}, 1000);
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

GraphMaker.prototype.replaceGraph = function(newContent, key) {
  var slideElem = null;
  newContent.find('.bar').each(function() {
    if ($(this).data('key') == key) {
      slideElem = $(this);
      slideElem.addClass('moving');
    }
    var valElem = $(this).children('.value');
    valElem.css({'height': '0%'});
  });

  var cb = new BarrierCallback(function() {
    if (slideElem) {
      slideElem.removeClass('moving');
    }
  });

  $('#content').replaceWith(newContent);
  newContent.find('.bar').each(function() {
    var targetHeight = $(this).data('height');
    var valElem = $(this).children('.value');
    valElem.animate({'height': targetHeight}, 1000, cb.callback());
  });
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
  var self = this;
  var barElem = $('<span class="bar" />');
  var keyData = self.data_[key];
  if (keyData) {
    barElem.data('height', (keyData.avg - 32) * 2 + '%');
    barElem.data('key', key);
    var cssData = {
      'background-color': keyData.rgb,
      'height': barElem.data('height')
    };
    $('<span class="value"/>').css(cssData).html(keyData.avg + ' &deg;F').appendTo(barElem);
    if (keyData.label) {
    $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if ((opt_zoomKey && keyData.parent) || 
        (!opt_zoomKey && keyData.children)) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(self, self.graphForKey)
      barElem.click(function() {
        barElem.addClass('moving');
        var newContent = boundGraphFn(zoomKey);

        var titleElem = $('.bargraph.title .bar');
        var curLeft = barElem.position().left;
        var targetLeft = titleElem.position().left;
        var doneFn = null;
        if (curLeft != targetLeft) {
          doneFn = bind(self, self.slideBar,
            barElem,
            targetLeft - curLeft,
            bind(self, self.replaceGraph, newContent, key),
            titleElem.css('width'));
        } else {
          var parentData = self.data_[keyData.parent];
          var childIndex = $.inArray(key, parentData.children);
          var numChildren = parentData.children.length;
          targetLeft = barElem.outerWidth(true) + (8 + 300 / numChildren) * childIndex;
          doneFn = bind(self, self.slideBar,
            barElem,
            targetLeft - curLeft,
            bind(self, self.replaceGraph, newContent, key),
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
    var parentKey = keyData.parent || ':(';
    this.barForKey(key, parentKey).appendTo(titleElem);
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
