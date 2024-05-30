document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('change-picture-btn').addEventListener('click', function() {
      var images = [
        '/static/css/images/aboutme/alex0.png',
        '/static/css/images/aboutme/alex1.png',
        '/static/css/images/aboutme/alex2.png',
        '/static/css/images/aboutme/alex5.png'
      ];

      var currentImageSrc = document.getElementById('profile-picture').src.split('/').pop();
      var currentImageIndex = images.map(function(image) { return image.split('/').pop(); }).indexOf(currentImageSrc);
      
      var nextImageIndex = (currentImageIndex + 1) % images.length;
      
      document.getElementById('profile-picture').src = images[nextImageIndex];
  });
});



//Slideshow
$(document).ready(function() {
  var slideIndex = 0;
  var slides = $(".mySlides");
  var delay = 3000;

  // Alle Slides verstecken außer dem ersten
  slides.not(':eq(0)').removeClass('active');
  slides.eq(0).addClass('active');

  function showNextSlide() {
    // Aktuelle Klasse entfernen
    slides.eq(slideIndex).removeClass('active');

    // Index erhöhen und Loop durchführen
    slideIndex = (slideIndex + 1) % slides.length;

    // Nächste Slide anzeigen
    slides.eq(slideIndex).addClass('active');
  }

  // Interval für das Wechseln der Slides
  setInterval(showNextSlide, delay);
});








