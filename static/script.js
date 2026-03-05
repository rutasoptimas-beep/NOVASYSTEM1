const canvas = document.getElementById("stars");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let stars = [];

for(let i=0;i<150;i++){

stars.push({
x:Math.random()*canvas.width,
y:Math.random()*canvas.height,
size:Math.random()*2,
speed:Math.random()*0.4
})

}

function draw(){

ctx.clearRect(0,0,canvas.width,canvas.height);

ctx.fillStyle="white";

stars.forEach(star=>{

ctx.beginPath();
ctx.arc(star.x,star.y,star.size,0,Math.PI*2);
ctx.fill();

star.y+=star.speed;

if(star.y>canvas.height){
star.y=0;
}

})

requestAnimationFrame(draw)

}

draw()

/* glow mouse */

const glow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", (e)=>{

glow.style.left = e.clientX + "px";
glow.style.top = e.clientY + "px";

});