import React, { useEffect, useRef } from 'react';

const GravityBubbles = () => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let animationFrameId;

        let particles = [];
        const particleCount = 40;
        const colors = ['#2563eb', '#eab308', '#ef4444', '#22c55e'];

        const mouse = {
            x: null,
            y: null,
            radius: 150
        };

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            init();
        };

        const handleMouseMove = (event) => {
            mouse.x = event.x;
            mouse.y = event.y;
        };

        window.addEventListener('resize', handleResize);
        window.addEventListener('mousemove', handleMouseMove);

        class Particle {
            constructor(x, y, size, color) {
                this.x = x;
                this.y = y;
                this.size = size;
                this.color = color;
                this.baseX = x;
                this.baseY = y;
                this.density = (Math.random() * 30) + 1;
                this.velocity = Math.random() * 2 + 1; // Gravity speed
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.globalAlpha = 0.6;
                ctx.fill();
                ctx.closePath();
            }

            update() {
                // Falling logic (Gravity substitute)
                this.y += this.velocity;
                if (this.y > canvas.height) {
                    this.y = -this.size;
                    this.x = Math.random() * canvas.width;
                }

                // Interaction
                let dx = mouse.x - this.x;
                let dy = mouse.y - this.y;
                let distance = Math.sqrt(dx * dx + dy * dy);
                let forceDirectionX = dx / distance;
                let forceDirectionY = dy / distance;
                let maxDistance = mouse.radius;
                let force = (maxDistance - distance) / maxDistance;
                let directionX = forceDirectionX * force * this.density;
                let directionY = forceDirectionY * force * this.density;

                if (distance < mouse.radius) {
                    this.x -= directionX;
                    this.y -= directionY;
                }
            }
        }

        const init = () => {
            particles = [];
            for (let i = 0; i < particleCount; i++) {
                let size = (Math.random() * 10) + 5;
                let x = Math.random() * canvas.width;
                let y = Math.random() * canvas.height;
                let color = colors[Math.floor(Math.random() * colors.length)];
                particles.push(new Particle(x, y, size, color));
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            for (let i = 0; i < particles.length; i++) {
                particles[i].draw();
                particles[i].update();
            }
            animationFrameId = requestAnimationFrame(animate);
        };

        handleResize();
        animate();

        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('mousemove', handleMouseMove);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                zIndex: -1,
                pointerEvents: 'none',
                background: 'transparent'
            }}
        />
    );
};

export default GravityBubbles;
