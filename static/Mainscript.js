const tableBody = document.querySelector("#playerTable tbody");
const errorMessageDiv = document.querySelector("#error-message");
const rollNumberDisplay = document.getElementById('RollNumber');
const movePieceButtonsDiv = document.getElementById('movePieceButtons');
const board = document.getElementById('board');
let activePlayerIndex = 0;
let rollResult = null;
let players = [];
let consecutiveSixes = 0;
let hasRolledSix = [];
let rollHistory = [];
let currentTurnRolls = [];


async function getPlayerInfo() {
    try {
        const gameId = sessionStorage.getItem('gameId');
        const response = await axios.get(`/game_players/${gameId}`);
        players = response.data.players;
        console.log('Players:', players);
        sessionStorage.setItem('gameId', response.data.game_id);

        hasRolledSix = new Array(players.length).fill(false);
        rollHistory = new Array(players.length).fill().map(() => []);

        tableBody.innerHTML = '';

        players.forEach((player, index) => {
            const row = tableBody.insertRow();
            const nameCell = row.insertCell();
            const colorCell = row.insertCell();
            const playerPieceCell = row.insertCell();
            const actionCell = row.insertCell();

            nameCell.textContent = player.name;
            colorCell.textContent = player.color;

            updatePlayerPieceDisplay(index);

            const actionButton = document.createElement('button');
            actionButton.textContent = 'Roll Dice';
            actionButton.id = `rollButton${index}`;
            actionButton.addEventListener('click', () => {
                if (index === activePlayerIndex) {
                    handleDiceRoll(player, index, actionButton);
                }
            });
            actionCell.appendChild(actionButton);
        });

        errorMessageDiv.style.display = "none";
        updateButtonStates();
        updateBoard();
    } catch (error) {
        console.error('Error fetching players:', error);
        errorMessageDiv.textContent = "Error fetching players. Please try again later.";
        errorMessageDiv.style.display = "block";
    }
}


function updateButtonStates() {
    players.forEach((player, index) => {
        const button = document.getElementById(`rollButton${index}`);
        if (button) {
            button.disabled = index !== activePlayerIndex;
        }
    });
    console.log(`Active player is now: ${activePlayerIndex}`);
}

function rollDice() {
    return Math.floor(Math.random() * 6) + 1;
}

function sendMove(playerId, pieceIndex) {
    const gameId = sessionStorage.getItem('gameId');

    if (!gameId) {
        alert("Error: Game ID not found. Please restart the game.");
        return;
    }

    axios.post('/playing_game', {
        player_id: playerId,
        player_roll: currentTurnRolls,
        player_move: pieceIndex,
        game_id: gameId
    })
    .then(function (response) {
        console.log(response.data.message);
        alert(response.data.message);

        if (response.data.updated_player_piece) {
            players[playerId].player_piece = response.data.updated_player_piece;
            updatePlayerPieceDisplay(playerId);
            updateBoard();
        }

        rollHistory[playerId] = rollHistory[playerId].concat(currentTurnRolls);
        currentTurnRolls = [];

        if (rollResult !== 6) {
            activePlayerIndex = (activePlayerIndex + 1) % players.length;
            consecutiveSixes = 0;
        }

        rollResult = null;
        rollNumberDisplay.textContent = 'Roll Number';
        movePieceButtonsDiv.innerHTML = '';
        updateButtonStates();
    })
    .catch(function (error) {
        console.error(error);
        alert('Error moving piece. Please try again.');
    });
}



function createMovePieceButtons(player, playerIndex) {
    movePieceButtonsDiv.innerHTML = '';

    for (let i = 0; i < player.player_piece.length; i++) {
        const button = document.createElement('button');
        button.textContent = `Move Piece ${i}`;
        button.id = `Move Piece ${i}`;
        button.addEventListener('click', () => {
            sendMove(playerIndex, i);
        });
        movePieceButtonsDiv.appendChild(button);
    }
}

function handleDiceRoll(player, index, actionButton) {
    rollResult = rollDice();
    rollNumberDisplay.textContent = `Roll: ${rollResult}`;
    alert(`Player ${player.name} rolled a ${rollResult}!`);
    console.log(`Player ${player.name} rolled a ${rollResult}!`);

    currentTurnRolls.push(rollResult);

    if (rollResult === 6) {
        hasRolledSix[index] = true;
        consecutiveSixes++;
        if (consecutiveSixes === 3) {
            alert("Three consecutive sixes! Turn ends without moving.");
            consecutiveSixes = 0;
            activePlayerIndex = (activePlayerIndex + 1) % players.length;
            currentTurnRolls = [];
            updateButtonStates();
            return;
        }
    } else {
        consecutiveSixes = 0;
    }

    if (hasRolledSix[index] || rollResult === 6) {
        createMovePieceButtons(player, index);
    } else {
        alert("No six rolled and haven't rolled a six before. Turn passes to the next player.");
        activePlayerIndex = (activePlayerIndex + 1) % players.length;
        currentTurnRolls = [];
        updateButtonStates();
    }

    // Update player pieces after rolling
    updatePlayerPieces();
}

function updatePlayerPieceDisplay(playerIndex) {
    const playerRow = tableBody.rows[playerIndex];
    const playerPieceCell = playerRow.cells[2];
    const formattedPlayerPieces = players[playerIndex].player_piece
        .map(piece => `[${piece.join(', ')}]`)
        .join(', ');
    playerPieceCell.textContent = `[${formattedPlayerPieces}]`;
}

function updatePlayerPieces() {
    const gameId = sessionStorage.getItem('gameId');

    axios.get(`/game_players/${gameId}`)
        .then(response => {
            players = response.data.players;
            players.forEach((player, index) => {
                updatePlayerPieceDisplay(index);
            });
            updateBoard();
        })
        .catch(error => {
            console.error('Error updating player pieces:', error);
        });
}





///////////////////////////////


function initializeBoard() {
    board.style.display = 'grid';
    board.style.gridTemplateColumns = 'repeat(15, 40px)';
    board.style.gridTemplateRows = 'repeat(15, 40px)';

    for (let row = 0; row < 15; row++) {
        for (let col = 0; col < 15; col++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.id = `cell-${row}-${col}`;

            // Add color classes as needed
            if (row >= 0 && row <= 5 && col >= 0 && col <= 5) {
                cell.classList.add('green');
            } else if (row >= 9 && row <= 14 && col >= 0 && col <= 5) {
                cell.classList.add('yellow');
            } else if (row >= 0 && row <= 5 && col >= 9 && col <= 14) {
                cell.classList.add('red');
            } else if (row >= 9 && row <= 14 && col >= 9 && col <= 14) {
                cell.classList.add('blue');
            }

            board.appendChild(cell);
        }
    }
}

function getInitialPosition(color) {
    switch (color.toLowerCase()) {
        case 'red': return [14, 6];
        case 'green': return [6, 14];
        case 'blue': return [0, 8];
        case 'yellow': return [8, 0];
        default: return [0, 0];
    }
}



function updateBoard() {
    // Clear all existing pieces
    document.querySelectorAll('.piece').forEach(piece => piece.remove());

    players.forEach(player => {
        const color = player.color.toLowerCase();

        player.player_piece.forEach((piece, index) => {
            const [row, col] = piece;

            // Only place pieces that are on the board (not at [0, 0])
            if (row !== 0 || col !== 0) {
                const cell = document.getElementById(`cell-${row}-${col}`);
                if (cell) {
                    const pieceElement = document.createElement('div');
                    pieceElement.classList.add('piece', color);
                    pieceElement.title = `${player.name} - Piece ${index + 1}`;
                    cell.appendChild(pieceElement);
                }
            }
        });
    });
}


function initializeGame() {
    initializeBoard();
    getPlayerInfo().then(() => {
        updateButtonStates();
        updateBoard();
    });
}

initializeGame();