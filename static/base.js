function bind(obj, method) {
  var args = Array.prototype.slice.call(arguments, 2);
  return function(){
    var foundArgs = Array.prototype.slice.call(arguments);
    return method.apply(obj, args.concat(foundArgs));
  };
};

