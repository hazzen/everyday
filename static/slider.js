function Slider(elem, opt_parentElem) {
  this.elem_ = $(elem);
  this.parentElem_ = opt_parentElem;
  this.handleElem_ = $('<a href="#" class="slider-handle" style="width:10px;border:2px solid black;margin-left:-5px;position:relative"/>');
  this.handle_ = new SliderHandle(this.handleElem_, this, opt_parentElem);

  if (this.parentElem_) {
    this.parentElem_ = $(this.parentElem_);
  }
  this.handleElem_.appendTo(this.elem_);

  this.elem_.click(bind(this, this.onClick));
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

/**
 * opt_options is a struct that contains config options:
 *   .numSteps --> number of steps to break the slider into
 */
function SliderHandle(elem, slider, opt_parentElem, opt_options) {
  this.elem_ = $(elem);
  this.parentElem_ = opt_parentElem;

  this.slider_ = slider;
  this.originalOffset_ = $.extend(true, {}, this.elem_.offset());
  this.startLeftOffset_ = null;
  this.startX_ = null;
  this.options_ = opt_options || {};

  /*
  this.elem_.mousedown(bind(this, this.onMouseDown));
  if (this.parentElem_) {
    this.parentElem_ = $(this.parentElem_);
  }
  this.stopListenerElem_().mouseup(bind(this, this.onMouseUp));
  this.stopListenerElem_().mouseleave(bind(this, this.cancelDrag_));
  */
};

SliderHandle.prototype.opt = function(name) {
  if (this.options_.hasOwnProperty(name)) {
    return this.options_[name];
  }
  return null;
};

SliderHandle.prototype.setRatio = function(ratio) {
  if (this.opt('numSteps')) {
    var stepSize = 1.0 / this.opt('numSteps');
    ratio = stepSize * round(ratio / stepSize);
  }
  if (ratio < 0) {
    ratio = 0;
  } else if (ratio > 1) {
    ratio = 1;
  }
  this.elem_.css('left', 100 * ratio + '%');
};

SliderHandle.prototype.stopListenerElem_ = function() {
  return this.parentElem_ || this.elem_;
};

SliderHandle.prototype.onMouseDown = function(event) {
  event.preventDefault();
  this.stopListenerElem_().bind('mousemove.slideHandle',
                                bind(this, this.onMouseDrag));
  this.startX_ = event.clientX;
  this.startLeftOffset_ = this.elem_.offset().left - this.originalOffset_.left;
};

SliderHandle.prototype.onMouseUp = function(event) {
  this.cancelDrag_();
};

SliderHandle.prototype.onMouseDrag = function(event) {
  var relativeLeft = this.startLeftOffset_ + event.clientX - this.startX_;

  if (this.options_.stepSize) {
    var tweak = relativeLeft % this.options_.stepSize;
    if (tweak < this.options_.stepSize / 2) {
      relativeLeft -= tweak;
    } else {
      relativeLeft += (this.options_.stepSize - tweak);
    }
  }
  if (relativeLeft < 0) {
    relativeLeft = 0;
  } else if (this.options_.maxX && relativeLeft > this.options_.maxX) {
    relativeLeft = this.options_.maxX;
  }
  var newLeft = this.originalOffset_.left + relativeLeft;
  this.elem_.offset({ top: this.originalOffset_.top, left: newLeft });
};

SliderHandle.prototype.cancelDrag_ = function() {
  this.stopListenerElem_().unbind('mousemove.slideHandle');
  this.startX_ = null;
  this.startLeftOffset_ = null;
};
