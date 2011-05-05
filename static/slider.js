function SliderHandle(elem, opt_minX, opt_maxX) {
  this.elem_ = elem;
  this.minX_ = opt_minX;
  this.maxX_ = opt_maxX;
  this.originalOffset_ = this.elem_.offset();
  this.startX_ = null;

  this.elem_.mousedown(bind(this, this.onMouseDown));
  this.elem_.mouseup(bind(this, this.onMouseUp));
  this.elem_.mouseleave(bind(this, this.cancelDrag_));
  this.elem_.click(bind(this, this.cancelDrag_));
};

SliderHandle.prototype.onMouseDown = function(event) {
  this.elem_.mousemove(bind(this, this.onMouseDrag));
  this.startX_ = event.clientX;
};

SliderHandle.prototype.onMouseUp = function(event) {
  this.cancelDrag_();
};

SliderHandle.prototype.onMouseDrag = function(event) {
  var newLeft = this.originalOffset_.left + event.clientX - this.startX_;
  this.elem_.offset({ top: this.originalOffset_.top, left: newLeft });
};

SliderHandle.prototype.cancelDrag_ = function() {
  this.elem_.unbind('mousemove');
  this.startX_ = null;
  this.originalOffset_ = this.elem_.offset();
};

var handle = new SliderHandle($('#handle'));
