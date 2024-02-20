document.addEventListener('DOMContentLoaded', function () {
    const images = [
        "/static/css/images/aboutme/alex0.jpeg",
        "/static/css/images/aboutme/alex1.png",
        "/static/css/images/aboutme/alex2.jpeg",
        "/static/css/images/aboutme/alex3.jpeg",
        "/static/css/images/aboutme/alex4.jpeg",
        "/static/css/images/aboutme/alex5.jpeg",
        "/static/css/images/aboutme/alex6.jpeg",
        "/static/css/images/aboutme/alex7.jpeg",
        "/static/css/images/aboutme/alex8.jpeg",
        "/static/css/images/aboutme/alex9.jpeg"
    ];
    const aboutMeImage = document.getElementById('about_me_image');
    let currentIndex = 0;

    setInterval(function () {
        currentIndex = (currentIndex + 1) % images.length; // Wechsle zum nächsten Bild, wiederholen, wenn das Ende erreicht ist
        aboutMeImage.src = images[currentIndex]; // Ändere die src-Eigenschaft des Bildes
    }, 5000);
});
