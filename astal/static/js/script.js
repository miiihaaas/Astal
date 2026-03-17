let mouseX = 0, mouseY = 0;
let ballX = 0, ballY = 0;

const ball = document.getElementById('ball');

function setInitialPosition(event) {
    mouseX = event.clientX + window.scrollX;
    mouseY = event.clientY + window.scrollY;
    ballX = mouseX;
    ballY = mouseY;
    ball.style.transform = `translate(${ballX - ball.clientWidth / 2}px, ${ballY - ball.clientHeight / 2}px)`;
    document.removeEventListener('mousemove', setInitialPosition);
}

document.addEventListener('mousemove', setInitialPosition);

document.addEventListener('mousemove', (event) => {
    mouseX = event.clientX + window.scrollX;
    mouseY = event.clientY + window.scrollY;
});

function animate() {
    ballX += (mouseX - ballX) * 0.1;
    ballY += (mouseY - ballY) * 0.1;

    ball.style.transform = `translate(${ballX - ball.clientWidth / 2}px, ${ballY - ball.clientHeight / 2}px)`;

    requestAnimationFrame(animate);
}

animate();

const activeElements = document.querySelectorAll('input, a, button, select, textarea');

activeElements.forEach(element => {
    element.addEventListener('mouseover', () => {
        ball.style.width = '120px';
        ball.style.height = '120px';
        ball.style.opacity = '0.2';
    });

    element.addEventListener('mouseout', () => {
        ball.style.width = '12px';
        ball.style.height = '12px';
        ball.style.opacity = '1';
    });
});