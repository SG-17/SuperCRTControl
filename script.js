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
