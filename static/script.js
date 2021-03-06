
$(document).ready(function () {

	/* implementazione sidebar */
	$('#sidebarCollapse').on('click', function () {
		$('#sidebar').toggleClass('active');
		$('#content').toggleClass('opacity-content');
	});

	/* implementazione accordion nella pagina file */
	var acc = document.getElementsByClassName("accordion");
	var i;

	for (i = 0; i < acc.length; i++) {
	    acc[i].addEventListener("click", function() {
	        this.classList.toggle("active");
	        var panel = this.nextElementSibling;
	        if (panel.style.display === "block") {
	            panel.style.display = "none";
	        } else {
	            panel.style.display = "block";
	        }
	    });
	}
 
 	/* gestione bottone rosso/verde con i bottoni apache */
 	if(document.getElementById('buttonSClickDeactiv') != null){
		document.getElementById("buttonSClickDeactiv").addEventListener("click", manage, false);
 	}
 	if(document.getElementById('buttonSClickActiv') != null){
 		document.getElementById('buttonSClickActiv').addEventListener("click", manage, false);
 	}
 	if(document.getElementById('buttonMClickDeactiv') != null){
		document.getElementById("buttonMClickDeactiv").addEventListener("click", manage, false);loadResult
 	}
 	if(document.getElementById('buttonMClickActiv') != null){
 		document.getElementById('buttonMClickActiv').addEventListener("click", manage, false);
 	}
 	if(document.getElementById('buttonCClickDeactiv') != null){
		document.getElementById("buttonCClickDeactiv").addEventListener("click", manage, false);
 	}
 	if(document.getElementById('buttonCClickActiv') != null){
 		document.getElementById('buttonCClickActiv').addEventListener("click", manage, false);
 	}

	function manage(){
			$('#startButton').css('opacity', '0.5');
			$('#startButton').addClass('disabled');
			$('#stopButton').css('opacity', '0.5');
			$('#stopButton').addClass('disabled');
			$('#statusButton').css('opacity', '0.5');
			$('#statusButton').addClass('disabled');
			$("#pText").show();
	};

	/* gestione modifica textarea onchange per i contenuti di site,module,configuration */
	$('#contentTextarea').change(function(){
		$('#contentTextarea').css("border-color","red");
		$('#modificaTextarea').prop('disabled',false);
	});

	
	// When the user scrolls down 20px from the top of the document, show the button
	window.onscroll = function() {scrollFunction()};

	function scrollFunction() {
	    if (document.body.scrollTop > 25 || document.documentElement.scrollTop > 25) {
	    	if(document.getElementById("myTopButton") != null){
	    		document.getElementById("myTopButton").style.display = "block";
	    	}
	    } else {
	    	if(document.getElementById("myTopButton") != null){
		        document.getElementById("myTopButton").style.display = "none";
		    }
	    }
	}
	

	// When the user clicks on the button, scroll to the top of the document
	$('#myTopButton').click(function() {
	    document.body.scrollTop = 0; // For Safari
	    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
	});

	$('#showPwd').click(function(){
		var x = document.getElementById('password');
		return (x.type === 'password' ? x.type = 'text' : x.type = 'password'); 
	});

	$('#dataDa').datetimepicker({
		format: 'YYYY-MM-DD'
	});

	$('#dataA').datetimepicker({
		format: 'YYYY-MM-DD',
		defaultDate : formatDate(new Date())
	});

	function formatDate(date){
		var day = date.getDate();
		var month = date.getMonth()+1;
		var year = date.getFullYear()
		return year+'-'+month+'-'+day;
	}
});