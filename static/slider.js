/**
 * opt_options is a struct that contains config options:
 *   .numSteps --> number of steps to break the slider into
 */
function Slider(elem, opt_parentElem, opt_options) {
  this.elem_ = $(elem);
  this.parentElem_ = opt_parentElem;
  this.handleElem_ = $('<a href="#" class="slider-handle"/>');

  if (this.parentElem_) {
    this.parentElem_ = $(this.parentElem_);
  }
  this.options_ = opt_options || {};
  this.handle_ = new SliderHandle(
      this.handleElem_,
      this,
      this.parentElem_);
  this.handleElem_.appendTo(this.elem_);

  this.elem_.click(bind(this, this.onClick));

  if (this.getOpt('numSteps')) {
    var numSteps = this.getOpt('numSteps') - 1;
    var stepSize = 1.0 / numSteps;
    for (var i = 0; i <= numSteps; ++i) {
      var tickElem = $('<div class="slider-tick"/>');
      tickElem.css('left', (100.0 * i * stepSize) + '%');
      tickElem.appendTo(this.elem_);
    }
  }
};

Slider.prototype.getOpt = function(name) {
  if (this.options_.hasOwnProperty(name)) {
    return this.options_[name];
  }
  return null;
};

Slider.prototype.pixelToRatio = function(leftPx) {
  var offset = leftPx - this.elem_.offset().left;
  var width = this.elem_.width();
  var ratio = offset / width;
  return ratio;
};

Slider.prototype.onClick = function(event) {
  this.handle_.setRatio(this.pixelToRatio(event.clientX));
};

function SliderHandle(elem, slider, opt_parentElem) {
  this.elem_ = $(elem);
  this.parentElem_ = opt_parentElem;

  this.slider_ = slider;
  this.originalOffset_ = $.extend(true, {}, this.elem_.offset());
  this.currentRatio_ = 0;
  this.currentStep_ = 0;

  this.elem_.mousedown(bind(this, this.onMouseDown));
  this.stopListenerElem_().mouseup(bind(this, this.onMouseUp));
  this.stopListenerElem_().mouseleave(bind(this, this.cancelDrag_));
};

SliderHandle.prototype.setRatio = function(ratio) {
  if (this.slider_.getOpt('numSteps')) {
    var stepSize = 1.0 / (this.slider_.getOpt('numSteps') - 1);
    this.currentStep_ = Math.round(ratio / stepSize);
    ratio = stepSize * this.currentStep_;
  }
  if (ratio < 0) {
    ratio = 0;
  } else if (ratio > 1) {
    ratio = 1;
  }
  this.currentRatio_ = ratio;
  this.elem_.css('left', 100 * ratio + '%');
};

SliderHandle.prototype.getRatio = function() {
  return this.currentRatio_;
};

SliderHandle.prototype.getStep = function() {
  return this.currentStep_;
};

SliderHandle.prototype.stopListenerElem_ = function() {
  return this.parentElem_ || this.elem_;
};

SliderHandle.prototype.onMouseDown = function(event) {
  event.preventDefault();
  event.stopPropagation();
  this.stopListenerElem_().bind('mousemove.slideHandle',
                                bind(this, this.onMouseDrag));
};

SliderHandle.prototype.onMouseUp = function(event) {
  this.cancelDrag_();
};

SliderHandle.prototype.onMouseDrag = function(event) {
  this.setRatio(this.slider_.pixelToRatio(event.clientX));
};

SliderHandle.prototype.cancelDrag_ = function() {
  this.stopListenerElem_().unbind('mousemove.slideHandle');
};
