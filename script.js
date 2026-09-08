    function resetHeight(){
		setTimeout(function() {
        document.body.style.height = window.innerHeight + "px";
        }, 500);
    }
    window.addEventListener("resize", resetHeight);
    window.addEventListener("orientationchange", resetHeight);
    screen.orientation.addEventListener('change', resetHeight);
	resetHeight();
	  
	function multiCmd(urls) {
		if (!Array.isArray(urls)) urls = [urls];
		urls.forEach(function(url) {
		(new Image()).src = url;
		});
	}
	
	const boxes = document.querySelectorAll('.box');
	boxes.forEach(box => {
		box.addEventListener('touchstart', () => box.classList.add('tocuhed'), { passive: true });
		box.addEventListener('touchend', () => box.classList.remove('touched'));
		box.addEventListener('touchcancel', () => box.classList.remove('touched'));
	});

	function fullscreen() {
		var el = document.documentElement
		, rfs = 
		el.requestFullScreen
		|| el.webkitRequestFullScreen
		|| el.mozRequestFullScreen
		|| el.msRequestFullScreen
		;
    if(typeof rfs!="undefined" && rfs){
        rfs.call(el);
		} else if(typeof window.ActiveXObject!="undefined"){
			var wscript = new ActiveXObject("WScript.Shell");
			if (wscript!=null) {
			wscript.SendKeys("{F11}");
			}
		}
	}

	if (window.self !== window.top) {
		document.documentElement.classList.add('in-iframe');
	}