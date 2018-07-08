/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
var showing = false;

function hamburger() {
  if (showing) {
    closeDropdowns();
    showing = false;
  } else {
    document.getElementById("myDropdown").classList.add("show");
    showing = true;
  }
}

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
  if (!event.target.matches('#dropbtn')) {
    closeDropdowns();
    showing = false;
  }
}

function closeDropdowns() {
  var dropdowns = document.getElementsByClassName("dropdown-content");
  var i;
  for (i = 0; i < dropdowns.length; i++) {
    var openDropdown = dropdowns[i];
    if (openDropdown.classList.contains('show')) {
      openDropdown.classList.remove('show');
    }
  }
}