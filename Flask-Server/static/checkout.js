document.addEventListener('DOMContentLoaded', function() {
    // Code to be executed when the DOM is loaded and ready
    let hamButton = document.querySelector('.hamburger');
    let sideBar = document.querySelector('.sidebar');
    let closeButton = document.querySelector('.close')

    hamButton.addEventListener('click', function() {
        sideBar.classList.add('active');
        console.log("class: ", sideBar.className);
    });

    closeButton.addEventListener('click', function() {
        sideBar.classList.remove('active');
    });

});