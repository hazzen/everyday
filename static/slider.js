/**
 * opt_options is a struct that contains config options:
 *   .maxX --> maximum x (in pixels) that we can drag to
 *   .stepSize --> we make sure the current offset % stepSize == 0
 */
function SliderHandle(elem, opt_parentElem, opt_options) {
  this.elem_ = $(elem);
  this.parentElem_ = opt_parentElem;
  this.originalOffset_ = $.extend(true, {}, this.elem_.offset());
  this.startLeftOffset_ = null;
  this.startX_ = null;
  this.options_ = opt_options || {};

  this.elem_.mousedown(bind(this, this.onMouseDown));
  if (this.parentElem_) {
    this.parentElem_ = $(this.parentElem_);
  }
  this.stopListenerElem_().mouseup(bind(this, this.onMouseUp));
  this.stopListenerElem_().mouseleave(bind(this, this.cancelDrag_));
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
