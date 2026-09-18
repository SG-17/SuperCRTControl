function resetHeight() {
  setTimeout(function () {
    document.body.style.height = window.innerHeight + "px";
  }, 500);
}
window.addEventListener("resize", resetHeight);
window.addEventListener("orientationchange", resetHeight);
if (screen.orientation) {
  screen.orientation.addEventListener("change", resetHeight);
}
resetHeight();

function parseCmdUrl(href) {
  try {
    const u = new URL(href, window.location.href);
    if (!u.searchParams.has("cmd")) return null;
    const ip = u.hostname;
    const cmd = u.searchParams.get("cmd");
    if (!ip || cmd === null || cmd === "") return null;
    return { ip, cmd };
  } catch (_) {
    return null;
  }
}

function sendViaProxy(ip, cmd, transport) {
  const url =
    "/api/cmd?ip=" + encodeURIComponent(ip) +
    "&c=" + encodeURIComponent(cmd) +
    "&transport=" + encodeURIComponent(transport || "tcp");

  return fetch(url)
    .then(function (r) {
      return r.text().then(function (text) {
        if (!r.ok) throw new Error(r.status + " " + text.slice(0, 120));
        return text;
      });
    })
    .catch(function (err) {
      console.warn("SIS proxy failed:", ip, cmd, err);
    });
}

function sendViaHttp(href) {
  (new Image()).src = href;
}

function multiCmd(items) {
  if (!Array.isArray(items)) items = [items];

  items.forEach(function (item) {
    if (typeof item === "string") {
      sendViaHttp(item);
      return;
    }
    if (item && item.url) {
      const transport = (item.transport || "http").toLowerCase();
      if (transport === "tcp" || transport === "http") {
        const parsed = parseCmdUrl(item.url);
        if (parsed) {
          sendViaProxy(parsed.ip, parsed.cmd, transport);
        } else {
          console.warn("multiCmd: could not parse", item.url);
        }
      } else {
        sendViaHttp(item.url);
      }
    }
  });
}

document.addEventListener(
  "click",
  function (e) {
    const a = e.target.closest && e.target.closest("a[data-transport]");
    if (!a) return;

    const transport = (a.getAttribute("data-transport") || "").toLowerCase();
    if (transport !== "tcp" && transport !== "http") return;

    const href = a.getAttribute("href");
    if (!href || href === "#") return;

    const parsed = parseCmdUrl(href);
    if (!parsed) return;

    e.preventDefault();
    e.stopPropagation();
    sendViaProxy(parsed.ip, parsed.cmd, transport);
  },
  true
);

const boxes = document.querySelectorAll(".box");
boxes.forEach(function (box) {
  box.addEventListener(
    "touchstart",
    function () {
      box.classList.add("touched");
    },
    { passive: true }
  );
  box.addEventListener("touchend", function () {
    box.classList.remove("touched");
  });
  box.addEventListener("touchcancel", function () {
    box.classList.remove("touched");
  });
});

function fullscreen() {
    var el = document.documentElement
    , rfs = // for newer Webkit and Firefox
       el.requestFullScreen
    || el.webkitRequestFullScreen
    || el.mozRequestFullScreen
    || el.msRequestFullScreen
    ;

    if(typeof rfs!="undefined" && rfs){

        rfs.call(el);

    } else if(typeof window.ActiveXObject!="undefined"){

        // for Internet Explorer
        var wscript = new ActiveXObject("WScript.Shell");

        if (wscript!=null) {
          wscript.SendKeys("{F11}");
        }
    }

}

if (window.self !== window.top) {
    document.documentElement.classList.add('in-iframe');
  }

