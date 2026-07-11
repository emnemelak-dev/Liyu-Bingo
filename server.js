const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const TelegramBot = require('node-telegram-bot-api');

const token = '8680680071:AAH-2szhMnDrstNLtojcWJlerBvTEMYfPf4'; // የእፕን Token እዚህ አስገባ
const bot = new TelegramBot(token, { polling: true });
const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static(__dirname));

// የጨዋታ ሁኔታ
let gameState = {
  status: 'WAITING', // WAITING, PLAYING, FINISHED
  timer: 120, // 2 ደቂቃ (120 ሰከንድ)
  players: [],
  drawnNumbers: [],
  totalPool: 0,
  winnersLine1: [],
  winnersLine2: []
};

// ቦቱ ሲጀምር
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, "እንኳን ወደ **ልዩ ቢንጎ** በሰላም መጡ! የጨዋታውን ሰሌዳ ለመክፈት ከታች ያለውን ቁልፍ ይጫኑ።", {
    reply_markup: {
      inline_keyboard: [[
        { text: "🎮 ልዩ ቢንጎ ተጫወት", web_app: { url: "YOUR_WEB_APP_URL" } } // Hosting ከተደረገ በኋላ የሚገባ URL
      ]]
    }
  });
});

// የ2 ደቂቃ ሰዓት ቆጣሪ እና የጨዋታ ሂደት
setInterval(() => {
  if (gameState.status === 'WAITING') {
    gameState.timer--;
    io.emit('timerUpdate', gameState.timer);

    if (gameState.timer <= 0) {
      if (gameState.players.length > 0) {
        gameState.status = 'PLAYING';
        startGame();
      } else {
        gameState.timer = 120; // ተጫዋች ከሌለ ሰዓቱን እንደገና ማስጀመር
      }
    }
  }
}, 1000);

function startGame() {
  io.emit('gameStarted', { pool: gameState.totalPool });
  
  // በየ 4 ሰከንዱ አዲስ ቁጥር ማውጣት
  const numberInterval = setInterval(() => {
    if (gameState.drawnNumbers.length >= 75 || gameState.status === 'FINISHED') {
      clearInterval(numberInterval);
      return;
    }

    let nextNum;
    do {
      nextNum = Math.floor(Math.random() * 75) + 1;
    } while (gameState.drawnNumbers.includes(nextNum));

    gameState.drawnNumbers.push(nextNum);
    io.emit('newNumber', nextNum);
  }, 4000);
}

// Socket.io ግንኙነት
io.on('connection', (socket) => {
  socket.emit('init', gameState);

  // ካርድ መግዛት (10 ብር)
  socket.on('buyCard', (userData) => {
    if (gameState.status === 'WAITING') {
      gameState.players.push({ id: socket.id, user: userData });
      gameState.totalPool += 10;
      io.emit('poolUpdated', gameState.totalPool);
      socket.emit('cardPurchased', generateBingoCard());
    }
  });

  // ቢንጎ ጥያቄ (1 መስመር ወይም 2 መስመር)
  socket.on('claimBingo', (data) => {
    // ህጉን ማረጋገጫ (1 መስመር = 30%, 2 መስመር = 50%)
    if (data.type === 1 && gameState.winnersLine1.length === 0) {
      gameState.winnersLine1.push(socket.id);
      const prize = (gameState.totalPool * 0.30) / gameState.winnersLine1.length;
      io.emit('bingoWin', { type: '1 መስመር', prize, winner: socket.id });
    } else if (data.type === 2 && gameState.winnersLine2.length === 0) {
      gameState.winnersLine2.push(socket.id);
      const prize = (gameState.totalPool * 0.50) / gameState.winnersLine2.length;
      io.emit('bingoWin', { type: '2 መስመር (ሙሉ ቢንጎ)', prize, winner: socket.id });
      gameState.status = 'FINISHED'; // ጨዋታው ተጠናቀቀ (ቀሪው 20% ለባለቤቱ ይሄዳል)
    }
  });
});

function generateBingoCard() {
  // 5x5 የቢንጎ ሰሌዳ ማመንጨት
  let card = [];
  for (let i = 0; i < 5; i++) {
    let row = [];
    for (let j = 0; j < 5; j++) {
      if (i === 2 && j === 2) {
        row.push("FREE"); // መሀል ሳጥን ነፃ
      } else {
        row.push(Math.floor(Math.random() * 15) + (j * 15) + 1);
      }
    }
    card.push(row);
  }
  return card;
}

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
