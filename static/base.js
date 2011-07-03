function bind(obj, method) {
  var args = Array.prototype.slice.call(arguments, 2);
  return function() {
    var foundArgs = Array.prototype.slice.call(arguments);
    return method.apply(obj, args.concat(foundArgs));
  };
};

function BarrierCallback(done) {
  this.done_ = done;
  this.count_ = 0;
};

BarrierCallback.prototype.done = function() {
  this.count_--;
  if (this.count_ == 0 && this.done_) {
    this.done_();
    this.done_ = null;
  }
};

BarrierCallback.prototype.callback = function() {
  this.count_++;
  return bind(this, this.done);
};
