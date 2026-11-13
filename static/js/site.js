// بدون inline-script تا با CSP سازگار باشد.
document.addEventListener("submit", function (e) {
  var msg = e.target.getAttribute("data-confirm");
  if (msg && !window.confirm(msg)) { e.preventDefault(); }
});
document.addEventListener("click", function (e) {
  var t = e.target.closest("[data-thumb]");
  if (t) {
    var main = document.getElementById("main-img");
    if (main) { main.src = t.getAttribute("data-thumb"); }
  }
});
