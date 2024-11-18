const SUITS = ["s", "p", "m"];
const HONORS = ["Ea", "No", "So", "We", "Gr", "Re", "Wh"]
const SEAT_NAMES = ["East", "South", "West", "North"]

class MahjongPlayer {
    constructor() {
        this.hand = [];
        this.discarded = null;
        this.melds = null;

        this.inRichii = false;
    }
}

class tileSetHandler {
    constructor(players) {
        this.undrawn_tiles = this.createTileset();
        this.players = players;
        this.deadWall = [];
        this.buildDeadWall();
        this.dora = null;
        this.hasDealt = false;      
    }

    createTileset(){
        let tiles = []
        for (let suit of SUITS) {
            for (let i = 1; i < 11; i++) {
                for (let j = 0; j < 4; j++) {
                    let tile = `${i}${suit}`;
                    tiles.push(tile);
                }
                if (i == 5) {
                    tiles.pop();
                    tiles.push(`5${suit}*`); // red tile
                }
            }
        }
        for (let tile of HONORS) {
            for (let i = 0; i < 4; i++) {
                tiles.push(tile);
            }
        }
        return tiles;
    }

    drawTile() {
        if (this.undrawn_tiles.length === 0) {
            return -1 // could emit?
        }

        let i = Math.floor(Math.random() * this.undrawn_tiles.length);
        let tile = this.undrawn_tiles[i];
        this.undrawn_tiles.splice(i, 1);

        return tile;
    }

    buildDeadWall(){
        for (let i = 0; i < 14; i++) {
            this.deadWall.push(this.drawTile());
        }

    }

    dealHands() {
        if (this.hasDealt || this.deadWall.length === 0) {
            throw new Error('Invalid Deal Attempt')
        }

        for (let player of this.players){ 
            for (let i = 0; i < 13; i++) {
                player.hand.push(this.drawTile());
            }
        }
    }
}

class MahjongGameStateHandler {
    constructor() {
        this.players = [];
        for (let i = 0; i < 4; i++) {
            this.players.push(new MahjongPlayer);
        }
        this.tileManager = new tileSetHandler(this.players);
        
    }

    startRound() {
        this.tileManager.dealHands();
        console.log(this.tileManager.deadWall);
        for (let player of this.players) {
            console.log(player.hand);
        }
    }

    getPlayers() {
        // return all the players
    }

    getPlayerHands() {
        // return all player hands in single datastructure
    }

    getDiscarded() {
        // return all the discarded tiles for each player in single datastructure
    }
}

export {
    MahjongGameStateHandler,
    tileSetHandler,
    MahjongPlayer
}