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
  this.curKey_ = null;
  this.ignoreClicks_ = false;
  this.lastShownSlider_ = null;;

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
    joined.push(this.baseBarFor_(key));
  }
  return joined;
};

GraphMaker.prototype.sliderGoalposts_ = function(key, opt_offset) {
  var goalposts = $('.mini-bargraph .bar[hlk*="' + key + '"]');
  var leftElem = goalposts.first();
  var rightElem = goalposts.first();
  if (opt_offset) {
    return {'left': goalposts.first().offset().left,
            'right': goalposts.last().offset().left + goalposts.width()};
  } else {
    return {'left': goalposts.first().position().left,
            'right': goalposts.last().position().left + goalposts.width()};
  }
};

GraphMaker.prototype.positionSlider_ = function(sliderElem, key) {
  var goalposts = this.sliderGoalposts_(key);
  sliderElem.css('left', goalposts.left);
  sliderElem.css('width', goalposts.right - goalposts.left);
};

GraphMaker.prototype.showSubSlider_ = function(key) {
  var subSliderElem = $('#guide-graph-sub-slider');
  subSliderElem.show();
  this.positionSlider_(subSliderElem, key);
  this.lastShownSlider_ = key;
};

GraphMaker.prototype.hideSubSlider_ = function() {
  var subSliderElem = $('#guide-graph-sub-slider');
  subSliderElem.hide();
};

GraphMaker.prototype.guideBarsMouseMove_ = function(event, opt_key, opt_noUp) {
  var key = opt_key || this.curKey_;
  var data = this.data_[key];
  if (data && data.children) {
    var curGoals = this.sliderGoalposts_(key, true);
    if (event.pageX >= curGoals.left && event.pageX <= curGoals.right) {
      if (opt_key) {
        this.showSubSlider_(key);
      } else {
        var self = this;
        $.each(data.children, function (index, value) {
            self.guideBarsMouseMove_(event, value, true);
        });
      }
    } else if (data.parent && !opt_noUp) {
      this.guideBarsMouseMove_(event, data.parent);
    }
  }
}

GraphMaker.prototype.onGuideBarsClick_ = function() {
  if (this.lastShownSlider_) {
    this.onBarClick_(this.lastShownSlider_, this.lastShownSlider_);
  }
};

GraphMaker.prototype.makeGuideBars = function() {
  var allElems = this.makeGuideBarsRecurse_('r');
  var graphElem = $('<div class="mini-bargraph"/>');
  var topLevelElem = $('<div id="guide-graph"/>');
  $.each(allElems, function(index, value) { value.appendTo(graphElem); });
  graphElem.appendTo(topLevelElem);

  $('<div id="guide-graph-slider"/>').appendTo(topLevelElem);
  $('<div id="guide-graph-sub-slider"/>').appendTo(topLevelElem);

  graphElem.click(bind(this, this.onGuideBarsClick_));
  graphElem.mousemove(bind(this, this.guideBarsMouseMove_));
  graphElem.mouseleave(bind(this, this.hideSubSlider_));

  return topLevelElem;
};

GraphMaker.prototype.shrinkBars = function(opt_exclude, opt_doneFn) {
  var cb = new BarrierCallback(opt_doneFn);
  $('.bargraph .bar').each(function() {
    if (opt_exclude == null || this != opt_exclude.get(0)) {
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
  barElem.animate(cssAnim, GLOBALS.animateTime, 'swing', opt_doneFn);
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

  var self = this;
  var cb = new BarrierCallback(function() {
    if (slideElem) {
      slideElem.removeClass('moving');
    }
    self.ignoreClicks_ = false;
  });

  $('#graph').replaceWith(newContent);
  newContent.find('.bargraph .bar').each(function() {
    var targetHeight = $(this).data('height');
    var valElem = $(this).children('.value');
    valElem.animate({'height': targetHeight}, GLOBALS.animateTime, cb.callback());
  });
  var makeOpaque = function(selector) {
    var cssAnim = {'opacity': 1};
    return function() { $(selector).animate(cssAnim); };
  };
  $('#img1').attr('onload', makeOpaque('#img1')).attr('src', 'composites/1' + key + '.jpg');
  $('#img0').attr('onload', makeOpaque('#img0')).attr('src', 'composites/0' + key + '.jpg');
};

GraphMaker.prototype.onBarClick_ = function(key, zoomKey, opt_barElem) {
  if (this.ignoreClicks_) { return; }
  var keyData = this.data_[key];
  this.ignoreClicks_ = true;
  $('.bar').unbind();
  this.hideSubSlider_();
  this.positionSlider_($('#guide-graph-slider'), zoomKey);
  $('#img0, #img1').animate({'opacity': 0}, GLOBALS.animateTime);

  var newContent = this.graphForKey(zoomKey);

  var doneFn = null;
  if (opt_barElem) {
    opt_barElem.addClass('moving');
    var titleElem = $('.bargraph.title .bar');
    var curLeft = opt_barElem.position().left;
    var targetLeft = titleElem.position().left;
    if (curLeft != targetLeft) {
      doneFn = bind(this, this.slideBar,
        opt_barElem,
        targetLeft - curLeft,
        bind(this, this.replaceGraph, newContent, key),
        titleElem.css('width'));
    } else {
      var parentData = this.data_[keyData.parent];
      var childIndex = $.inArray(key, parentData.children);
      var numChildren = parentData.children.length;
      targetLeft = opt_barElem.outerWidth(true) + (8 + 300 / numChildren) * childIndex;
      doneFn = bind(this, this.slideBar,
        opt_barElem,
        targetLeft - curLeft,
        bind(this, this.replaceGraph, newContent, key),
        300 / numChildren);
    }
  } else {
    doneFn = bind(this, this.replaceGraph, newContent, key);
  }
  this.shrinkBars(opt_barElem, doneFn);
};

GraphMaker.prototype.barForKey = function(key, opt_zoomKey) {
  var barElem = this.baseBarFor_(key, true);
  var keyData = this.data_[key];
  if (keyData) {
    if (keyData.label) {
      $('<span class="label"/>').text(keyData.label).appendTo(barElem);
    }
    if ((opt_zoomKey && keyData.parent) ||
        (!opt_zoomKey && keyData.children)) {
      var zoomKey = opt_zoomKey || key;
      barElem.mouseover(bind(this, this.showSubSlider_, zoomKey));
      barElem.mouseout(bind(this, this.hideSubSlider_));
      barElem.css({'cursor': 'pointer'});
      barElem.click(bind(this, this.onBarClick_, key, zoomKey, barElem));
    }
  }
  return barElem;
};

GraphMaker.prototype.graphForKey = function(key) {
  this.curKey_ = key;
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
