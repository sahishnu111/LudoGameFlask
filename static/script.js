

document.getElementById("startGameBtn").addEventListener("click",
       function() {
    const numPlayersInput = document.getElementById("num_of_player");
    const numPlayers = parseInt(numPlayersInput.value); // Convert string to an integer

    if (isNaN(numPlayers) || numPlayers < 2 || numPlayers > 4) {
        alert("Please enter a valid player count (2-4).");
        return false;
    }

    // Now you have the valid 'numPlayers' value. Use it to start your game logic!
    StartGame(numPlayers); // Call the StartGame function with numPlayers as argument
});



