unselectAll = function() {
  $(".thumb-selected").removeClass("thumb-selected");
  $(".thumb-start").removeClass("thumb-start");
  $(".thumb-end").removeClass("thumb-end");
};

function SlideTracker() {
  this.downOn_ = null;
  this.lastOn_ = null;
};

SlideTracker.prototype.getRange = function() {
  var start = -1;
  var end = -1;
  if (this.downOn_ || this.downOn_ == 0) {
    start = this.downOn_;
    end = start;
    if (this.lastOn_ || this.lastOn_ == 0) {
      if (this.lastOn_ > start) {
        end = this.lastOn_;
      } else {
        start = this.lastOn_;
      }
    }
  }
  return {start: start, end: end};
};

SlideTracker.prototype.reset = function() {
  this.downOn_ = null;
  this.lastOn_ = null;
};

SlideTracker.prototype.downOn = function(id) {
  this.downOn_ = id;
  this.lastOn_ = id;
};

SlideTracker.prototype.entered = function(id) {
  if (this.downOn_ || this.downOn_ == 0) {
    this.lastOn_ = id;
    return true;
  }
  return false;
};

SlideTracker.prototype.left = function(id) {
  if (id != this.lastOn) {
    return false;
  } else {
    return true;
  }
};

function ThumbUi(elem) {
  this.elem = elem;
  this.id = elem.attr("img_id");

  elem.mousedown(bind(this, this.onMouseDown));
  elem.mouseenter(bind(this, this.onMouseEnter));
  elem.mouseleave(bind(this, this.onMouseLeave));
};

ThumbUi.prototype.onMouseEnter = function(event) {
  if (GLOBAL.tracker.entered(this.id)) {
    this.elem.addClass("thumb-selected");
  }
};

ThumbUi.prototype.onMouseLeave = function(event) {
  if (GLOBAL.tracker.left(this.id)) {
    this.elem.removeClass("thumb-selected");
  }
};

ThumbUi.prototype.onMouseDown = function(event) {
  unselectAll();
  event.preventDefault();
  this.elem.addClass("thumb-selected");
  GLOBAL.tracker.downOn(this.elem.attr("img_id"));
};

onMouseUp = function(e) {
  var range = GLOBAL.tracker.getRange();
  if (range.start != -1) {
    var holder = $("#img_holder");
    holder.empty();
    holder.append($("<img />",
                    { src: "db_img?start=" + range.start + "&end=" + range.end,
                      style: "margin-left:auto;margin-right:auto;display:block"}));
  }
  GLOBAL.tracker.reset();
};

var maybeMouseUp = document.onmouseup;
document.onmouseup = function(e) {
  onMouseUp(e);
  if (maybeMouseUp) {
    maybeMouseUp(e);
  }
};
createImageThumbs = function() {
  imgThumbs = [];
  for (var i = 0; i < 13; ++i) {
    var imgElem = $("<img />", {
      class: "highlight-thumb",
      src: "db_img?start=" + i,
      img_id: i,
      width: 90,
      height: 60,
    });
    imgThumbs.push(imgElem);
    var thumbUi = new ThumbUi(imgElem);
  }
  return imgThumbs;
};
var GLOBAL = {};
window.onload = function() {
  GLOBAL.tracker = new SlideTracker();
  var thumbs = createImageThumbs();
  for (var i = 0; i < thumbs.length; ++i) {
    $("#img_selector").append(thumbs[i]);
  }
  var handle = new SliderHandle($('#handle'), document.body, {maxX: 800, stepSize: 50});
  /*
  var slideFn = function(event, ui) {
    $("#img_slider_value").val("From " + ui.values[0] + " to " + ui.values[1]);
  };
  var slider = $("#img_slider_range").slider(
      { range: true,
        min: 0,
        max: 13,
        values: [0, 0],
        slide: slideFn });
  slideFn(null, {values: [0, 0]});
  */
};
