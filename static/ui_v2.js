function initPage() {
  $('#about').click(function() { $(this).toggle('slow'); });
  $('#about-button').click(function() { $('#about').toggle('slow'); });
}

if (typeof(GLOBALS) == 'undefined') {
  GLOBALS = {};
}
GLOBALS.animateTime = 600;

function GraphMaker(dataJson) {
  this.data_ = dataJson;

  $(window).resize(bind(this, this.resizePage));
};

GraphMaker.prototype.baseBarFor_ = function(key, opt_valueText) {
  var barElem = $('<span class="bar" />');
  var keyData = this.data_[key];
  if (keyData) {
    barElem.data('height', (keyData.avg - 32) * 2 + '%');
    barElem.data('key', key);
    var cssData = {
      'background-color': keyData.rgb,
      'height': barElem.data('height')
    };
    var valueElem = $('<span class="value"/>').css(cssData).appendTo(barElem);
    if (opt_valueText) {
      valueElem.html(keyData.avg + ' &deg;F');
    }
  }
  return barElem;
};

GraphMaker.prototype.makeGuideBarsRecurse_ = function(key) {
  var self = this;
  var topLevel = this.data_[key];
  var joined = [];
  if (topLevel.children && topLevel.children.length) {
    $.each(topLevel.children, function(index, val) {
      var returned = self.makeGuideBarsRecurse_(val);
      $.merge(joined, returned);
    });
    var firstAttr = joined[0].attr('hlk') || '';
    joined[0].attr('hlk', firstAttr + ' ' + key);
    var lastAttr = joined[joined.length - 1].attr('hlk') || '';
    joined[joined.length - 1].attr('hlk', lastAttr + ' ' + key);
  } else {
    joined.push(self.baseBarFor_(key));
  }
  return joined;
};

GraphMaker.prototype.positionSlider_ = function(sliderElem, key) {
  var goalposts = $('.mini-bargraph .bar[hlk*="' + key + '"]');
  var left = goalposts.first().position().left;
  var right = goalposts.last().position().left + goalposts.width();
  sliderElem.css('left', left);
  sliderElem.css('width', right - left);
};

GraphMaker.prototype.showSubSlider_ = function(key) {
  var subSliderElem = $('#guide-graph-sub-slider');
  subSliderElem.show();
  this.positionSlider_(subSliderElem, key);
};

GraphMaker.prototype.hideSubSlider_ = function(key) {
  var subSliderElem = $('#guide-graph-sub-slider');
  subSliderElem.hide();
};

GraphMaker.prototype.makeGuideBars = function() {
  var allElems = this.makeGuideBarsRecurse_('root');
  var graphElem = $('<div class="mini-bargraph"/>');
  var topLevelElem = $('<div id="guide-graph"/>');
  $.each(allElems, function(index, value) { value.appendTo(graphElem); });
  graphElem.appendTo(topLevelElem);

  $('<div id="guide-graph-slider"/>').appendTo(topLevelElem);
  $('<div id="guide-graph-sub-slider"/>').appendTo(topLevelElem);

  return topLevelElem;
};

GraphMaker.prototype.shrinkBars = function(exclude, opt_doneFn) {
  var cb = new BarrierCallback(opt_doneFn);
  $('.bargraph .bar').each(function() {
    if (this != exclude) {
      var valElem = $(this).children('.value');
      var labelElem = $(this).children('.label');
      labelElem.hide();
      valElem.animate({'height': 0}, GLOBALS.animateTime, cb.callback());
    } else {
      var valElem = $(this).children('.value');
      valElem.animate({'height': 1}, GLOBALS.animateTime);
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
  barElem.animate(cssAnim, 2 * GLOBALS.animateTime, 'swing', opt_doneFn);
};

GraphMaker.prototype.replaceGraph = function(newContent, key) {
  var slideElem = null;
  newContent.find('.bargraph .bar').each(function() {
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

  $('#graph').replaceWith(newContent);
  newContent.find('.bargraph .bar').each(function() {
    var targetHeight = $(this).data('height');
    var valElem = $(this).children('.value');
    valElem.animate({'height': targetHeight}, GLOBALS.animateTime, cb.callback());
  });
  $('#img1').attr('src', 'composites/1' + key + '.jpg');
  $('#img0').attr('src', 'composites/0' + key + '.jpg');
  $('#img0, #img1').animate({'height': '100%'}, GLOBALS.animateTime);
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
  var self = this;
  var barElem = self.baseBarFor_(key, true);
  var keyData = self.data_[key];
  if (keyData) {
    if (keyData.label) {
      $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if ((opt_zoomKey && keyData.parent) ||
        (!opt_zoomKey && keyData.children)) {
      var zoomKey = opt_zoomKey || key;
      var boundGraphFn = bind(self, self.graphForKey)
      barElem.mouseover(function() {
        self.showSubSlider_(zoomKey);
      });
      barElem.mouseout(function() {
        self.hideSubSlider_();
      });
      barElem.click(function() {
        $('.bar').unbind();
        self.hideSubSlider_();
        self.positionSlider_($('#guide-graph-slider'), zoomKey);
        $('#img0, #img1').animate({'height': 0}, GLOBALS.animateTime);
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
  return graphElem;
};

GraphMaker.prototype.resizePage = function() {
  var heightPadding = 360;
  var brackets = [
    {'reqWidth': 1280, 'reqHeight': 480},
    {'reqWidth': 800,  'reqHeight': 300},
    {'reqWidth': 620,  'reqHeight': 240},
  ];
  var width = $(window).width();
  var height = $(window).height();
  var bracketsLength = brackets.length;
  for (var i = 0; i < bracketsLength; ++i) {
    if (i == bracketsLength - 1 || (width >= brackets[i].reqWidth &&
                                    height >= brackets[i].reqHeight + heightPadding)) {
      $('#img0, #img1').width(brackets[i].reqWidth / 2);
      $('#imgs').width(brackets[i].reqWidth).height(brackets[i].reqHeight);
      break;
    }
  }
};
